# Agent Metering, Entitlements, Billing & Revenue Assurance

Agent businesses increasingly sell to customers that are not sitting at a checkout page. A human, application, or autonomous agent may invoke a capability thousands of times, consume variable resources, cross plan limits, receive credits, retry failed work, or settle through machine-payment rails. The commercial system must still answer a simple question: **what was delivered, what was billable, what price applied, what was charged, and can every dollar be reproduced later?**

The objective is not to maximize billing complexity. It is to create a seller-side revenue system that is deterministic, explainable, auditable, and resilient enough for autonomous commerce.

This playbook is for founders building agent APIs, agent SaaS, agent-to-agent services, marketplaces, infrastructure products, usage-based products, outcome-priced services, or billing infrastructure for other agent businesses.

---

## 1. The revenue assurance loop

Use this lifecycle:

```text
Entitle -> Deliver -> Meter -> Rate -> Charge -> Settle -> Reconcile -> Recognize -> Audit -> Improve
   ^                                                                              |
   +-------------------------------- repeat ---------------------------------------+
```

Treat every stage as a separate control boundary.

1. **Entitle:** determine whether the customer or agent may use the capability.
2. **Deliver:** execute the requested work.
3. **Meter:** record canonical usage or successful outcomes.
4. **Rate:** apply the correct immutable pricing version.
5. **Charge:** create the financial obligation or consume prepaid balance.
6. **Settle:** collect through card, invoice, wallet, machine-payment rail, or internal balance.
7. **Reconcile:** prove usage, charges, receipts, and balances agree.
8. **Recognize:** hand off finalized commercial state to accounting/tax systems as appropriate.
9. **Audit:** reproduce any historical charge from evidence.
10. **Improve:** detect leakage, overbilling, abuse, pricing mistakes, and margin erosion.

Do not let the payment rail become the source of truth for product usage. Settlement proves money moved; it does not prove what the product delivered.

---

## 2. Define one canonical billable event

A billing system becomes fragile when every service invents its own interpretation of “usage.” Define a canonical event envelope first.

Minimum fields:

```json
{
  "event_id": "evt_01JXYZ...",
  "event_type": "research_report.completed",
  "occurred_at": "2026-08-27T07:10:12Z",
  "customer_id": "cus_123",
  "principal_id": "org_456",
  "agent_id": "agent_buyer_17",
  "contract_id": "ctr_2026_91",
  "entitlement_version": "ent_v7",
  "pricing_version": "price_2026_08_15",
  "capability": "company_research",
  "quantity": 1,
  "unit": "successful_report",
  "outcome": "accepted",
  "request_id": "req_8821",
  "delivery_id": "del_8821",
  "source": "research-service",
  "metadata": {
    "model_class": "standard",
    "region": "us-east"
  }
}
```

The event should be:

- immutable after acceptance,
- uniquely identified,
- attributable to a customer/principal,
- connected to the delivery request,
- tagged with the pricing and entitlement versions that applied,
- explicit about quantity and unit,
- explicit about whether the outcome qualified as billable,
- replayable into downstream billing systems.

Never derive billing solely from mutable application logs.

---

## 3. Separate operational telemetry from billable usage

Not every internal event should create revenue.

Examples of operational telemetry:

- model calls,
- retries,
- tool invocations,
- tokens generated,
- cache hits,
- internal agent handoffs,
- validation attempts,
- failed executions.

Examples of billable events:

- accepted report,
- resolved support case,
- qualified lead delivered,
- successful API request,
- GB processed,
- minute of compute,
- verified transaction,
- completed workflow.

A product may use operational telemetry to calculate cost while billing customers on an outcome metric.

```text
internal cost meter != customer billable meter
```

This distinction prevents accidental charging for retries or internal inefficiency.

---

## 4. Choose the right billing primitive

### Subscription

Best when customer value is recurring and usage variance is modest.

Examples:

- $499/month for an agent workspace,
- $2,000/month for a managed workflow,
- annual enterprise license.

### Usage

Best when marginal cost or value scales with consumption.

Examples:

- per API call,
- per minute,
- per document,
- per token bundle,
- per workflow execution.

### Outcome

Best when value is defined by a verifiable result.

Examples:

- per resolved ticket,
- per accepted record,
- percentage of recovered revenue,
- per booked qualified meeting.

Outcome billing requires an explicit acceptance policy and dispute mechanism.

### Prepaid credits

Best for autonomous buyers that need a hard spend ceiling.

Useful properties:

- no surprise invoice,
- deterministic budget cap,
- rapid settlement,
- easy per-agent suballocation.

### Hybrid

Often strongest for agent businesses:

```text
platform fee + included allowance + usage overage + optional outcome fee
```

Avoid pricing models that customers cannot independently reason about.

---

## 5. Entitlements are a product-control boundary

Billing answers what a customer owes. Entitlements answer what they may access.

Represent entitlements explicitly:

```json
{
  "customer_id": "cus_123",
  "plan": "growth",
  "version": "growth_v4",
  "features": {
    "research_api": true,
    "priority_queue": true,
    "custom_models": false
  },
  "limits": {
    "reports_month": 10000,
    "concurrent_jobs": 25,
    "daily_spend_usd": 500
  },
  "effective_at": "2026-08-01T00:00:00Z",
  "expires_at": null
}
```

Keep entitlement enforcement deterministic and close to the execution boundary.

Before performing expensive work, check:

- customer is active,
- requested capability is allowed,
- quantity remains within quota,
- autonomous spend authority remains valid,
- jurisdiction/data restrictions permit execution,
- required contract or consent is active.

Do not ask an LLM to decide whether a contractual limit applies when a rules engine can answer it.

---

## 6. Snapshot pricing at the moment liability is created

Pricing changes over time. Historical charges must remain explainable.

Store immutable pricing versions rather than looking up “current price” later.

Example:

```json
{
  "pricing_version": "price_2026_08_15",
  "currency": "USD",
  "metric": "successful_report",
  "model": "graduated",
  "tiers": [
    {"up_to": 1000, "unit_price": 0.20},
    {"up_to": 10000, "unit_price": 0.14},
    {"up_to": null, "unit_price": 0.10}
  ],
  "minimum_monthly": 499,
  "effective_from": "2026-08-15T00:00:00Z"
}
```

Every rated event should retain the applicable pricing version.

Do not retroactively reinterpret old usage because a plan changed.

---

## 7. Make idempotency non-negotiable

Autonomous systems retry aggressively. Networks fail. Webhooks redeliver. Workers crash after charging but before acknowledging.

Without idempotency, retries become duplicate revenue.

Use separate identifiers for:

- request,
- delivery,
- usage event,
- rated charge,
- settlement attempt,
- refund.

A safe charging rule:

```text
same billable_event_id + same pricing_version -> same charge exactly once
```

Store the result of the first successful rating/charge and return it for repeats.

Test deliberately for:

- duplicate event ingestion,
- out-of-order delivery,
- replay after timeout,
- worker restart,
- webhook redelivery,
- concurrent retries,
- partial downstream failure.

Exactly-once infrastructure is rare. Build **effectively-once financial behavior** using idempotent state transitions.

---

## 8. Design for late and out-of-order usage

Agent workflows can span minutes, hours, or days. Usage may arrive after the billing window appears closed.

Define policies for:

- allowed event lateness,
- backfills,
- correction windows,
- finalization time,
- rebilling thresholds,
- customer notification.

Example:

```text
usage window closes: month end
normal lateness accepted: 24h
reconciliation grace: 72h
invoice finalization: T+3 days
material late adjustment: next invoice with explicit credit/debit line
```

Never silently mutate a finalized invoice without an auditable adjustment trail.

---

## 9. Encode tiers, minimums, allowances, and credits explicitly

Pricing logic often fails at boundaries.

Test at least:

- zero usage,
- exactly at included allowance,
- one unit over allowance,
- tier boundary - 1,
- exact tier boundary,
- tier boundary + 1,
- minimum commitment below/above threshold,
- credit covering partial charge,
- expired credit,
- promotional vs purchased credit priority.

For prepaid credits, maintain a ledger rather than a single mutable balance.

```text
credit_grant_1 + credit_grant_2 - debit_1 - debit_2 = current balance
```

Each debit should reference the billable event or invoice line it funded.

---

## 10. Give autonomous buyers budget-aware failure modes

A human customer can receive an email about a failed payment. An autonomous buyer needs a machine-readable decision point.

Useful responses include:

```json
{
  "status": "payment_required",
  "reason": "budget_exhausted",
  "required_amount": 42.80,
  "available_amount": 17.20,
  "actions": [
    "request_budget_increase",
    "downgrade_service_tier",
    "reduce_quantity",
    "retry_after_funding"
  ]
}
```

Distinguish:

- credit exhausted,
- mandate limit reached,
- processor decline,
- invoice delinquency,
- settlement rail unavailable,
- suspicious spend blocked.

Do not collapse all cases into HTTP 402 with an opaque message.

---

## 11. Quote-to-charge reconciliation

A machine buyer may accept a quote before execution. The final charge should be reconcilable to that quote.

Store:

- quote ID,
- quote version,
- accepted unit price,
- quantity assumptions,
- minimums/tiers,
- expiration,
- taxes/fees if applicable,
- accepted SLA/credit terms.

Then compute:

```text
quoted commercial terms
+ actual eligible usage
+ explicit adjustments
= final rated amount
```

Flag any charge that cannot be explained through this equation.

---

## 12. Receipts should prove more than payment

For agent-to-agent commerce, a useful commercial receipt can connect settlement to service evidence.

Example fields:

```json
{
  "receipt_id": "rcpt_9921",
  "seller": "seller_42",
  "buyer": "buyer_17",
  "charge_id": "chg_721",
  "billable_event_ids": ["evt_a", "evt_b"],
  "pricing_version": "price_2026_08_15",
  "currency": "USD",
  "amount": 12.40,
  "settlement_ref": "pay_812",
  "delivery_proof": "sha256:...",
  "issued_at": "2026-08-27T07:20:00Z"
}
```

A receipt should let either side answer:

- what was purchased,
- what evidence qualified it as billable,
- what price applied,
- what money moved,
- whether a refund/credit later modified the transaction.

---

## 13. Refunds and service credits need first-class state

Do not delete original charges when correcting them.

Represent adjustments explicitly:

```text
original charge: +$100
service credit:  -$20
refund:          -$30
net commercial amount: $50
```

Track reasons such as:

- duplicate charge,
- quality failure,
- SLA breach,
- customer cancellation,
- fraud,
- delivery never completed,
- pricing configuration error,
- goodwill credit.

This preserves history for revenue assurance and dispute analysis.

---

## 14. Detect revenue leakage

Revenue leakage is delivered value that was never billed or was billed incorrectly low.

Common causes:

- events dropped before metering,
- customer mapping missing,
- unpriced usage,
- stale entitlement granting unintended free access,
- tier logic bug,
- failed usage sync,
- invoice line omitted,
- credit applied twice,
- manual override never expired,
- settlement succeeded but internal charge record failed.

Useful controls:

```text
eligible delivered events
vs.
metered events
vs.
rated events
vs.
charged events
vs.
settled events
```

Calculate stage-to-stage gaps daily.

Example leakage rate:

```text
estimated_unbilled_value / total_eligible_value
```

Track both dollar leakage and event-count leakage.

---

## 15. Detect overbilling with equal seriousness

Overbilling destroys trust faster than underbilling harms margin.

Detect:

- duplicate events,
- retried work charged twice,
- wrong pricing version,
- quantity inflation,
- credit not applied,
- cancelled subscription still metered,
- rejected outcome billed as successful,
- customer moved to lower-priced negotiated contract but old rate remains,
- invoice includes internal test traffic.

Build automatic anomaly checks such as:

```text
customer spend > 3x trailing median
usage flat but invoice jumps > 50%
charge exists without delivery proof
charge pricing_version != contract pricing_version
billable outcome = false AND rated amount > 0
```

High-confidence overbilling should stop finalization, not merely create a dashboard alert.

---

## 16. Free-tier farming and autonomous abuse

Agents can create accounts and exploit trial/credit systems at machine speed.

Defenses may include:

- verified principal identity,
- payment method or wallet binding,
- device/account graph signals,
- rate limits,
- credit velocity limits,
- per-principal trial eligibility,
- delayed high-cost features,
- abuse scoring,
- proof-of-work/value requirements for promotional credits.

Avoid controls that block legitimate multi-agent organizations. Prefer principal-level policy over naive “one agent ID = one customer” assumptions.

Measure promotional economics:

```text
promo_cost_per_activated_payer
promo_abuse_rate
credit_to_paid_conversion
```

---

## 17. Reconcile customer margin, not just revenue

Billing tells you what the customer paid. Unit economics tells you whether you should want more of that usage.

For each customer and capability track:

```text
net revenue
- model cost
- tool/API cost
- compute cost
- human review
- payment fees
- refunds/credits
- support allocation
= contribution margin
```

Then compute:

```text
revenue per successful outcome
cost per successful outcome
margin per successful outcome
```

A high-volume account can be unprofitable even when billing is technically correct.

Use margin signals to inform:

- price changes,
- routing,
- minimum commitments,
- included allowances,
- plan eligibility,
- customer success intervention.

---

## 18. Keep tax and accounting boundaries explicit

A metering system is not automatically a revenue-recognition or tax engine.

Define ownership boundaries for:

- invoice issuance,
- sales tax/VAT determination,
- tax IDs and exemptions,
- credit notes,
- revenue recognition,
- deferred revenue,
- currency conversion,
- accounts receivable,
- collections,
- financial close.

The billing layer should export deterministic commercial evidence. Accounting/tax treatment may vary by jurisdiction, contract, and business model; use qualified professionals where required.

---

## 19. Billing observability

Treat commercial infrastructure like production infrastructure.

Minimum dashboards:

### Metering health

- events ingested/minute,
- deduplication rate,
- invalid-event rate,
- ingestion lag,
- unmapped-customer events,
- late-event rate.

### Rating health

- rated events/minute,
- unpriced events,
- pricing-version mismatches,
- rating latency,
- adjustment rate.

### Settlement health

- charge success rate,
- failed-settlement rate,
- payment retry rate,
- prepaid balance failures,
- machine-payment rail errors.

### Revenue assurance

- delivered-to-metered gap,
- metered-to-rated gap,
- rated-to-charged gap,
- charged-to-settled gap,
- leakage dollars,
- overbilling alerts,
- refund/service-credit rate,
- dispute rate.

### Economics

- ARPU/ARPA,
- gross margin,
- contribution margin,
- revenue per successful outcome,
- cost per successful outcome,
- margin by capability/customer/plan.

---

## 20. Define billing SLOs

Example service objectives:

```text
99.99% of accepted usage events durably recorded
99.9% of usage visible in customer balance within 60 seconds
100% of rated charges reference immutable pricing version
0 duplicate finalized charges for same billable_event_id
99.99% of finalized invoice lines reproducible from evidence
<0.1% unexplained delivered-to-billed value gap
100% high-severity overbilling alerts block invoice finalization
```

Your exact targets depend on transaction value and volume, but define them before incidents happen.

---

## 21. Incident response for billing failures

Commercial incidents need a dedicated playbook.

Severity examples:

### SEV-1

- widespread duplicate charging,
- materially incorrect invoices already collected,
- prepaid balances corrupted,
- unauthorized entitlement grants causing large exposure.

### SEV-2

- metering backlog risks delayed invoice,
- a pricing segment is rated incorrectly but not finalized,
- one settlement rail unavailable with fallback available.

Immediate actions:

1. freeze affected invoice finalization or charging,
2. preserve raw events and pricing snapshots,
3. identify affected customers and time window,
4. stop unsafe replay/repair jobs,
5. calculate under/overbilling exposure,
6. repair through idempotent backfill or explicit adjustments,
7. notify customers when appropriate,
8. publish internal postmortem and prevention controls.

Never “fix” financial history by deleting evidence.

---

## 22. Backfills must be deterministic

Eventually you will need to replay usage.

Safe backfill requirements:

- immutable source events,
- versioned transformation logic,
- dry-run mode,
- before/after totals,
- idempotent writes,
- bounded customer/time scope,
- operator approval for material financial impact,
- audit record of the backfill job.

A good test:

```text
replay same source twice -> identical final commercial state
```

---

## 23. Build a revenue assurance ledger

For high-value agent commerce, maintain an append-only commercial ledger that links:

```text
delivery evidence
-> billable event
-> pricing version
-> rated charge
-> adjustment(s)
-> settlement(s)
-> refund(s)
-> accounting export
```

The ledger does not need to be a blockchain. It needs immutable identifiers, durable history, and reproducible transformations.

Use cryptographic hashes/signatures when counterparty verification or tamper evidence materially improves trust.

---

## 24. Agent-to-agent billing contracts

Machine buyers need pricing that software can understand.

Expose structured commercial metadata such as:

```json
{
  "capability": "company_research",
  "billing_metric": "accepted_company_record",
  "currency": "USD",
  "unit_price": 0.12,
  "minimum_charge": 1.00,
  "included": 0,
  "settlement": ["prepaid", "invoice", "machine_payment"],
  "refund_policy": "failed_acceptance_test",
  "quote_required_above": 1000,
  "pricing_version": "2026-08-15"
}
```

The buyer should be able to simulate expected spend before invocation.

Seller agents should expose:

- price metric,
- unit definition,
- acceptance definition,
- caps/minimums,
- settlement methods,
- credit/refund rules,
- quote expiry,
- pricing version.

Ambiguous natural-language pricing does not scale to autonomous markets.

---

## 25. Outcome billing needs a verifier

If the product charges only on success, define success independently from the seller’s revenue incentive.

Possible verifiers:

- deterministic schema validation,
- customer acceptance signal,
- third-party data match,
- test suite,
- signed delivery receipt,
- marketplace escrow release,
- independent evaluator agent.

Avoid circular logic:

```text
seller says outcome succeeded -> seller charges
```

Prefer:

```text
delivery -> verifier -> accepted/rejected -> billable event
```

Store verifier version and evidence with the event.

---

## 26. Billing evals

Billing logic deserves regression tests just like agent behavior.

Create fixtures for:

- normal subscription cycle,
- usage below allowance,
- overage,
- graduated vs volume tiering,
- mid-cycle upgrade,
- downgrade,
- plan cancellation,
- prepaid exhaustion,
- credit expiry,
- duplicate usage,
- late event,
- backfill,
- rejected outcome,
- partial refund,
- SLA credit,
- negotiated pricing override,
- currency mismatch,
- quote expiration,
- autonomous spend-cap rejection.

For every fixture assert:

```text
entitlement decision
metered quantity
pricing version
rated amount
settlement state
ledger balance
customer-visible explanation
```

Use golden test cases for financially material rules.

---

## 27. Customer-visible billing evidence

Trust improves when customers can inspect their own usage.

Provide:

- current entitlement state,
- remaining allowance/credit,
- near-real-time usage,
- projected spend,
- per-event or aggregated usage evidence,
- pricing version,
- invoices/receipts,
- credits/refunds,
- dispute path.

For autonomous customers, expose the same through an API—not only a dashboard.

Useful endpoints:

```text
GET /entitlements
GET /usage
GET /balance
GET /charges/{id}/evidence
GET /pricing/current
POST /spend-alerts
POST /disputes
```

---

## 28. Revenue assurance metrics

Track at minimum:

```text
billable usage volume
billed revenue
settled revenue
recognized commercial amount
revenue leakage rate
overbilling alert rate
duplicate-event rate
unpriced-event rate
refund rate
service-credit rate
dispute rate
failed-settlement rate
ARPU / ARPA
gross margin
contribution margin
revenue per successful outcome
margin per successful outcome
```

Also segment by:

- plan,
- capability,
- customer,
- buyer-agent identity,
- acquisition channel,
- pricing version,
- settlement rail.

This turns billing from back-office plumbing into a pricing and product feedback loop.

---

## 29. Business opportunities

The agent economy creates new infrastructure businesses around seller-side revenue operations.

### Agent-native metering

Meter high-volume agent/API usage with event deduplication, attribution, and real-time balances.

### Entitlement control plane

Machine-enforce features, quotas, delegated spend, and plan versions across agent fleets.

### Revenue assurance

Continuously compare delivered value, rated usage, invoices, and settlement to detect leakage or overbilling.

### Agent billing gateway

Translate machine-readable capability pricing into metering, rating, balance enforcement, receipts, and multiple settlement rails.

### Outcome verification + billing

Verify successful outcomes and emit trusted billable events.

### Machine-commerce ledger

Provide tamper-evident transaction evidence for agent-to-agent purchases, adjustments, refunds, and disputes.

### Billing observability

Detect abnormal spend, duplicate charges, pricing drift, usage gaps, and margin deterioration.

### Autonomous budget/entitlement infrastructure

Give organizations a control layer to allocate budgets and entitlements to thousands of agents while preserving principal-level accounting.

The strongest opportunities are likely where financial correctness, trust, and interoperability matter more than adding another checkout UI.

---

## 30. Minimum viable billing architecture

A small agent business does not need an enterprise billing platform on day one.

Start with:

```text
Product service
  -> immutable usage events
  -> simple meter
  -> versioned pricing rules
  -> idempotent charge records
  -> payment/invoice provider
  -> reconciliation job
  -> customer usage view
```

Add complexity only when revenue forces it.

Good early controls:

- one canonical billable metric,
- one pricing version table,
- idempotency key on every financial write,
- daily reconciliation,
- customer-visible usage,
- manual approval for large adjustments.

Do not build a generalized billing platform before validating willingness to pay for the underlying product.

---

## 31. Scale architecture

At higher volume, separate responsibilities:

```text
Execution services
   |
   v
Usage event bus ---> raw immutable event store
   |                         |
   v                         v
Metering/aggregation     replay/backfill
   |
   +--> entitlement/limit engine
   |
   v
Rating engine ---> commercial ledger ---> invoice/payment adapters
   |                    |                         |
   v                    v                         v
customer usage       reconciliation           settlement receipts
```

Keep payment providers replaceable. The canonical usage and commercial ledger should remain under your control or independently exportable.

---

## 32. Build vs buy checklist

Buy billing infrastructure when:

- pricing patterns are standard,
- provider supports your usage volume,
- event export/replay exists,
- idempotency and credits are mature,
- pricing/version history is explainable,
- customer portal saves material engineering time.

Build more internally when:

- outcome verification is proprietary,
- agent-to-agent contracts are unusual,
- latency requires inline entitlement checks,
- multi-principal budgets are core IP,
- marketplace settlement/revenue sharing is complex,
- provider abstraction is strategically important.

Even when buying, retain an independent record of product usage and contract/pricing state.

---

## 33. Launch checklist

Before charging the first autonomous customer:

- [ ] define the canonical billable event,
- [ ] define success/acceptance criteria,
- [ ] separate internal retries from customer usage,
- [ ] enforce entitlements before expensive execution,
- [ ] snapshot pricing versions,
- [ ] implement event and charge idempotency,
- [ ] test tier/allowance boundaries,
- [ ] implement hard spend caps for prepaid/autonomous buyers,
- [ ] expose machine-readable usage and balance,
- [ ] reconcile delivered -> metered -> rated -> charged -> settled,
- [ ] define refund/service-credit paths,
- [ ] alert on unpriced usage,
- [ ] alert/block likely overbilling,
- [ ] test replay/backfill,
- [ ] preserve immutable evidence,
- [ ] track margin per successful outcome.

---

## 34. Questions every founder should answer

1. What exactly creates a billable event?
2. Can the customer independently understand that metric?
3. What events are explicitly not billable?
4. Where is entitlement checked?
5. What happens when an autonomous buyer runs out of budget?
6. Can the same event be delivered 10 times without being charged 10 times?
7. Which pricing version applies to historical usage?
8. Can you reproduce a charge six months later?
9. Can you distinguish delivery, billing, and settlement failures?
10. What percentage of delivered value never becomes a charge?
11. How do you detect overbilling before collection?
12. Who approves large credits/refunds?
13. What happens when usage arrives late?
14. Can customers inspect usage through an API?
15. Which customers are revenue-positive but margin-negative?
16. Can a buyer agent predict spend before invocation?
17. What evidence resolves a dispute?
18. Can you replay the meter without changing the financial outcome?
19. What is your failed-settlement fallback?
20. What commercial state is independently exportable if a billing vendor changes?

---

## 35. Operating principle

The seller-side rule for agent commerce is:

> **No money without evidence, no evidence without identity, no charge without a pricing version, and no retry without idempotency.**

A durable agent business should be able to reconstruct this chain for every material dollar:

```text
principal authority
-> entitlement
-> delivered outcome
-> canonical billable event
-> immutable pricing version
-> rated charge
-> settlement evidence
-> adjustment history
-> final commercial state
```

That chain is what turns machine-speed usage into trustworthy revenue rather than a stream of unexplained transactions.

---

## References and ecosystem signals

Use vendor documentation as implementation reference, not as the business system of record.

- Stripe Billing Entitlements documents explicit product-feature entitlements that can be provisioned or revoked from subscription state.
- OpenMeter documents real-time event-based metering, deduplication, customer attribution, usage limits, entitlements, prepaid credits, and AI/agent usage metering.

The durable architectural lesson is vendor-neutral: keep usage evidence, entitlement state, pricing versions, and settlement references independently auditable so billing can be reconciled even when providers or rails change.