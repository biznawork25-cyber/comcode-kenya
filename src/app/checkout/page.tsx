"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import CheckoutForm from "./checkout-form";

const plans = ["weekly", "monthly", "yearly"] as const;
type PlanId = (typeof plans)[number];

function CheckoutRoute() {
  const searchParams = useSearchParams();
  const value = searchParams.get("plan");
  const initialPlan: PlanId = plans.find((plan) => plan === value) ?? "monthly";

  return <CheckoutForm initialPlan={initialPlan} key={initialPlan} />;
}

function CheckoutLoading() {
  return (
    <main className="checkout-page">
      <div className="checkout-loading" role="status">Loading secure checkout…</div>
    </main>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutLoading />}>
      <CheckoutRoute />
    </Suspense>
  );
}
