from functools import lru_cache
import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PLAN_CATALOG_PATH = Path(__file__).resolve().parents[2] / "billing-plans.json"


class Settings(BaseSettings):
    app_env: str = "development"
    billing_live_enabled: bool = False
    billing_account_linking_enabled: bool = False
    database_url: str = "sqlite:///./comcode-billing.db"
    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    paystack_secret_key: str = ""
    paystack_weekly_plan_code: str = ""
    paystack_monthly_plan_code: str = ""
    paystack_yearly_plan_code: str = ""
    paystack_callback_url: str = ""

    mpesa_environment: str = "sandbox"
    mpesa_consumer_key: str = ""
    mpesa_consumer_secret: str = ""
    mpesa_shortcode: str = ""
    mpesa_passkey: str = ""
    mpesa_callback_url: str = ""
    mpesa_transaction_type: str = "CustomerPayBillOnline"

    renewal_job_token: str = ""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    def plan_price(self, plan: str) -> int:
        plans = get_plan_catalog()
        return int(plans[plan]["amount_kes"])

    def paystack_plan_code(self, plan: str) -> str:
        plan_codes = {
            "weekly": self.paystack_weekly_plan_code,
            "monthly": self.paystack_monthly_plan_code,
            "yearly": self.paystack_yearly_plan_code,
        }
        return plan_codes[plan]


@lru_cache
def get_plan_catalog() -> dict[str, dict[str, str | int]]:
    try:
        catalog = json.loads(PLAN_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unable to load billing plan catalog at {PLAN_CATALOG_PATH}.") from error

    if not isinstance(catalog, list) or not all(
        isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("amount_kes"), int)
        and item["amount_kes"] > 0
        for item in catalog
    ):
        raise RuntimeError(f"Billing plan catalog at {PLAN_CATALOG_PATH} is invalid.")

    return {item["id"]: item for item in catalog}


@lru_cache
def get_settings() -> Settings:
    return Settings()
