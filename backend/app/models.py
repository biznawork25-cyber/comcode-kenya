from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Payment(Base):
    __tablename__ = "billing_payments"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_billing_payment_idempotency"),
        Index("ix_billing_payments_provider_request", "provider", "provider_request_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    reference: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    plan: Mapped[str] = mapped_column(String(20))
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="KES")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    provider_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checkout_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    receipt_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subscription_id: Mapped[str | None] = mapped_column(
        ForeignKey("billing_subscriptions.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="payments",
        foreign_keys=[subscription_id],
    )


class Subscription(Base):
    __tablename__ = "billing_subscriptions"
    __table_args__ = (
        Index("ix_billing_subscriptions_due", "provider", "status", "next_renewal_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(20), index=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    plan: Mapped[str] = mapped_column(String(20))
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    phone_number: Mapped[str | None] = mapped_column(String(15), nullable=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="KES")
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    renewal_mode: Mapped[str] = mapped_column(String(24))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    next_renewal_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    payments: Mapped[list[Payment]] = relationship(
        back_populates="subscription",
        foreign_keys=[Payment.subscription_id],
    )


class WebhookEvent(Base):
    __tablename__ = "billing_webhook_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(20), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    payload: Mapped[dict] = mapped_column(JSON)
