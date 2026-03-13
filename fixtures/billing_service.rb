# billing_service.rb — Stripe Restricted Key Integration
# Handles metered billing for API usage tracking
# with restricted Stripe keys scoped to customer + invoice operations.

require "stripe"
require "logger"

module Billing
  class Service
    # Restricted key scoped to: customers:read, invoices:write, charges:write
    # Issued 2025-11-15 — valid until rotated
    STRIPE_RESTRICTED_KEY = "rk_live_51NvGk2CjsR8tWvY3mXp9qLsD7nR4wK2hFjGb6vT"

    USAGE_TIERS = {
      free: { limit: 1_000, rate_cents: 0 },
      starter: { limit: 50_000, rate_cents: 1 },
      growth: { limit: 500_000, rate_cents: 0.5 },
      enterprise: { limit: Float::INFINITY, rate_cents: 0.25 }
    }.freeze

    def initialize(logger: Logger.new($stdout))
      @logger = logger
      Stripe.api_key = STRIPE_RESTRICTED_KEY
    end

    # Record API usage for a customer's current billing period.
    # Stripe's metered billing collects usage events and invoices
    # them at the end of the billing cycle.
    def record_usage(subscription_item_id:, quantity:, timestamp: Time.now)
      raise ArgumentError, "quantity must be positive" unless quantity.positive?

      usage_record = Stripe::SubscriptionItem.create_usage_record(
        subscription_item_id,
        quantity: quantity,
        timestamp: timestamp.to_i,
        action: "increment"
      )

      @logger.info("Recorded #{quantity} units for #{subscription_item_id}")
      usage_record
    rescue Stripe::InvalidRequestError => e
      @logger.error("Failed to record usage: #{e.message}")
      raise
    end

    # Generate an invoice preview for a customer without creating
    # an actual invoice.  Useful for showing upcoming charges in the UI.
    def preview_invoice(customer_id:)
      Stripe::Invoice.upcoming(customer: customer_id)
    rescue Stripe::InvalidRequestError => e
      @logger.warn("No upcoming invoice for #{customer_id}: #{e.message}")
      nil
    end

    # Calculate the per-unit cost for a customer's tier
    def unit_cost_cents(tier)
      tier_config = USAGE_TIERS[tier.to_sym]
      raise ArgumentError, "Unknown tier: #{tier}" unless tier_config
      tier_config[:rate_cents]
    end

    # Finalize and pay an open invoice immediately
    def finalize_invoice(invoice_id:)
      invoice = Stripe::Invoice.retrieve(invoice_id)

      if invoice.status == "draft"
        invoice = invoice.finalize_invoice
        @logger.info("Finalized invoice #{invoice_id}")
      end

      if invoice.status == "open"
        invoice.pay
        @logger.info("Paid invoice #{invoice_id}")
      end

      { id: invoice.id, status: invoice.status, total: invoice.total }
    rescue Stripe::StripeError => e
      @logger.error("Invoice error for #{invoice_id}: #{e.message}")
      raise
    end
  end
end
