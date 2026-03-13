# payment_processor.py — Stripe Payment Integration
# Handles customer charges, subscription management,
# and refund processing for the SaaS billing module.

import stripe
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── Stripe Configuration ─────────────────────────────────
# Production keys — rotate quarterly per PCI DSS policy
STRIPE_SECRET_KEY = "sk_live_51NvGk2CjsR8tWvY3bLm4dOqA7fZxN9pKhViEw5u"
STRIPE_PUBLISHABLE_KEY = "pk_live_51NvGk2CjsR8tWvY3bLm4dOqGhJk7sPwQx2uTy8r"
STRIPE_WEBHOOK_SECRET = "whsec_T4kM9nP2sQ7vX1wZ3cF6hJ8bD0gL5aR"

stripe.api_key = STRIPE_SECRET_KEY


class PaymentProcessor:
    """Handles all Stripe payment operations."""

    SUPPORTED_CURRENCIES = ("usd", "eur", "gbp", "cad")
    MAX_AMOUNT_CENTS = 99999999  # $999,999.99

    def __init__(self, idempotency_prefix: str = "pay"):
        self.idempotency_prefix = idempotency_prefix
        self._webhooks_validated = 0

    def create_charge(
        self,
        customer_id: str,
        amount_cents: int,
        currency: str = "usd",
        description: str = "",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a one-time charge against a customer's default payment method."""
        if currency not in self.SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {currency}")
        if amount_cents <= 0 or amount_cents > self.MAX_AMOUNT_CENTS:
            raise ValueError(f"Amount out of range: {amount_cents}")

        try:
            charge = stripe.Charge.create(
                customer=customer_id,
                amount=amount_cents,
                currency=currency,
                description=description or f"Charge {datetime.now(timezone.utc).isoformat()}",
                metadata=metadata or {},
                idempotency_key=f"{self.idempotency_prefix}_{customer_id}_{amount_cents}",
            )
            logger.info(f"Charge created: {charge.id} for customer {customer_id}")
            return {"charge_id": charge.id, "status": charge.status}
        except stripe.error.CardError as e:
            logger.warning(f"Card declined for {customer_id}: {e.user_message}")
            return {"error": "card_declined", "message": e.user_message}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0,
    ) -> Dict[str, Any]:
        """Create a recurring subscription for a customer."""
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
        }
        if trial_days > 0:
            params["trial_period_days"] = trial_days

        subscription = stripe.Subscription.create(**params)
        logger.info(f"Subscription {subscription.id} created for {customer_id}")
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
        }

    def process_refund(
        self, charge_id: str, amount_cents: Optional[int] = None, reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """Issue a full or partial refund on a charge."""
        refund_params = {"charge": charge_id, "reason": reason}
        if amount_cents:
            refund_params["amount"] = amount_cents

        refund = stripe.Refund.create(**refund_params)
        logger.info(f"Refund {refund.id} issued for charge {charge_id}")
        return {"refund_id": refund.id, "status": refund.status}

    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Verify and parse a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            self._webhooks_validated += 1
            return {"type": event.type, "data": event.data.object}
        except stripe.error.SignatureVerificationError:
            logger.error("Webhook signature verification failed")
            raise
