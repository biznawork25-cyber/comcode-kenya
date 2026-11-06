CREATE TABLE billing_subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    provider VARCHAR(20) NOT NULL,
    provider_subscription_id VARCHAR(120) UNIQUE,
    plan VARCHAR(20) NOT NULL,
    customer_email VARCHAR(320) NOT NULL,
    phone_number VARCHAR(15),
    amount_minor INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KES',
    status VARCHAR(24) NOT NULL DEFAULT 'active',
    renewal_mode VARCHAR(24) NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    next_renewal_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_billing_subscriptions_provider
    ON billing_subscriptions (provider);
CREATE INDEX ix_billing_subscriptions_customer_email
    ON billing_subscriptions (customer_email);
CREATE INDEX ix_billing_subscriptions_status
    ON billing_subscriptions (status);
CREATE INDEX ix_billing_subscriptions_next_renewal_at
    ON billing_subscriptions (next_renewal_at);
CREATE INDEX ix_billing_subscriptions_due
    ON billing_subscriptions (provider, status, next_renewal_at);

CREATE TABLE billing_payments (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(36) NOT NULL UNIQUE,
    provider VARCHAR(20) NOT NULL,
    plan VARCHAR(20) NOT NULL,
    customer_email VARCHAR(320) NOT NULL,
    phone_number VARCHAR(15),
    amount_minor INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KES',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    provider_request_id VARCHAR(100),
    checkout_url VARCHAR(2048),
    receipt_number VARCHAR(100),
    idempotency_key VARCHAR(120) UNIQUE,
    subscription_id VARCHAR(36) REFERENCES billing_subscriptions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_billing_payments_reference ON billing_payments (reference);
CREATE INDEX ix_billing_payments_provider ON billing_payments (provider);
CREATE INDEX ix_billing_payments_customer_email ON billing_payments (customer_email);
CREATE INDEX ix_billing_payments_status ON billing_payments (status);
CREATE INDEX ix_billing_payments_provider_request
    ON billing_payments (provider, provider_request_id);

CREATE TABLE billing_webhook_events (
    id VARCHAR(64) PRIMARY KEY,
    provider VARCHAR(20) NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload JSON NOT NULL
);

CREATE INDEX ix_billing_webhook_events_provider
    ON billing_webhook_events (provider);
