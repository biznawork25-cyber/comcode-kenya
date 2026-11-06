import base64
import hashlib
import hmac
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


def verify_paystack_signature(secret_key: str, body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret_key.encode(), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def _read_provider_response(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError as error:
        raise ProviderError("Payment provider returned an invalid response.") from error

    if not isinstance(payload, dict):
        raise ProviderError("Payment provider returned an invalid response.")

    if response.is_error or payload.get("status") is False:
        message = str(payload.get("message", "Payment provider request failed."))
        logger.warning("Payment provider request failed with status %s", response.status_code)
        raise ProviderError(message)
    return payload


def initialize_paystack(
    settings: Settings,
    *,
    email: str,
    amount_minor: int,
    plan_code: str,
    reference: str,
    payment_id: str,
) -> str:
    payload = {
        "email": email,
        "amount": amount_minor,
        "currency": "KES",
        "plan": plan_code,
        "reference": reference,
        "callback_url": settings.paystack_callback_url,
        "metadata": {
            "billing_payment_id": payment_id,
            "comcode_plan": plan_code,
        },
    }
    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(
                "https://api.paystack.co/transaction/initialize",
                headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
                json=payload,
            )
    except httpx.HTTPError as error:
        raise ProviderError("Could not reach Paystack. Please try again.") from error

    data = _read_provider_response(response).get("data", {})
    authorization_url = data.get("authorization_url")
    if not authorization_url:
        raise ProviderError("Paystack did not return a checkout URL.")
    return authorization_url


def mpesa_api_base(settings: Settings) -> str:
    if settings.mpesa_environment == "sandbox":
        return "https://sandbox.safaricom.co.ke"
    if settings.mpesa_environment == "production":
        return "https://api.safaricom.co.ke"
    raise ProviderError("MPESA_ENVIRONMENT must be sandbox or production.")


def mpesa_access_token(settings: Settings, client: httpx.Client | None = None) -> str:
    credentials = f"{settings.mpesa_consumer_key}:{settings.mpesa_consumer_secret}"
    authorization = base64.b64encode(credentials.encode()).decode()
    try:
        if client is None:
            with httpx.Client(timeout=15) as owned_client:
                response = owned_client.get(
                    f"{mpesa_api_base(settings)}/oauth/v1/generate",
                    params={"grant_type": "client_credentials"},
                    headers={"Authorization": f"Basic {authorization}"},
                )
        else:
            response = client.get(
                f"{mpesa_api_base(settings)}/oauth/v1/generate",
                params={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {authorization}"},
            )
    except httpx.HTTPError as error:
        raise ProviderError("Could not connect to Safaricom Daraja.") from error

    if response.is_error:
        logger.warning("Daraja OAuth request failed with status %s", response.status_code)
        raise ProviderError("Daraja authentication failed.")
    try:
        token = response.json().get("access_token")
    except ValueError as error:
        raise ProviderError("Daraja returned an invalid authentication response.") from error
    if not token:
        raise ProviderError("Daraja did not return an access token.")
    return token


def _mpesa_timestamp() -> str:
    return datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%Y%m%d%H%M%S")


def initiate_mpesa_stk_push(
    settings: Settings,
    *,
    phone_number: str,
    amount_kes: int,
    account_reference: str,
    description: str,
) -> dict:
    if not settings.mpesa_callback_url.startswith("https://"):
        raise ProviderError("Configure a public HTTPS Daraja callback URL before checkout.")

    timestamp = _mpesa_timestamp()
    password = base64.b64encode(
        f"{settings.mpesa_shortcode}{settings.mpesa_passkey}{timestamp}".encode()
    ).decode()
    payload = {
        "BusinessShortCode": settings.mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": settings.mpesa_transaction_type,
        "Amount": amount_kes,
        "PartyA": phone_number,
        "PartyB": settings.mpesa_shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.mpesa_callback_url,
        "AccountReference": account_reference[:12],
        "TransactionDesc": description[:13],
    }

    try:
        with httpx.Client(timeout=20) as client:
            token = mpesa_access_token(settings, client)
            response = client.post(
                f"{mpesa_api_base(settings)}/mpesa/stkpush/v1/processrequest",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
    except httpx.HTTPError as error:
        raise ProviderError("Could not reach Safaricom Daraja. Please try again.") from error

    data = _read_provider_response(response)
    if data.get("ResponseCode") != "0" or not data.get("CheckoutRequestID"):
        logger.warning("Daraja did not accept the STK Push request")
        raise ProviderError(data.get("ResponseDescription", "Daraja rejected the STK Push."))
    return data


def query_mpesa_stk_push(settings: Settings, checkout_request_id: str) -> dict:
    timestamp = _mpesa_timestamp()
    password = base64.b64encode(
        f"{settings.mpesa_shortcode}{settings.mpesa_passkey}{timestamp}".encode()
    ).decode()
    payload = {
        "BusinessShortCode": settings.mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }
    try:
        with httpx.Client(timeout=20) as client:
            token = mpesa_access_token(settings, client)
            response = client.post(
                f"{mpesa_api_base(settings)}/mpesa/stkpushquery/v1/query",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
    except httpx.HTTPError as error:
        raise ProviderError("Could not verify the Daraja payment status.") from error
    return _read_provider_response(response)
