import { Suspense } from "react";
import CheckoutStatus from "./checkout-status";

export default function CheckoutCompletePage() {
  return (
    <Suspense fallback={<main className="checkout-loading">Checking payment status…</main>}>
      <CheckoutStatus />
    </Suspense>
  );
}
