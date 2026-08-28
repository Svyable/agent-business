# Agent Pricing, Packaging, Metering & Deal Desk

Agent businesses should be able to answer five commercial questions before a quote reaches a buyer:

1. **What exactly is the customer buying?**
2. **What event creates a billable unit?**
3. **Does the price clear the real delivery-cost and margin floor?**
4. **How can the customer bound and independently understand spend?**
5. **Who is actually authorized to change price, credits, or terms?**

This guide turns the high-level models in `docs/MONETIZATION.md` into an executable commercial contract. It sits upstream of `docs/AGENT_BILLING_REVENUE_ASSURANCE.md`: pricing defines the package and commercial rules; billing deterministically applies the accepted version to delivered events.

This is commercial operating guidance, not tax, accounting, legal, or market-specific pricing advice. Tax determination belongs in `docs/AGENT_FISCAL_OPERATIONS.md`. Contract authority must come from the real operating environment, never from this repository.

## 1. Start with the billable unit, not the sticker price

The fastest way to create pricing disputes is to price an undefined word such as “conversation,” “task,” “resolution,” “lead,” or “action.”

For every package, write one sentence that a buyer, seller, and billing system can all evaluate:

```text
One billable unit occurs when <observable trigger> satisfies <acceptance rule>,
identified by <deduplication key>, excluding <provider/customer exceptions>.
```

Examples:

```text
One report is billable when the final report passes the agreed acceptance checks
and is delivered under one delivery_id. Provider retries and rejected drafts are excluded.
```

```text
One support outcome is billable when the conversation meets the agreed resolution
rule after the acceptance window. A conversation can create at most one outcome charge.
```

Do not let internal cost events become billable events accidentally. Model calls, tool calls, retries, cache misses, internal handoffs, and evaluation runs usually belong in the cost model, not on the customer invoice.

## 2. Choose pricing architecture by value and risk

### Subscription

Use when recurring availability and continuity are the main value and marginal usage variance is bounded.

Good controls:
- clear included capabilities,
- usage/fair-use boundary,
- renewal/change notice,
- defined support level.

### Usage

Use when customer value or marginal delivery cost scales with a measurable quantity.

Good meters are externally comprehensible: document, minute, GB, workflow, accepted API operation. Avoid exposing tokens as the customer meter unless the customer explicitly buys inference capacity.

### Outcome

Use when successful results can be defined and attribution is defensible.

Outcome pricing requires more evidence, not less. Define:
- success,
- attribution,
- acceptance window,
- customer-side failure exclusions,
- duplicate/retry treatment,
- dispute process,
- evidence retained per outcome.

### Hybrid

Often the best fit for production agent businesses:

```text
platform/minimum commitment
+ included allowance
+ usage or verified-outcome overage
+ bounded service credits
```

This can fund fixed implementation/support while preserving a value-aligned variable component.

### Setup + recurring

Useful for integration-heavy services. The setup fee should fund real onboarding/configuration work rather than disguise an arbitrary margin plug.

### Marketplace take rate

Use when the business facilitates a transaction or match. Define which transaction value is commissionable, when it becomes final, refund/cancellation treatment, and whether buyer/seller fees can stack.

### Enterprise commitment

Use when procurement, security, support, deployment, reserved capacity, or custom terms justify a negotiated commitment. Treat nonstandard terms as deal-desk state, not free-form sales text.

## 3. Separate meter, price, and cost

These are different objects:

```text
customer meter: what creates a billable unit
pricing rule: what the customer owes for that unit/package
cost model: what the seller spends to deliver it
```

A support agent may be billed per verified resolution while internally consuming dozens of model/tool events. A research agent may be billed by accepted report while its cost varies with search depth. This separation is essential for both customer trust and margin control.

## 4. Link every quote to workflow economics

Use `scripts/workflow_roi.py` and the workflow ROI record to estimate fully loaded delivery cost. At minimum include:

- inference/context,
- tools/data,
- compute,
- retries,
- human review,
- failure recovery,
- support/operations,
- payment/refund variable cost where applicable.

Then calculate expected contribution margin per billable unit:

```text
expected contribution margin
= (expected net price - expected fully loaded delivery cost)
  / expected net price
```

Store both:
- **target margin** — what the package is designed to achieve;
- **minimum margin floor** — below this, the quote must be rejected or escalated.

Do not save a deal by pretending delivery cost is only model tokens.

## 5. Discount against economics, not emotion

A discount changes unit economics. Before approving one, recompute the expected net price and margin.

Deal-desk policy should define:

```text
seller/agent discount authority
manager approval threshold
absolute maximum discount
minimum contribution margin
setup-fee waiver authority
minimum-commitment change authority
service-credit authority and cap
nonstandard-term approval authority
```

The machine record stores actual authority provenance. The repository starter grants none.

A useful rule:

```text
discount is allowed only when
requested_discount <= delegated_discount_limit
AND post-discount margin >= margin floor
AND quote is still inside effective evidence/approval windows
```

## 6. Make customer spend predictable

Autonomous consumption can move faster than a human finance review. Every variable package should make spend behavior explicit.

Choose at least one strong control:
- prepaid balance,
- monthly hard cap,
- per-agent sub-budget,
- alert thresholds,
- throttling after threshold,
- downgrade/fallback mode,
- explicit approval before overage.

Prefer multiple warning thresholds such as 50%, 80%, and 95% before a hard ceiling.

Never rely on “the customer can watch the dashboard” as the only budget control for machine-speed usage.

## 7. Included units, overages, and commitments

Document boundary behavior precisely.

Test:
- zero usage,
- exactly included usage,
- one unit over,
- tier boundary - 1 / exact / + 1,
- minimum commitment with low usage,
- prepaid balance exhaustion,
- expired promotional credit,
- overage above hard cap,
- mid-period package change.

For committed use, specify whether unused commitment:
- expires,
- rolls forward,
- converts to another capability,
- is refundable,
- can be reallocated across agents/accounts.

## 8. Outcome pricing needs attribution rules

A seller should not charge merely because its agent touched a workflow.

For an outcome define:

```text
success event
observation/acceptance window
required evidence
maximum charges per canonical object
customer-side exclusions
provider-side exclusions
dispute window
finalization rule
```

Examples of exclusions:
- duplicate provider retry,
- workflow failed before acceptance,
- internal test traffic,
- customer cancelled before completion,
- customer did not provide required access/data,
- success was already achieved by another channel before the agent intervention.

Use conservative attribution when multiple systems contributed.

## 9. Service credits are not free-form refunds

A service credit should have:
- reason,
- maximum amount,
- authority source,
- contract/SLA linkage when applicable,
- expiration/usage treatment,
- explicit adjustment record in billing.

Do not delete original charge history. The billing layer should represent the credit as an auditable adjustment.

## 10. Quote lifecycle

Use explicit state:

```text
draft -> needs_review -> quote_ready -> active -> retired
```

### Draft
May contain incomplete economics or customer assumptions. Not sendable.

### Needs review
A real package being evaluated. Still not sendable unless real authority says otherwise.

### Quote ready
Requires:
- unambiguous customer-verifiable meter,
- retry/duplicate exclusions,
- current economics evidence,
- margin above floor,
- bounded spend behavior,
- current quote expiry,
- real quote authority provenance.

### Active
Commercial terms are accepted/effective and become the pricing source referenced by metering/rating systems.

### Retired
Preserve for historical charge reconstruction. Never reinterpret old usage under a replacement price version.

## 11. Change and repricing protocol

Never silently reprice active customers.

For each change record:
- old package/version,
- new package/version,
- reason,
- effective date,
- required notice period,
- affected segment/accounts,
- grandfathering rule,
- open quote treatment,
- prepaid/commitment migration,
- expected margin and retention impact.

Coordinate with:
- `docs/AGENT_CUSTOMER_SUCCESS_RETENTION.md` for renewal/retention risk,
- service-contract records for accepted terms,
- billing for pricing-version enforcement,
- fiscal operations for taxes/invoice requirements.

## 12. Price experiments

Do not treat a pricing test as “we changed the price and conversion moved.” Track the entire experiment context:

| Field | Capture |
|---|---|
| Segment | Who saw it? |
| Problem/offer | What outcome was promised? |
| Package | What was included/excluded? |
| Meter | What was billable? |
| Price | List and effective net price |
| Channel | How was it sold? |
| Conversion | Qualified denominator and result |
| Activation | Did buyers reach first value? |
| Delivery cost | Fully loaded cost/outcome |
| Retention | Renewal/continued-use signal |
| Objections | Price vs scope vs trust vs procurement |

Change one major commercial variable at a time when possible. A large discount that improves conversion but creates negative-margin retained customers is not a successful pricing experiment.

## 13. Deal-desk operating queue

A lightweight deal desk can be a deterministic review queue rather than a department.

Escalate when:
- requested discount exceeds delegated limit,
- margin falls below floor,
- buyer asks for uncapped usage,
- setup fee/minimum is waived outside policy,
- service credits exceed authority,
- outcome definition changes,
- billing unit differs from provider cost assumptions materially,
- quote currency changes,
- contract term exceeds standard duration,
- customer asks for bespoke refund/SLA/termination language,
- pricing evidence is stale.

The output should be a decision plus evidence, not merely “approved by sales.”

## 14. Cross-border and tax boundary

Keep commercial price and fiscal treatment separate.

The pricing record can say:

```text
list/net price: USD 2.00 per verified outcome
prices: exclusive of applicable taxes
```

But it must not invent:
- tax jurisdiction,
- VAT/sales-tax rate,
- exemption,
- withholding treatment,
- invoice legal requirements.

Those belong in the fiscal evidence record, sourced to current jurisdiction evidence.

## 15. Agent-to-agent quoting

Machine buyers benefit from a compact quote contract containing:
- package/version,
- capability,
- billable unit definition,
- price/currency,
- included units/minimum,
- overage rule,
- spend cap,
- effective/expiry timestamps,
- outcome acceptance/dispute rule,
- authority/contract reference,
- pricing evidence/version.

A buyer agent should be able to compare two offers without parsing marketing prose.

Do not let one agent infer that another agent has authority to accept a quote merely because it can call a payment or procurement tool. Buyer-side authority still needs its own current delegation.

## 16. Failure-mode evals

At minimum test these before activating a pricing system:

1. **Retry double-bill** — one workflow retries three times; only one eligible charge can result.
2. **Ambiguous outcome** — “resolved” has no acceptance rule; quote cannot become ready.
3. **Customer-side failure** — required input was withheld; outcome attribution follows documented exclusion.
4. **Negative-margin discount** — discount is within salesperson percentage limit but crosses margin floor; reject.
5. **Unauthorized discount** — requested discount exceeds delegated limit; reject/escalate.
6. **Unauthorized credit** — service credit exceeds delegated cap; reject/escalate.
7. **Expired quote** — old quote cannot be newly accepted/rated silently.
8. **Silent repricing** — active customer is moved to a new price without required change evidence/notice; block.
9. **Unbounded overage** — variable pricing has neither hard cap nor approval/alert controls; block.
10. **Meter mismatch** — customer expects completed workflow but provider charges attempted actions; block quote until reconciled.
11. **Stale cost evidence** — margin model depends on superseded delivery cost; return to review.
12. **Duplicate customer object** — multiple delivery events reference one canonical outcome; deduplicate before rating.
13. **Currency confusion** — quote currency differs from contract/billing without explicit conversion/change process; escalate.
14. **Tax confusion** — sales tax/VAT assumptions appear inside pricing logic without fiscal evidence; separate and review.
15. **Credit plus refund** — same failure receives overlapping credit/refund unintentionally; billing reconciliation catches double adjustment.

## 17. Metrics that improve pricing decisions

Track by package/segment:
- realized net price per billable unit,
- fully loaded cost per billable unit,
- contribution margin,
- discount distribution,
- service credits/refunds,
- percentage hitting usage cap,
- overage conversion/approval rate,
- quote-to-close rate,
- activation,
- renewal/expansion,
- outcome dispute rate,
- billing dispute rate,
- meter reconciliation failures.

A pricing model is healthy when customers understand it, sellers can enforce it, billing can reproduce it, and economics remain attractive after real production behavior.

## 18. Machine-readable workflow

Start from:

```bash
cp templates/PRICING_PACKAGE.json pricing-package.json
```

Customize the package, then validate:

```bash
python scripts/validate_pricing_package.py pricing-package.json
```

The starter is intentionally not quote-ready and grants no commercial authority.

The validator blocks operational states when, among other failures:
- outcome/meter semantics are incomplete,
- retries/duplicates are not excluded,
- economics lack current evidence,
- expected margin is below the declared floor,
- discounts or service credits exceed authority,
- quote authority/provenance is missing,
- the quote is expired,
- variable spend is insufficiently bounded,
- prohibited sensitive fields appear.

Treat passing validation as a necessary control, not as evidence that the market will accept the price. Customer willingness to pay still requires real selling and outcome evidence.
