# Agent Recurring Payment Mandates, Renewals, and Revocation

A one-time payment approval answers whether an agent may execute **one transaction**. A recurring mandate answers a harder question: **under what bounded, versioned, revocable authority may an agent cause a series of future payments without asking for fresh approval each time?**

This playbook gives agent founders an operating contract for subscriptions, usage-based recurring purchases, standing API/compute spend, replenishment, maintenance services, and other repeated autonomous payments.

> **Core rule:** a successful past payment, stored payment credential, active subscription, or technical ability to charge is not standing authority for future payments.

## Why recurring authority is a separate control object

The repository's machine-payment system governs a transaction from authorization through settlement, reconciliation, dispute, and reversal. A recurring mandate sits *above* those child transactions. It defines which future transactions may be created and how that durable authority changes over time.

Without a dedicated mandate layer, agent systems can accidentally:

- treat a one-time approval as permission to keep charging;
- split spend into many small payments that exceed an aggregate budget;
- renew after a material price or terms change without new authority;
- continue charging after the principal pauses or revokes the mandate;
- retry a failed charge after the mandate has expired;
- confuse possession of a tokenized credential with permission to use it;
- cancel payment authority while leaving the underlying service contract active, or cancel service while leaving charge authority live;
- lose provenance showing which mandate version authorized a specific child payment.

Current agentic-payment work is already moving beyond single purchases toward recurring transactions and delegated purchases under predefined parameters. The safe design principle is therefore to make standing authority explicit, narrow, observable, and revocable.

## Lifecycle

Use one durable mandate identity across its entire life:

```text
proposed
   ↓
approved
   ↓
active ─────────────┐
   │                │
   ├→ used          │
   ├→ modified      │
   ├→ renewal_due   │
   ├→ paused        │
   └→ revocation_requested
                    ↓
             revoked | expired
                    ↓
               reconciled
                    ↓
                  closed
```

A modification or renewal that changes material economics should create a **new mandate version**, not silently overwrite the old one.

### State meanings

| State | Meaning | Must not be inferred |
|---|---|---|
| `proposed` | Candidate standing authority is being assembled. | No future payment authority exists. |
| `approved` | Required approver has accepted the bounded mandate. | It is not active before its start time or activation conditions. |
| `active` | Current version may authorize child payments within all bounds. | Any arbitrary payment to the payee is allowed. |
| `used` | At least one child payment consumed mandate capacity. | The mandate has renewed or gained more budget. |
| `modified` | A new version changes one or more terms. | Prior approval automatically covers material changes. |
| `renewal_due` | A renewal decision or notice window has arrived. | Renewal has already been authorized. |
| `paused` | New child payments are temporarily blocked. | The service contract is terminated. |
| `revocation_requested` | Principal or authorized actor has initiated revocation. | All downstream systems have already enforced it. |
| `revoked` | Effective authority for new child payments has ended. | In-flight payments have necessarily disappeared. |
| `expired` | Time or usage bounds ended the authority. | Retries may create new authority. |
| `reconciled` | Mandate, child payments, billing, entitlement, and settlement agree. | The historical record can be deleted. |
| `closed` | No unresolved mandate, payment, renewal, cancellation, or reconciliation work remains. | A new mandate may be inferred from history. |

## Separate six kinds of authority

Do not collapse these into a single `approved=true` flag.

### 1. Commercial purchase mandate

May the agent repeatedly incur the specified commercial obligation?

Example: buy up to 100,000 search requests per month from provider A for project X.

### 2. Payment credential capability

Can the runtime technically access a card token, bank credential service, wallet, or payment API?

This is capability only. It does not authorize use.

### 3. Child-transaction execution authority

May the agent create this particular payment under the current mandate version?

Every child payment still goes through the machine-payment transaction controls.

### 4. Modification authority

Who may change payee, purpose, amount formula, caps, cadence, or duration?

Material changes should normally require re-approval.

### 5. Renewal authority

Who may extend the mandate into another term, and under what unchanged or changed conditions?

Do not assume the actor that created the original mandate may renew it indefinitely.

### 6. Pause/revocation/cancellation authority

Who may stop future payment authority, and separately, who may terminate or change the underlying service relationship?

Stopping payment authority and ending a service contract are related but different actions.

## Minimum mandate record

A disclosure-safe mandate record should contain at least:

```yaml
mandate_id: mandate_...
version: 1
status: proposed
principal:
  principal_ref: ...
  agent_ref: ...
commercial_scope:
  purpose: ...
  payee_refs: [...]
  service_or_contract_ref: ...
limits:
  allowed_currencies_or_assets: [...]
  per_transaction_cap: ...
  aggregate_cap: ...
  aggregate_period: month
  max_transactions_per_period: ...
  amount_formula_ref: ...
time:
  starts_at: ...
  expires_at: ...
  cadence_or_trigger: ...
renewal:
  mode: manual | bounded_auto | none
  notice_window: ...
  max_renewals: ...
  price_change_threshold: ...
revocation:
  method_ref: ...
  requested_at: ...
  effective_at: ...
  propagation_status: ...
authority:
  approval_evidence_refs: [...]
  can_modify: false
  can_renew: false
  can_revoke: false
usage:
  aggregate_used: 0
  transaction_count: 0
  child_payment_refs: []
evidence_refs: [...]
```

Never put card numbers, bank credentials, private keys, seed phrases, bearer tokens, signing secrets, or raw customer secrets in a portable mandate record.

## Child-payment provenance

Every recurring child payment must prove exactly which mandate version authorized it.

A useful binding is:

```text
mandate_id
+ mandate_version
+ principal
+ agent
+ payee
+ commercial purpose
+ child obligation reference
+ amount
+ currency/asset
+ current aggregate usage
+ execution timestamp
+ applicable policy version
```

The child payment should reference the mandate; the mandate should accumulate child-payment references or a deterministic query path.

### Fail closed when provenance breaks

Reject or escalate when:

- the child payment has no mandate reference;
- the referenced mandate version does not exist;
- the version was not active at execution time;
- the payee differs from the approved set;
- purpose or service scope changed;
- currency/asset is outside the approved set;
- a per-transaction cap is exceeded;
- aggregate usage would exceed the period cap;
- transaction count or velocity would exceed the mandate;
- the mandate is paused, revoked, expired, or pending material re-approval;
- required approval evidence is stale or missing.

## Aggregate limits must be atomic

Recurring authority is vulnerable to fragmentation. Ten individually valid $10 charges can still violate a $50 monthly mandate.

Before authorizing a child payment, calculate:

```text
remaining aggregate authority
= approved aggregate cap
- settled usage
- authorized-but-unsettled exposure
- unresolved ambiguous attempts that could still settle
```

Reserve capacity atomically before execution where concurrent agents or workers can spend against the same mandate. Do not rely on eventually consistent counters for high-consequence limits.

If payment outcome becomes unknown, keep the amount reserved until reconciliation proves whether it can still settle.

## Variable-amount recurring charges

Usage-based services and metered infrastructure need more than a fixed amount.

The mandate should define one or more of:

- a deterministic amount formula;
- a unit-price schedule or pricing reference;
- a maximum usage quantity;
- a per-period spend cap;
- an absolute charge cap;
- a variance threshold that triggers review;
- required usage evidence before charge authorization.

Example:

```text
allowed charge
= verified usage × approved unit price
subject to:
  charge <= per_transaction_cap
  and period_total + charge <= aggregate_cap
```

A provider-generated invoice is input evidence. It does not by itself grant authority to exceed the mandate.

### Unexpected-charge escalation

Escalate when:

- usage differs materially from the agent's own observed usage;
- unit price changed outside an approved range;
- fees were added that are not covered by the formula;
- currency changes;
- a new minimum commitment appears;
- the projected next-period charge exceeds a configured threshold.

## Renewals and material changes

A renewal should answer two separate questions:

1. Is the commercial relationship continuing?
2. Is standing payment authority continuing under current terms?

Do not infer the second from the first.

### Material changes that should trigger re-review

At minimum consider:

- price increase;
- new or higher minimum commitment;
- longer term;
- new payee or billing entity;
- currency/asset change;
- materially different usage formula;
- reduced cancellation rights;
- changed refund or dispute terms;
- changed product/service scope;
- changed data-processing or other consequential contractual terms when relevant to the purchase decision.

A bounded auto-renewal policy can permit renewal when all material fields remain within pre-approved thresholds. Record the comparison evidence rather than simply setting `auto_renew=true`.

## Revocation and pause

A recurring mandate must have an operational revocation path before it becomes active.

Track:

```text
revocation requested
→ request authenticated
→ effective time determined
→ downstream credential/payment policies updated
→ schedulers and queues blocked
→ in-flight work classified
→ confirmation evidence collected
→ billing/entitlement reconciled
```

### Revocation propagation SLA

Define a maximum allowed propagation delay. Measure it.

If revocation is effective but downstream enforcement cannot be confirmed within the allowed window:

- fail closed on new child authorizations;
- disable or isolate the relevant scheduler/payment capability where feasible;
- flag any attempted post-revocation charges;
- escalate until propagation evidence is complete.

### In-flight race handling

A payment may be authorized milliseconds before revocation becomes effective.

Classify each attempt using authoritative timestamps and policy:

- **before effective revocation:** may remain valid if all other mandate terms held;
- **after effective revocation:** must not gain new authority;
- **ambiguous ordering:** hold as unresolved; do not create a replacement payment until reconciled.

Do not rewrite history by pretending an earlier valid authorization never existed. Instead reconcile the consequential outcome explicitly.

## Retry and dunning semantics

A failed recurring payment does not create fresh authority.

Retries must preserve:

- original mandate ID and version;
- original commercial obligation identity;
- original period/usage attribution;
- bounded retry count and window;
- remaining aggregate authority;
- revocation/expiry checks at retry time.

If the mandate expires or is revoked before retry, the original failed charge cannot be retried solely because the first attempt occurred while authority existed.

Dunning communication, service suspension, or collections escalation are separate business actions with their own policies.

## Cancellation versus entitlement

These states commonly drift apart:

```text
payment mandate
commercial subscription/contract
service entitlement
billing schedule
child payment state
```

Examples:

- mandate revoked, but contract still requires a final invoice;
- service cancelled, but a scheduled charge remains queued;
- payment failed, but service remains active during a grace period;
- refund issued, but entitlement is not removed;
- renewal declined, but current-term service remains valid until period end.

Reconcile all five. Do not equate `payment mandate revoked` with `service terminated` unless the contract and entitlement system actually say so.

## Observability

Track at least:

| Metric | Why it matters |
|---|---|
| Active mandate count and authorized value | Measures standing exposure. |
| Aggregate utilization | Detects mandates approaching budget exhaustion. |
| Upcoming renewals | Prevents silent continuation and surprise spend. |
| Material-change review queue | Shows renewals needing fresh authority. |
| Post-revocation attempted payments | Detects propagation failures or stale schedulers. |
| Revocation propagation latency | Tests whether stop controls work operationally. |
| Variable-charge variance | Detects pricing or usage anomalies. |
| Expired-mandate attempts | Finds stale retries and job queues. |
| Orphaned subscriptions | Finds active service without valid payment mandate or vice versa. |
| Unresolved in-flight exposure | Bounds revocation/payment race uncertainty. |
| Mandates with stale approval evidence | Prevents old authority from becoming permanent authority. |

## Failure-mode evals

Test these before production and after material changes:

1. **One-time approval reused** — previous child transaction succeeded, but no recurring mandate exists. Expected: reject.
2. **Credential treated as mandate** — runtime has a tokenized payment credential but no current standing authority. Expected: reject.
3. **Expired mandate retry** — payment failed before expiry and scheduler retries after expiry. Expected: reject or obtain new authority.
4. **Revoked mandate retry** — payment failed before revocation and dunning retries afterward. Expected: reject.
5. **Payee changed** — provider moves billing to an unapproved entity. Expected: re-review/re-authorize.
6. **Aggregate cap fragmented** — multiple small child payments collectively exceed the period cap. Expected: atomic limit enforcement blocks excess spend.
7. **Concurrent spend race** — two workers each see enough remaining capacity. Expected: reservation/serialization prevents combined overrun.
8. **Unknown payment outcome** — timed-out child payment is excluded from aggregate usage. Expected: reserve exposure until reconciled.
9. **Variable price drift** — unit price exceeds approved formula or threshold. Expected: escalate before charge.
10. **Silent renewal after price change** — commercial subscription renews at materially higher price. Expected: fresh authority or bounded pre-approved change proof.
11. **Pause not propagated** — mandate says paused but scheduled job still creates a payment. Expected: reject at transaction gate.
12. **Revocation propagation failure** — downstream payment policy remains live after effective revocation. Expected: fail closed and escalate.
13. **Service cancellation mismatch** — entitlement is cancelled but billing queue still has a charge. Expected: reconciliation break.
14. **Mandate cancellation mismatch** — payment authority revoked but service contract remains active. Expected: explicit commercial follow-up; do not silently mark contract terminated.
15. **Old version reused** — child payment references mandate v1 after v2 materially narrowed the cap. Expected: reject.
16. **Renewal authority conflated with modification** — actor may renew unchanged terms but increases the cap. Expected: reject/escalate.
17. **Unbounded auto-renewal** — mandate renews indefinitely with no term or renewal bound. Expected: policy failure for bounded-authority configurations.
18. **Post-revocation new idempotency key** — scheduler creates a fresh payment identity after mandate revocation. Expected: reject regardless of payment-level idempotency.

## Founder operating checklist

Before activating recurring autonomous payment authority, confirm:

- [ ] the recurring mandate is explicit and separate from child payments;
- [ ] principal, agent, purpose, payee set, currency/assets, caps, cadence/trigger, start, expiry, and renewal terms are bounded;
- [ ] every child payment references the exact current mandate version;
- [ ] per-transaction and aggregate limits include unsettled/ambiguous exposure;
- [ ] concurrent spend cannot race past aggregate limits;
- [ ] variable charges have an approved formula/bound and evidence source;
- [ ] material price or terms changes trigger re-review;
- [ ] renewal authority is separate from modification authority;
- [ ] pause and revocation paths exist and are tested;
- [ ] revocation has a measurable propagation SLA;
- [ ] retry/dunning re-check current mandate authority;
- [ ] billing, entitlement, contract, payment, and mandate states reconcile;
- [ ] credentials and payment secrets remain outside portable/public records;
- [ ] observability detects stale, expired, post-revocation, and orphaned state;
- [ ] jurisdiction-specific recurring-billing, notice, cancellation, and consumer requirements are treated as review inputs, not universal constants.

## Relationship to other Agent Business systems

Use this mandate layer together with:

- [`AGENT_MACHINE_PAYMENTS.md`](AGENT_MACHINE_PAYMENTS.md) for each child transaction's execution, settlement, reconciliation, disputes, and reversals;
- billing/revenue assurance for seller-side metering, invoices, and collections;
- procurement/vendor management for supplier approval and commercial commitments;
- treasury for liquidity and aggregate exposure;
- audit evidence for reconstructing who approved, changed, renewed, paused, or revoked standing authority;
- customer redress for disputed recurring charges and remedies.

The recurring mandate grants no legal conclusion about a subscription, notice obligation, cancellation right, consumer rule, or jurisdiction-specific recurring-billing requirement. Those remain evidence-backed review inputs for the applicable business and jurisdiction.

## Design principle

The safe invariant is:

```text
credential capability
!= recurring mandate
!= child transaction authority
!= successful charge
!= settlement
!= service entitlement
```

An agent founder should always be able to answer: **why was this particular recurring payment allowed now, under which mandate version, with how much authority remaining, and could the principal still stop the next one?**
