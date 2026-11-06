"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

const apiUrl = (
  process.env.NEXT_PUBLIC_BILLING_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

type PaymentState = {
  status: string;
  plan: string;
};

export default function CheckoutStatus() {
  const searchParams = useSearchParams();
  const reference = searchParams.get("reference") ?? "";
  const [payment, setPayment] = useState<PaymentState | null>(null);
  const [error, setError] = useState("");
  const invalidReference = !/^[0-9a-f-]{36}$/i.test(reference);

  useEffect(() => {
    if (invalidReference) return;

    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    async function refreshStatus() {
      try {
        const response = await fetch(
          `${apiUrl}/api/billing/payments/${encodeURIComponent(reference)}`,
          { cache: "no-store" },
        );
        if (!response.ok) {
          throw new Error("We could not retrieve the payment status.");
        }
        const result = (await response.json()) as PaymentState;
        if (active) {
          setPayment(result);
          if (
            result.status === "pending" ||
            result.status === "awaiting_payment" ||
            result.status === "awaiting_subscription"
          ) {
            timer = setTimeout(() => void refreshStatus(), 3000);
          }
        }
      } catch (statusError) {
        if (active) {
          setError(
            statusError instanceof Error
              ? statusError.message
              : "We could not retrieve the payment status.",
          );
        }
      }
    }

    void refreshStatus();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [invalidReference, reference]);

  const complete = payment?.status === "succeeded";
  const visibleError = invalidReference
    ? "The payment reference is missing or invalid."
    : error;
  const stillProcessing =
    payment?.status === "pending" ||
    payment?.status === "awaiting_payment" ||
    payment?.status === "awaiting_subscription";

  return (
    <main className="checkout-page">
      <header className="checkout-header">
        <Link aria-label="ComCode home" className="brand" href="/">
          <span aria-hidden="true" className="brand-mark">c</span>
          <span>comcode</span>
        </Link>
        <Link className="checkout-back" href="/#plans">Back to plans</Link>
      </header>
      <section aria-live="polite" className="checkout-result">
        <span className={`result-mark${complete ? " result-complete" : ""}`}>
          {complete ? "✓" : "…"}
        </span>
        <div className="eyebrow">PAYMENT STATUS</div>
        <h1>
          {complete
            ? "Payment confirmed."
            : stillProcessing
              ? "Confirming your payment."
              : visibleError
                ? "We couldn’t confirm that yet."
                : payment?.status === "failed"
                  ? "Payment wasn’t completed."
                  : "Checking your payment."}
        </h1>
        <p>
          {complete
            ? `Your ${payment?.plan} membership payment is confirmed. Account access will be linked after student sign-in is added.`
            : stillProcessing
              ? "This page updates when the provider confirms your payment. M-Pesa payments require you to approve the prompt on your phone."
              : visibleError
                  ? visibleError
                : payment?.status === "review_required"
                  ? "Your payment is being checked. Please contact support if this status does not change."
                  : "If you just approved a payment, allow a moment for the provider to notify us."}
        </p>
        {payment && (
          <span className="result-reference">
            Reference: {reference} · Status: {payment.status.replaceAll("_", " ")}
          </span>
        )}
        {visibleError && <Link className="button button-dark" href="/checkout">Return to checkout</Link>}
        <Link className="result-home-link" href="/">Return to ComCode</Link>
      </section>
    </main>
  );
}
