"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { FormEvent } from "react";
import billingPlans from "../../../billing-plans.json";

type PlanId = "weekly" | "monthly" | "yearly";
type Provider = "paystack" | "mpesa";

type PlanAvailability = {
  id: PlanId;
  amount_kes: number;
  paystack_available: boolean;
  mpesa_available: boolean;
};

type CheckoutFormProps = {
  initialPlan: PlanId;
};

const apiUrl = (
  process.env.NEXT_PUBLIC_BILLING_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

const plans: {
  id: PlanId;
  name: string;
  interval: string;
  amount_kes: number;
  price: string;
}[] = billingPlans.map((plan) => ({
  ...plan,
  id: plan.id as PlanId,
  price: `KSh ${new Intl.NumberFormat("en-KE").format(plan.amount_kes)}`,
}));

export default function CheckoutForm({ initialPlan }: CheckoutFormProps) {
  const [plan, setPlan] = useState<PlanId>(initialPlan);
  const [provider, setProvider] = useState<Provider>("paystack");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [availability, setAvailability] = useState<PlanAvailability[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [paymentReference, setPaymentReference] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadPlans() {
      try {
        const response = await fetch(`${apiUrl}/api/billing/plans`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error("Could not load payment availability.");
        }
        const plansResponse = (await response.json()) as PlanAvailability[];
        setAvailability(plansResponse);
      } catch (loadError) {
        if (loadError instanceof Error && loadError.name !== "AbortError") {
          setError("Billing service is unavailable. Please try again later.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingPlans(false);
        }
      }
    }

    void loadPlans();
    return () => controller.abort();
  }, []);

  const selectedAvailability = availability.find((item) => item.id === plan);
  const selectedPlan = plans.find((item) => item.id === plan) ?? plans[0];
  const planPrice = (planId: PlanId) => {
    const availablePlan = availability.find((item) => item.id === planId);
    const fallbackPlan = plans.find((item) => item.id === planId);
    const amount = availablePlan?.amount_kes ?? fallbackPlan?.amount_kes ?? 0;
    return `KSh ${new Intl.NumberFormat("en-KE").format(amount)}`;
  };
  const paystackAvailable = selectedAvailability?.paystack_available ?? false;
  const mpesaAvailable = selectedAvailability?.mpesa_available ?? false;
  const activeProvider =
    provider === "paystack" && !paystackAvailable && mpesaAvailable
      ? "mpesa"
      : provider === "mpesa" && !mpesaAvailable && paystackAvailable
        ? "paystack"
        : provider;

  async function submitCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    setPaymentReference("");
    setSubmitting(true);

    try {
      const response = await fetch(`${apiUrl}/api/billing/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan,
          provider: activeProvider,
          email,
          ...(activeProvider === "mpesa" ? { phone_number: phone } : {}),
        }),
      });
      const result = (await response.json()) as {
        detail?: string;
        checkout_url?: string;
        message?: string;
        reference?: string;
      };

      if (!response.ok) {
        throw new Error(result.detail ?? "Checkout could not be started.");
      }
      if (!result.reference || !result.message) {
        throw new Error("The billing service returned an incomplete checkout response.");
      }

      setPaymentReference(result.reference);
      if (result.checkout_url) {
        window.location.assign(result.checkout_url);
        return;
      }
      setMessage(result.message);
    } catch (checkoutError) {
      setError(
        checkoutError instanceof Error
          ? checkoutError.message
          : "Checkout could not be started. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="checkout-page">
      <header className="checkout-header">
        <Link aria-label="ComCode home" className="brand" href="/">
          <span aria-hidden="true" className="brand-mark">c</span>
          <span>comcode</span>
        </Link>
        <Link className="checkout-back" href="/#plans">Back to plans</Link>
      </header>

      <div className="checkout-layout">
        <section className="checkout-main">
          <div className="eyebrow">COMCODE MEMBERSHIP</div>
          <h1>Choose how you&apos;d like to pay.</h1>
          <p className="checkout-intro">
            Test your membership payment securely with the provider. Student
            sign-in and course-access linking will be connected before launch.
          </p>

          <form className="checkout-form" onSubmit={submitCheckout}>
            <label className="checkout-label" htmlFor="plan">Choose a plan</label>
            <div className="checkout-plan-options">
              {plans.map((item) => (
                <label
                  className={`checkout-plan-option${plan === item.id ? " selected" : ""}`}
                  key={item.id}
                >
                  <input
                    checked={plan === item.id}
                    name="plan"
                    onChange={() => setPlan(item.id)}
                    type="radio"
                    value={item.id}
                  />
                  <span className="checkout-plan-copy">
                    <strong>{item.name}</strong>
                    <small>per {item.interval}</small>
                  </span>
                  <span className="checkout-plan-price">{planPrice(item.id)}</span>
                </label>
              ))}
            </div>

            <label className="checkout-label" htmlFor="checkout-email">Email address</label>
            <input
              autoComplete="email"
              className="checkout-input"
              id="checkout-email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
              type="email"
              value={email}
            />

            <fieldset className="payment-methods">
              <legend className="checkout-label">Payment method</legend>
              <label className={`payment-option${activeProvider === "paystack" ? " selected" : ""}${!paystackAvailable ? " unavailable" : ""}`}>
                <input
                  checked={activeProvider === "paystack"}
                  disabled={!paystackAvailable}
                  name="provider"
                  onChange={() => setProvider("paystack")}
                  type="radio"
                  value="paystack"
                />
                <span className="billing-brand paystack-brand">P</span>
                <span className="payment-option-copy">
                  <strong>Paystack</strong>
                  <small>Card payments · automatic renewal</small>
                </span>
                <span className="payment-status">
                  {loadingPlans ? "Checking" : paystackAvailable ? "Available" : "Coming soon"}
                </span>
              </label>
              <label className={`payment-option${activeProvider === "mpesa" ? " selected" : ""}${!mpesaAvailable ? " unavailable" : ""}`}>
                <input
                  checked={activeProvider === "mpesa"}
                  disabled={!mpesaAvailable}
                  name="provider"
                  onChange={() => setProvider("mpesa")}
                  type="radio"
                  value="mpesa"
                />
                <span className="billing-brand mpesa-brand">M</span>
                <span className="payment-option-copy">
                  <strong>M-Pesa · Daraja</strong>
                  <small>Approve this payment and every renewal</small>
                </span>
                <span className="payment-status">
                  {loadingPlans ? "Checking" : mpesaAvailable ? "Available" : "Coming soon"}
                </span>
              </label>
            </fieldset>

            {activeProvider === "mpesa" && (
              <div className="phone-field">
                <label className="checkout-label" htmlFor="mpesa-phone">M-Pesa phone number</label>
                <input
                  autoComplete="tel"
                  className="checkout-input"
                  id="mpesa-phone"
                  inputMode="tel"
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="07XX XXX XXX"
                  required
                  type="tel"
                  value={phone}
                />
                <small>You&apos;ll receive an STK Push prompt and approve it with your M-Pesa PIN.</small>
              </div>
            )}

            {error && <p className="checkout-feedback checkout-error" role="alert">{error}</p>}
            {message && (
              <div className="checkout-feedback checkout-success" role="status">
                <strong>{message}</strong>
                {paymentReference && (
                  <Link href={`/checkout/complete?reference=${encodeURIComponent(paymentReference)}`}>
                    Check payment status
                  </Link>
                )}
              </div>
            )}

            <button
              className="button button-dark checkout-submit"
              disabled={
                submitting ||
                loadingPlans ||
                (activeProvider === "paystack" && !paystackAvailable) ||
                (activeProvider === "mpesa" && !mpesaAvailable)
              }
              type="submit"
            >
              {submitting ? "Starting secure checkout…" : "Continue to secure checkout"}
            </button>
            <p className="checkout-terms">
              By continuing, you agree to recurring billing. Paystack renewals are
              automatic; M-Pesa renewals require your approval each time.
            </p>
          </form>
        </section>

        <aside className="checkout-summary">
          <span className="summary-label">YOUR PLAN</span>
          <h2>{selectedPlan.name} membership</h2>
          <p>Access to ComCode&apos;s interactive computer science curriculum.</p>
          <div className="summary-price">
            <strong>{planPrice(plan)}</strong>
            <span>per {selectedPlan.interval}</span>
          </div>
          <ul>
            <li>Interactive lessons and course materials</li>
            <li>Practice, quizzes, and timed exams</li>
            <li>Progress tracking and recommendations</li>
            <li>AI tutor access as it becomes available</li>
          </ul>
          <div className="summary-security">
            <span aria-hidden="true">◎</span>
            <span>Payment is processed securely by your chosen provider. ComCode does not store card details. Account access is not enabled yet.</span>
          </div>
        </aside>
      </div>
    </main>
  );
}
