import hashlib
import hmac
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import add_billing_interval, app, settings
from app.models import Payment, Subscription
from app.providers import verify_paystack_signature
from app.schemas import CheckoutRequest


class BillingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved_settings = {
            "app_env": settings.app_env,
            "billing_live_enabled": settings.billing_live_enabled,
            "billing_account_linking_enabled": settings.billing_account_linking_enabled,
            "paystack_secret_key": settings.paystack_secret_key,
            "paystack_callback_url": settings.paystack_callback_url,
            "paystack_weekly_plan_code": settings.paystack_weekly_plan_code,
            "mpesa_consumer_key": settings.mpesa_consumer_key,
            "mpesa_consumer_secret": settings.mpesa_consumer_secret,
            "mpesa_shortcode": settings.mpesa_shortcode,
            "mpesa_passkey": settings.mpesa_passkey,
            "mpesa_callback_url": settings.mpesa_callback_url,
            "mpesa_environment": settings.mpesa_environment,
        }
        settings.app_env = "test"
        settings.billing_live_enabled = False
        settings.billing_account_linking_enabled = False
        settings.paystack_secret_key = ""
        settings.paystack_callback_url = ""
        settings.paystack_weekly_plan_code = ""
        settings.mpesa_consumer_key = ""
        settings.mpesa_consumer_secret = ""
        settings.mpesa_shortcode = ""
        settings.mpesa_passkey = ""
        settings.mpesa_callback_url = ""
        settings.mpesa_environment = "sandbox"

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

        def override_get_db():
            with self.session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        for key, value in self.saved_settings.items():
            setattr(settings, key, value)

    def test_phone_number_is_normalized_to_mpesa_format(self) -> None:
        checkout = CheckoutRequest(
            plan="weekly",
            provider="mpesa",
            email="student@example.com",
            phone_number="0712 345 678",
        )

        self.assertEqual(checkout.phone_number, "254712345678")

    def test_invalid_phone_number_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CheckoutRequest(
                plan="weekly",
                provider="mpesa",
                email="student@example.com",
                phone_number="12345",
            )

    def test_monthly_interval_uses_last_valid_day(self) -> None:
        start = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)

        self.assertEqual(
            add_billing_interval(start, "monthly"),
            datetime(2026, 2, 28, 12, 0, tzinfo=timezone.utc),
        )

    def test_paystack_signature_uses_sha512_hmac(self) -> None:
        secret = "test-secret"
        body = b'{"event":"charge.success"}'
        signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()

        self.assertTrue(verify_paystack_signature(secret, body, signature))
        self.assertFalse(verify_paystack_signature(secret, body, "invalid"))

    def test_plans_report_provider_availability_without_credentials(self) -> None:
        response = self.client.get("/api/billing/plans")

        self.assertEqual(response.status_code, 200)
        weekly = response.json()[0]
        self.assertEqual(weekly["amount_kes"], 150)
        self.assertFalse(weekly["paystack_available"])
        self.assertFalse(weekly["mpesa_available"])

    def test_paystack_checkout_and_signed_webhook_activate_subscription(self) -> None:
        settings.paystack_secret_key = "sk_test_example"
        settings.paystack_callback_url = "https://comcode.example/checkout/complete"
        settings.paystack_weekly_plan_code = "PLN_weekly"

        with patch(
            "app.main.initialize_paystack",
            return_value="https://checkout.paystack.com/example",
        ):
            checkout_response = self.client.post(
                "/api/billing/checkout",
                json={
                    "plan": "weekly",
                    "provider": "paystack",
                    "email": "student@example.com",
                },
            )

        self.assertEqual(checkout_response.status_code, 200)
        reference = checkout_response.json()["reference"]
        event = {
            "event": "charge.success",
            "data": {
                "reference": reference,
                "status": "success",
                "amount": 15000,
                "currency": "KES",
                "subscription": {
                    "subscription_code": "SUB_test",
                    "next_payment_date": "2026-11-13T00:00:00.000Z",
                },
            },
        }
        body = json.dumps(event).encode()
        signature = hmac.new(
            settings.paystack_secret_key.encode(),
            body,
            hashlib.sha512,
        ).hexdigest()
        webhook_response = self.client.post(
            "/api/billing/webhooks/paystack",
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-paystack-signature": signature,
            },
        )

        self.assertEqual(webhook_response.status_code, 200)
        with self.session_factory() as session:
            payment = session.scalar(select(Payment).where(Payment.reference == reference))
            subscription = session.scalar(
                select(Subscription).where(
                    Subscription.provider_subscription_id == "SUB_test"
                )
            )
            self.assertEqual(payment.status, "succeeded")
            self.assertEqual(subscription.renewal_mode, "automatic")

    def test_invalid_paystack_webhook_signature_is_rejected(self) -> None:
        settings.paystack_secret_key = "sk_test_example"
        response = self.client.post(
            "/api/billing/webhooks/paystack",
            content=b'{"event":"charge.success","data":{}}',
            headers={"x-paystack-signature": "invalid"},
        )

        self.assertEqual(response.status_code, 401)

    def test_mpesa_checkout_callback_is_queried_before_activation(self) -> None:
        settings.mpesa_consumer_key = "sandbox-key"
        settings.mpesa_consumer_secret = "sandbox-secret"
        settings.mpesa_shortcode = "123456"
        settings.mpesa_passkey = "test-passkey"
        settings.mpesa_callback_url = "https://comcode.example/api/billing/webhooks/daraja"

        with patch(
            "app.main.initiate_mpesa_stk_push",
            return_value={"CheckoutRequestID": "ws_CO_test"},
        ):
            checkout_response = self.client.post(
                "/api/billing/checkout",
                json={
                    "plan": "weekly",
                    "provider": "mpesa",
                    "email": "student@example.com",
                    "phone_number": "0712345678",
                },
            )

        self.assertEqual(checkout_response.status_code, 200)
        with patch(
            "app.main.query_mpesa_stk_push",
            return_value={"ResultCode": "0"},
        ) as query:
            callback_response = self.client.post(
                "/api/billing/webhooks/daraja",
                json={
                    "Body": {
                        "stkCallback": {
                            "CheckoutRequestID": "ws_CO_test",
                            "ResultCode": 0,
                            "CallbackMetadata": {
                                "Item": [
                                    {"Name": "Amount", "Value": 150},
                                    {"Name": "MpesaReceiptNumber", "Value": "QAB123"},
                                    {"Name": "PhoneNumber", "Value": 254712345678},
                                ]
                            },
                        }
                    }
                },
            )

        self.assertEqual(callback_response.status_code, 200)
        query.assert_called_once_with(settings, "ws_CO_test")
        with self.session_factory() as session:
            payment = session.scalar(
                select(Payment).where(Payment.provider_request_id == "ws_CO_test")
            )
            subscription = session.scalar(
                select(Subscription).where(Subscription.customer_email == "student@example.com")
            )
            self.assertEqual(payment.status, "succeeded")
            self.assertEqual(subscription.renewal_mode, "customer_approval")


if __name__ == "__main__":
    unittest.main()
