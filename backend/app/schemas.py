import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


PlanName = Literal["weekly", "monthly", "yearly"]
PaymentProvider = Literal["paystack", "mpesa"]


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    plan: PlanName
    provider: PaymentProvider
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=20)

    @field_validator("phone_number")
    @classmethod
    def normalize_phone_number(cls, value: str | None) -> str | None:
        if value is None:
            return None

        if not re.fullmatch(r"[+0-9\s()-]+", value):
            raise ValueError("Enter a valid Kenyan mobile number, such as 0712345678.")

        digits = "".join(character for character in value if character.isdigit())
        if digits.startswith("0") and len(digits) == 10:
            digits = f"254{digits[1:]}"
        elif digits.startswith("7") or digits.startswith("1"):
            digits = f"254{digits}"

        if len(digits) != 12 or not digits.startswith("254") or digits[3] not in "17":
            raise ValueError("Enter a valid Kenyan mobile number, such as 0712345678.")
        return digits


class CheckoutResponse(BaseModel):
    reference: str
    provider: PaymentProvider
    status: str
    message: str
    checkout_url: str | None = None


class PlanResponse(BaseModel):
    id: PlanName
    name: str
    interval: str
    amount_kes: int
    paystack_available: bool
    mpesa_available: bool
