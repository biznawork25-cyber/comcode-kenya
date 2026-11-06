# ComCode

ComCode is an interactive computer science learning platform. The repository
contains the Next.js website and a FastAPI billing service for KES subscriptions.

## Website

Install the JavaScript dependencies and start the development server:

```powershell
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The checkout page calls the billing API at `http://127.0.0.1:8000` by default.
Set `NEXT_PUBLIC_BILLING_API_URL` if the API runs at a different address.

## Billing API

The API supports:

- Weekly (KSh 150), monthly (KSh 550), and yearly (KSh 6,500) plans.
- Paystack card subscriptions with provider-managed automatic renewals.
- M-Pesa Daraja STK Push payments; the customer approves each renewal on their
  phone. A scheduled API call sends the renewal prompt when it is due.
- Signed Paystack webhook verification, Daraja STK status queries, and
  idempotent billing-event processing.

Paystack's subscription plans must be created in the merchant dashboard with
the same KES amount and interval as the ComCode plan. Availability of KES
recurring card plans depends on the merchant account and Paystack configuration.
Daraja STK Push does not silently charge a customer on renewal. Automatic
M-Pesa renewals are intentionally not enabled; use them only if Safaricom has
approved and provisioned an applicable recurring-payment product for the
merchant account.

### Run locally

Use Python 3.11 or newer:

```powershell
py -3.13 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

For a local SQLite database, set this in `backend\.env`:

```text
DATABASE_URL=sqlite:///./comcode-billing.db
```

Run the API from the repository root:

```powershell
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

The API creates local development tables automatically. Production uses
PostgreSQL; apply `backend/migrations/001_billing.sql` before deploying.
The website and API use the shared `billing-plans.json` catalog for prices and
billing intervals.

### Configure sandbox providers

Set test credentials in `backend\.env`; never put secret keys in frontend code,
commit them, or send them in chat.

- Paystack: configure test secret key, callback URL, and weekly/monthly/yearly
  plan codes. The plans must match the amounts above and use KES.
- Daraja: set sandbox consumer key, consumer secret, shortcode, passkey, and a
  publicly reachable HTTPS callback URL ending in
  `/api/billing/webhooks/daraja`.
- Set a long random `RENEWAL_JOB_TOKEN`; a trusted scheduler must send
  `Authorization: Bearer <token>` to `POST /api/billing/renewals`.

The plan endpoint reports provider availability. Checkout stays unavailable for
a provider until its required configuration is present. Start with sandbox
credentials and complete test transactions before switching to production.
Live credentials are rejected unless `BILLING_LIVE_ENABLED=true` is explicitly
set on the backend. Live checkout also remains disabled until student account
linking is implemented and `BILLING_ACCOUNT_LINKING_ENABLED=true` is explicitly
set after that work is deployed.

### Important rollout notes

Billing records are associated with the submitted customer email. ComCode's
student authentication and course-access entitlement system is not yet present;
connect those records to verified student accounts before granting paid access.
The checkout is currently for sandbox testing; do not enable live billing
before account linking, subscription cancellation, and access control are in
place.
Configure production CORS origins, database backups, HTTPS, webhook URLs, and
the renewal scheduler before accepting live payments.

## Verification

```powershell
npm run lint
npm run build
$env:PYTHONPATH = "backend"
python -m unittest discover -s backend\tests
```
