import hashlib
import json
import logging
import secrets
import calendar
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_plan_catalog, get_settings
from app.database import Base, engine, get_db
from app.models import Payment, Subscription, WebhookEvent
from app.providers import (
    ProviderError,
    initialize_paystack,
    initiate_mpesa_stk_push,
    query_mpesa_stk_push,
    verify_paystack_signature,
)
from app.schemas import CheckoutRequest, CheckoutResponse, PlanResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_billing_interval(value: datetime, plan: str) -> datetime:
    if plan == "weekly":
        return value + timedelta(days=7)
    if plan == "monthly":
        month = value.month % 12 + 1
        year = value.year + (1 if value.month == 12 else 0)
        day = min(value.day, calendar.monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)
    year = value.year + 1
    day = min(value.day, calendar.monthrange(year, value.month)[1])
    return value.replace(year=year, day=day)


def mpesa_enabled() -> bool:
    credentials_configured = all(
        (
            settings.mpesa_consumer_key,
            settings.mpesa_consumer_secret,
            settings.mpesa_shortcode,
            settings.mpesa_passkey,
            settings.mpesa_callback_url.startswith("https://"),
        )
    )
    live_mode_allowed = settings.mpesa_environment == "sandbox" and settings.app_env != "production"
    live_mode_allowed = live_mode_allowed or (
        settings.mpesa_environment == "production"
        and settings.app_env == "production"
        and settings.billing_live_enabled
        and settings.billing_account_linking_enabled
    )
    return bool(credentials_configured and live_mode_allowed)


def paystack_enabled(plan: str | None = None) -> bool:
    configured = settings.paystack_secret_key and settings.paystack_callback_url
    secret_key = settings.paystack_secret_key
    test_mode = secret_key.startswith("sk_test_") and settings.app_env != "production"
    live_mode = (
        secret_key.startswith("sk_live_")
        and settings.app_env == "production"
        and settings.billing_live_enabled
        and settings.billing_account_linking_enabled
    )
    return bool(
        configured
        and (test_mode or live_mode)
        and (plan is None or settings.paystack_plan_code(plan))
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ComCode Billing API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Paystack-Signature"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/billing/plans", response_model=list[PlanResponse])
def list_plans() -> list[PlanResponse]:
    return [
        PlanResponse(
            id=plan_id,
            name=str(plan["name"]),
            interval=str(plan["interval"]),
            amount_kes=int(plan["amount_kes"]),
            paystack_available=paystack_enabled(plan_id),
            mpesa_available=mpesa_enabled(),
        )
        for plan_id, plan in get_plan_catalog().items()
    ]


@app.post("/api/billing/checkout", response_model=CheckoutResponse)
def create_checkout(
    checkout: CheckoutRequest,
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    amount_kes = settings.plan_price(checkout.plan)
    if amount_kes <= 0:
        raise HTTPException(status_code=503, detail="This subscription plan is not configured.")

    if checkout.provider == "paystack":
        if not paystack_enabled(checkout.plan):
            raise HTTPException(
                status_code=503,
                detail="Paystack recurring billing is not configured for this plan yet.",
            )
        if checkout.phone_number:
            raise HTTPException(
                status_code=400,
                detail="Use the M-Pesa option to pay with a Kenyan mobile number.",
            )
    else:
        if not mpesa_enabled():
            raise HTTPException(
                status_code=503,
                detail="Daraja is not configured yet. Add sandbox credentials to the backend environment.",
            )
        if not checkout.phone_number:
            raise HTTPException(status_code=422, detail="A Kenyan mobile number is required for M-Pesa.")

    email_attempts = db.scalar(
        select(func.count())
        .select_from(Payment)
        .where(
            Payment.provider == checkout.provider,
            Payment.customer_email == str(checkout.email).lower(),
            Payment.created_at >= utc_now() - timedelta(hours=1),
        )
    )
    email_attempt_limit = 3 if checkout.provider == "mpesa" else 5
    if email_attempts >= email_attempt_limit:
        raise HTTPException(
            status_code=429,
            detail="Too many payment attempts were made for this email. Please wait before trying again.",
        )

    if checkout.provider == "mpesa":
        phone_attempts = db.scalar(
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.provider == "mpesa",
                Payment.phone_number == checkout.phone_number,
                Payment.created_at >= utc_now() - timedelta(hours=1),
            )
        )
        if phone_attempts >= 3:
            raise HTTPException(
                status_code=429,
                detail="Too many M-Pesa prompts were sent to this number. Please wait before requesting another.",
            )

    reference = str(uuid4())
    payment = Payment(
        reference=reference,
        provider=checkout.provider,
        plan=checkout.plan,
        customer_email=str(checkout.email).lower(),
        phone_number=checkout.phone_number,
        amount_minor=amount_kes * 100,
        currency="KES",
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    try:
        if checkout.provider == "paystack":
            payment.checkout_url = initialize_paystack(
                settings,
                email=payment.customer_email,
                amount_minor=payment.amount_minor,
                plan_code=settings.paystack_plan_code(checkout.plan),
                reference=payment.reference,
                payment_id=payment.id,
            )
            payment.status = "awaiting_payment"
            message = "Continue to Paystack to authorize your recurring card subscription."
        else:
            response = initiate_mpesa_stk_push(
                settings,
                phone_number=checkout.phone_number or "",
                amount_kes=amount_kes,
                account_reference=f"CC{payment.id.replace('-', '')}",
                description=f"ComCode {checkout.plan}",
            )
            payment.provider_request_id = response["CheckoutRequestID"]
            payment.status = "awaiting_payment"
            message = "Approve the M-Pesa prompt on your phone. Renewals will also ask you to approve."
    except ProviderError as error:
        payment.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(error)) from error

    db.commit()
    return CheckoutResponse(
        reference=payment.reference,
        provider=checkout.provider,
        status=payment.status,
        message=message,
        checkout_url=payment.checkout_url,
    )


@app.get("/api/billing/payments/{reference}")
def get_payment_status(reference: str, db: Session = Depends(get_db)) -> dict[str, str]:
    payment = db.scalar(select(Payment).where(Payment.reference == reference))
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment was not found.")
    return {"reference": payment.reference, "status": payment.status, "plan": payment.plan}


def _parse_provider_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _subscription_from_payment(
    db: Session,
    payment: Payment,
    provider_subscription_id: str | None,
    next_renewal_at: datetime | None = None,
) -> Subscription:
    subscription = None
    if provider_subscription_id:
        subscription = db.scalar(
            select(Subscription).where(
                Subscription.provider_subscription_id == provider_subscription_id
            )
        )
    if subscription is None and payment.subscription_id:
        subscription = db.get(Subscription, payment.subscription_id)

    next_date = next_renewal_at or add_billing_interval(utc_now(), payment.plan)
    if subscription is None:
        subscription = Subscription(
            provider=payment.provider,
            provider_subscription_id=provider_subscription_id,
            plan=payment.plan,
            customer_email=payment.customer_email,
            phone_number=payment.phone_number,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            status="active",
            renewal_mode="automatic" if payment.provider == "paystack" else "customer_approval",
            current_period_end=next_date,
            next_renewal_at=next_date,
        )
        db.add(subscription)
        db.flush()
    else:
        subscription.status = "active"
        subscription.current_period_end = next_date
        subscription.next_renewal_at = next_date
    payment.subscription = subscription
    payment.status = "succeeded"
    return subscription


def _handle_paystack_event(db: Session, event: dict) -> None:
    event_type = event.get("event")
    data = event.get("data") or {}
    if not isinstance(event_type, str) or not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid Paystack event.")

    event_key = hashlib.sha256(
        json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if db.get(WebhookEvent, event_key):
        return

    webhook_record = WebhookEvent(
        id=event_key,
        provider="paystack",
        event_type=event_type,
        payload={"event": event_type},
    )
    db.add(webhook_record)

    if event_type == "charge.success":
        reference = data.get("reference")
        payment = db.scalar(select(Payment).where(Payment.reference == reference))
        if payment is not None:
            if (
                data.get("status") != "success"
                or data.get("amount") != payment.amount_minor
                or data.get("currency") != payment.currency
            ):
                payment.status = "review_required"
                logger.error("Paystack charge details did not match billing reference %s", reference)
            else:
                sub_data = data.get("subscription") or {}
                if not isinstance(sub_data, dict):
                    sub_data = {}
                subscription_code = sub_data.get("subscription_code")
                next_date = _parse_provider_time(sub_data.get("next_payment_date"))
                if subscription_code:
                    _subscription_from_payment(db, payment, subscription_code, next_date)
                else:
                    payment.status = "awaiting_subscription"

    elif event_type == "subscription.create":
        customer = data.get("customer") or {}
        plan_data = data.get("plan") or {}
        if not isinstance(customer, dict):
            customer = {}
        subscription_code = data.get("subscription_code")
        customer_email = str(customer.get("email", "")).lower()
        amount_minor = data.get("amount")
        metadata = data.get("metadata") or {}
        billing_payment_id = (
            metadata.get("billing_payment_id") if isinstance(metadata, dict) else None
        )
        payment = db.get(Payment, billing_payment_id) if billing_payment_id else None
        if not isinstance(plan_data, dict):
            plan_data = {}
        plan_code = plan_data.get("plan_code")
        if payment is None and customer_email and isinstance(amount_minor, int):
            payment = db.scalar(
                select(Payment)
                .where(
                    Payment.provider == "paystack",
                    Payment.customer_email == customer_email,
                    Payment.amount_minor == amount_minor,
                    Payment.status.in_(("awaiting_payment", "succeeded")),
                    Payment.subscription_id.is_(None),
                )
                .order_by(Payment.created_at.desc())
            )
        if (
            payment
            and payment.provider == "paystack"
            and payment.customer_email == customer_email
            and payment.status in {"awaiting_payment", "succeeded"}
            and subscription_code
            and data.get("status") == "active"
            and amount_minor == payment.amount_minor
            and plan_code == settings.paystack_plan_code(payment.plan)
        ):
            _subscription_from_payment(
                db,
                payment,
                subscription_code,
                _parse_provider_time(data.get("next_payment_date")),
            )

    elif event_type in {"invoice.update", "invoice.payment_failed"}:
        provider_subscription = data.get("subscription") or {}
        subscription_code = (
            provider_subscription.get("subscription_code")
            if isinstance(provider_subscription, dict)
            else None
        )
        subscription = db.scalar(
            select(Subscription).where(
                Subscription.provider_subscription_id == subscription_code
            )
        )
        if subscription:
            if event_type == "invoice.payment_failed":
                subscription.status = "past_due"
            elif data.get("status") == "success" or data.get("paid") is True:
                subscription.status = "active"
                next_date = _parse_provider_time(provider_subscription.get("next_payment_date"))
                if next_date:
                    subscription.current_period_end = next_date
                    subscription.next_renewal_at = next_date

    elif event_type in {"subscription.disable", "subscription.not_renew"}:
        subscription_code = data.get("subscription_code")
        subscription = db.scalar(
            select(Subscription).where(
                Subscription.provider_subscription_id == subscription_code
            )
        )
        if subscription:
            subscription.status = (
                "cancelled" if event_type == "subscription.disable" else "cancel_at_period_end"
            )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()


@app.post("/api/billing/webhooks/paystack")
async def paystack_webhook(
    request: Request,
    signature: str | None = Header(default=None, alias="x-paystack-signature"),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=503, detail="Paystack webhook is not configured.")
    body = await request.body()
    if not verify_paystack_signature(settings.paystack_secret_key, body, signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature.")
    try:
        event = json.loads(body)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from error
    _handle_paystack_event(db, event)
    return {"received": True}


def _activate_mpesa_payment(
    db: Session,
    payment: Payment,
    callback: dict,
) -> None:
    callback_metadata = callback.get("CallbackMetadata")
    callback_items = (
        callback_metadata.get("Item", [])
        if isinstance(callback_metadata, dict)
        else []
    )
    if not isinstance(callback_items, list):
        callback_items = []
    metadata = {
        item["Name"]: item.get("Value")
        for item in callback_items
        if isinstance(item, dict) and isinstance(item.get("Name"), str)
    }
    amount = metadata.get("Amount")
    try:
        amount_matches = amount is not None and int(amount) * 100 == payment.amount_minor
    except (TypeError, ValueError):
        amount_matches = False
    if not amount_matches or not metadata.get("PhoneNumber") or not metadata.get("MpesaReceiptNumber"):
        payment.status = "review_required"
        if payment.subscription_id:
            subscription = db.get(Subscription, payment.subscription_id)
            if subscription:
                subscription.status = "past_due"
                subscription.next_renewal_at = utc_now() + timedelta(days=1)
        logger.error("Daraja callback metadata was incomplete for payment %s", payment.reference)
        return
    if str(metadata["PhoneNumber"]) != payment.phone_number:
        payment.status = "review_required"
        if payment.subscription_id:
            subscription = db.get(Subscription, payment.subscription_id)
            if subscription:
                subscription.status = "past_due"
                subscription.next_renewal_at = utc_now() + timedelta(days=1)
        logger.error("Daraja phone number did not match billing reference %s", payment.reference)
        return

    payment.receipt_number = metadata.get("MpesaReceiptNumber")
    renewal_date = add_billing_interval(utc_now(), payment.plan)
    if payment.subscription_id:
        subscription = db.get(Subscription, payment.subscription_id)
        if subscription:
            subscription.status = "active"
            subscription.current_period_end = renewal_date
            subscription.next_renewal_at = renewal_date
            payment.status = "succeeded"
            return
    _subscription_from_payment(db, payment, None, renewal_date)


@app.post("/api/billing/webhooks/daraja")
async def daraja_callback(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        payload = await request.json()
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid Daraja callback JSON.") from error

    body = payload.get("Body") if isinstance(payload, dict) else None
    callback = body.get("stkCallback") if isinstance(body, dict) else None
    if not isinstance(callback, dict):
        raise HTTPException(status_code=400, detail="Invalid Daraja callback.")

    checkout_id = callback.get("CheckoutRequestID")
    payment = db.scalar(
        select(Payment).where(
            Payment.provider == "mpesa",
            Payment.provider_request_id == checkout_id,
        )
    )
    if payment is None:
        logger.warning("Received Daraja callback for an unknown checkout request")
        return {"ResultCode": 0, "ResultDesc": "Callback received"}

    if callback.get("ResultCode") != 0:
        payment.status = "failed"
        if payment.subscription_id:
            subscription = db.get(Subscription, payment.subscription_id)
            if subscription:
                subscription.status = "past_due"
                subscription.next_renewal_at = utc_now() + timedelta(days=1)
                subscription.next_renewal_at = utc_now() + timedelta(days=1)
        db.commit()
        return {"ResultCode": 0, "ResultDesc": "Callback received"}

    try:
        query = query_mpesa_stk_push(settings, checkout_id)
    except ProviderError:
        logger.exception("Could not verify Daraja callback for payment %s", payment.reference)
        return {"ResultCode": 0, "ResultDesc": "Callback received; verification pending"}

    if str(query.get("ResultCode")) != "0":
        payment.status = "review_required"
        if payment.subscription_id:
            subscription = db.get(Subscription, payment.subscription_id)
            if subscription:
                subscription.status = "past_due"
                subscription.next_renewal_at = utc_now() + timedelta(days=1)
        db.commit()
        logger.error("Daraja STK query did not confirm payment %s", payment.reference)
        return {"ResultCode": 0, "ResultDesc": "Callback received; verification pending"}

    _activate_mpesa_payment(db, payment, callback)
    db.commit()
    return {"ResultCode": 0, "ResultDesc": "Callback received"}


@app.post("/api/billing/renewals")
def prompt_due_mpesa_renewals(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    if not settings.renewal_job_token:
        raise HTTPException(status_code=503, detail="The renewal scheduler is not configured.")
    expected = f"Bearer {settings.renewal_job_token}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized.")
    if not mpesa_enabled():
        raise HTTPException(status_code=503, detail="Daraja is not configured.")

    stale_payments = db.scalars(
        select(Payment).where(
            Payment.provider == "mpesa",
            Payment.status == "awaiting_payment",
            Payment.created_at <= utc_now() - timedelta(minutes=30),
        )
    ).all()
    for payment in stale_payments:
        payment.status = "failed"
        if payment.subscription_id:
            subscription = db.get(Subscription, payment.subscription_id)
            if subscription:
                subscription.status = "past_due"
                subscription.next_renewal_at = utc_now() + timedelta(days=1)
    if stale_payments:
        db.commit()

    due_subscriptions = db.scalars(
        select(Subscription).where(
            Subscription.provider == "mpesa",
            Subscription.status.in_(("active", "past_due")),
            Subscription.next_renewal_at <= utc_now(),
        )
    ).all()
    prompted = 0
    for subscription in due_subscriptions:
        idempotency_key = f"{subscription.id}:{subscription.next_renewal_at.isoformat()}"
        existing = db.scalar(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        if existing:
            continue

        payment = Payment(
            reference=str(uuid4()),
            provider="mpesa",
            plan=subscription.plan,
            customer_email=subscription.customer_email,
            phone_number=subscription.phone_number,
            amount_minor=subscription.amount_minor,
            currency=subscription.currency,
            status="pending",
            idempotency_key=idempotency_key,
            subscription_id=subscription.id,
        )
        subscription.status = "renewal_pending"
        db.add(payment)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        try:
            response = initiate_mpesa_stk_push(
                settings,
                phone_number=subscription.phone_number or "",
                amount_kes=subscription.amount_minor // 100,
                account_reference=f"CC{payment.id.replace('-', '')}",
                description=f"ComCode {subscription.plan}",
            )
        except ProviderError:
            logger.exception("Daraja renewal prompt failed for subscription %s", subscription.id)
            payment.status = "failed"
            subscription.status = "past_due"
            subscription.next_renewal_at = utc_now() + timedelta(days=1)
        else:
            payment.provider_request_id = response["CheckoutRequestID"]
            payment.status = "awaiting_payment"
            prompted += 1
        db.commit()

    return {"prompts_sent": prompted}
