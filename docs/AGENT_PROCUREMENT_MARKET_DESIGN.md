# Agent Procurement, Negotiation & Market Design

Autonomous agents are becoming buyers as well as sellers. That changes procurement from a human workflow with machine assistance into a machine-executable market process: discover suppliers, request structured offers, filter by hard constraints, negotiate within delegated authority, award work, verify delivery, pay, and update supplier reputation.

The objective is **not** to make agents buy faster at any cost. The objective is to let agents make bounded, auditable purchasing decisions that improve total cost of outcome without violating authority, quality, safety, legal, or data-governance constraints.

This playbook is for founders building buyer agents, seller agents, procurement infrastructure, agent marketplaces, or businesses that expect autonomous agents to become customers.

---

## 1. The procurement loop

Use this lifecycle:

```text
Need -> Policy -> Discover -> RFQ -> Filter -> Rank -> Negotiate -> Approve -> Award -> Verify -> Settle -> Learn
  ^                                                                                                      |
  +------------------------------------------- repeat ----------------------------------------------------+
```

A robust system treats each stage as a separate control boundary.

1. **Need:** define the outcome, quantity, timing, and acceptance criteria.
2. **Policy:** load budget, authority, compliance, data, security, and counterparty constraints.
3. **Discover:** find candidate suppliers or agents.
4. **RFQ:** send a machine-readable request for quote/proposal.
5. **Filter:** reject candidates that fail hard eligibility requirements.
6. **Rank:** compare eligible offers using outcome-adjusted utility.
7. **Negotiate:** exchange bounded concessions within delegated limits.
8. **Approve:** escalate when value, risk, novelty, or authority requires a human or parent agent.
9. **Award:** create a signed order/contract with explicit deliverables.
10. **Verify:** test whether delivery satisfies the acceptance policy.
11. **Settle:** pay, refund, release escrow, or dispute based on verified state.
12. **Learn:** update supplier performance, pricing benchmarks, and procurement policy.

Do not collapse this into one LLM prompt. Deterministic policy gates should sit between stages.

---

## 2. Start with build vs buy vs delegate

Before sourcing, decide whether procurement is even the right answer.

| Option | Best when | Main risk |
|---|---|---|
| Build internally | capability is strategic, frequent, differentiating | fixed cost and maintenance |
| Buy a product/API | requirement is standardized and vendor market is mature | lock-in and recurring spend |
| Delegate to specialist agent | task is variable but outcome can be specified and verified | coordination and quality risk |
| Broker through marketplace | discovery/comparison cost is high | marketplace fees and platform dependence |

A simple decision score can include:

```text
expected_internal_cost
+ maintenance_cost
+ opportunity_cost
vs.
external_price
+ integration_cost
+ switching_cost
+ expected_failure_cost
+ risk_premium
```

Procure only when the external option wins on **expected total cost of successful outcome**, not just invoice price.

---

## 3. Define the buying mandate before agents negotiate

Every autonomous buyer needs a machine-enforceable mandate.

Minimum fields:

```json
{
  "principal": "org_123",
  "agent_id": "buyer_agent_7",
  "scope": ["rfq:create", "bid:compare", "deal:negotiate"],
  "category": "web_research",
  "max_unit_price": 0.20,
  "max_transaction": 500,
  "max_daily_spend": 2000,
  "allowed_regions": ["US", "EU"],
  "required_data_terms": ["no_training", "delete_30d"],
  "min_reputation": 0.92,
  "approval_threshold": 250,
  "expires_at": "2026-09-30T23:59:59Z"
}
```

The mandate should answer:

- what the agent may source,
- which counterparties are eligible,
- which terms are non-negotiable,
- what price and spend limits apply,
- what concessions are allowed,
- when human approval is required,
- how long authority lasts,
- how authority can be revoked.

A negotiation engine must never be able to reinterpret these hard limits as suggestions.

---

## 4. Separate hard constraints from ranking criteria

Procurement fails when a high-scoring cheap offer is allowed to outrank a mandatory requirement.

### Hard constraints

Use deterministic rejection for requirements such as:

- seller is on allowlist,
- identity or business verification passed,
- minimum reputation threshold,
- acceptable jurisdiction,
- security certification requirement,
- data residency requirement,
- prohibited data-use terms,
- required SLA floor,
- budget ceiling,
- sanctions/export restrictions,
- required license or professional qualification,
- required insurance,
- prohibited subcontracting,
- delivery deadline.

If a candidate fails one hard requirement, do not include it in utility ranking.

### Soft criteria

Rank only after eligibility passes. Example weighted utility:

```text
utility =
  0.30 * quality_score
+ 0.20 * success_probability
+ 0.15 * normalized_price
+ 0.10 * latency_score
+ 0.10 * reliability_score
+ 0.05 * support_score
+ 0.05 * switching_score
+ 0.05 * strategic_fit
```

Weights should reflect the principal's actual economics rather than a generic marketplace default.

---

## 5. Use machine-readable RFQs

PDFs and free-form email are poor interfaces for autonomous procurement. A buyer agent should express requirements in a structured RFQ.

Example:

```json
{
  "rfq_id": "rfq_2026_00421",
  "buyer": "did:example:buyer-17",
  "capability": "company_research",
  "volume": {
    "unit": "company",
    "expected": 10000,
    "period": "month"
  },
  "inputs": {
    "domains": true,
    "company_names": true
  },
  "required_outputs": [
    "employee_count",
    "industry",
    "funding_stage",
    "source_urls"
  ],
  "acceptance": {
    "field_accuracy_min": 0.95,
    "freshness_days_max": 30,
    "source_required": true
  },
  "service": {
    "p95_latency_ms_max": 5000,
    "availability_min": 0.995
  },
  "commercial": {
    "currency": "USD",
    "billing": "per_successful_record",
    "max_unit_price": 0.12
  },
  "data_policy": {
    "training_allowed": false,
    "retention_days_max": 30,
    "regions": ["US", "EU"]
  },
  "quote_expires_at": "2026-08-28T18:00:00Z"
}
```

Good RFQs make seller responses comparable and reduce negotiation ambiguity.

---

## 6. Standardize bid schemas

A bid should be more than a price.

Include:

- supplier identity,
- capability/version,
- unit price and volume tiers,
- minimum commitment,
- capacity,
- delivery time,
- SLA,
- quality metric commitments,
- support level,
- data handling terms,
- geographic constraints,
- dependencies/subprocessors,
- quote expiry,
- refund/service-credit policy,
- proof or benchmark references,
- seller signature.

Example:

```json
{
  "bid_id": "bid_8821",
  "rfq_id": "rfq_2026_00421",
  "seller": "did:example:seller-99",
  "price": {
    "unit": 0.105,
    "currency": "USD",
    "tiers": [
      {"min": 10000, "unit": 0.105},
      {"min": 50000, "unit": 0.085}
    ]
  },
  "sla": {
    "availability": 0.999,
    "p95_latency_ms": 2500
  },
  "quality": {
    "field_accuracy": 0.965
  },
  "capacity": 100000,
  "data_terms": {
    "training": false,
    "retention_days": 7,
    "regions": ["US", "EU"]
  },
  "valid_until": "2026-08-28T16:00:00Z"
}
```

The schema should expose every term that affects expected outcome cost.

---

## 7. Compare total cost of outcome

Do not optimize procurement for nominal price.

A useful model:

```text
expected_cost_per_success =
  purchase_price
+ integration_cost_per_unit
+ verification_cost_per_unit
+ expected_retry_cost
+ expected_failure_loss
+ expected_support_cost
+ switching_amortization
+ risk_adjustment
```

Then compare:

```text
expected_value_per_success - expected_cost_per_success
```

A $0.08 provider with 15% failure may be economically worse than a $0.11 provider with 1% failure.

Track realized economics after award so the buyer learns from actual delivery rather than quoted terms.

---

## 8. Negotiation should be policy-driven, not improvisational

LLM negotiation is useful for exploring multi-dimensional trades, but the authority envelope must be deterministic.

For each negotiable term define:

- ideal value,
- reservation value,
- absolute boundary,
- concession step,
- maximum cumulative concession,
- tradeable relationships between terms.

Example:

```yaml
price:
  target: 0.085
  reservation: 0.110
  never_above: 0.120
term_months:
  target: 12
  max: 24
availability:
  target: 0.999
  minimum: 0.995
data_retention_days:
  target: 0
  maximum: 30
  negotiable: false
```

An agent can decide *how* to bargain within the envelope. It cannot change the envelope.

---

## 9. Use BATNA-aware negotiation

The buyer should know its Best Alternative to a Negotiated Agreement before bargaining.

Examples:

- second-best supplier,
- internal execution,
- existing contract renewal,
- delayed purchase,
- alternative capability,
- no purchase.

Define the reservation utility from the BATNA.

```text
accept deal only if:
expected_deal_utility > expected_BATNA_utility + switching_margin
```

This avoids an agent optimizing for “deal closed” rather than “good deal.”

Do not reward negotiation agents on closure rate alone.

Better metrics:

- realized savings vs benchmark,
- utility captured vs BATNA,
- quality-adjusted cost,
- policy violation rate,
- negotiation cycle time,
- post-award dispute rate.

---

## 10. Multi-dimensional negotiation beats price-only bargaining

Useful trade dimensions include:

- unit price,
- volume commitment,
- term length,
- latency,
- uptime,
- support response time,
- data retention,
- geographic residency,
- cancellation rights,
- credits/refunds,
- payment timing,
- exclusivity,
- usage minimums,
- delivery window.

Example exchange:

```text
Buyer: lower unit price if annual volume exceeds 2M requests.
Seller: accepts price reduction if term extends to 18 months.
Buyer: accepts 18 months only if cancellation right applies after two SLA breaches.
Seller: accepts with a 99.9% uptime commitment.
```

This can create surplus that fixed-list pricing leaves unrealized.

---

## 11. Choose the market mechanism deliberately

Different categories need different market structures.

### Fixed-price catalog

Best for:

- standardized low-value services,
- frequent purchases,
- transparent commodity pricing.

### RFQ / competitive bid

Best for:

- several qualified suppliers,
- moderately customized terms,
- purchases where comparison matters.

### Reverse auction

Suppliers compete downward or on multi-dimensional utility.

Best for:

- standardized requirements,
- sufficient supplier liquidity,
- categories where dynamic price discovery creates value.

Do not use when quality is hard to verify or suppliers can cheaply misrepresent capability.

### Broker / procurement agent

A specialist intermediary sources and ranks sellers.

Best for:

- fragmented markets,
- high discovery cost,
- recurring purchasing needs.

### Multi-source award

Split volume across suppliers.

Best for:

- resilience,
- capacity limits,
- avoiding supplier concentration,
- keeping competitive pricing pressure.

---

## 12. Design auctions against gaming

Autonomous markets can amplify manipulation at machine speed.

Threats include:

- fake bids to create false market depth,
- Sybil suppliers,
- bid shading designed to exploit predictable buyer agents,
- last-millisecond bid manipulation,
- seller collusion,
- buyer collusion,
- self-dealing through related identities,
- front-running purchase intent,
- wash transactions to inflate reputation,
- fake capacity claims,
- spoofed benchmark evidence.

Controls:

- verified identities,
- beneficial-owner or relationship disclosure where applicable,
- bid bonds/stakes for high-risk markets,
- signed bids,
- immutable timestamps,
- randomized tie-breaking,
- minimum bid-validity periods,
- market surveillance,
- anomaly detection,
- graph analysis for related counterparties,
- transaction-history audits,
- penalties for fraudulent delivery,
- independent verification for high-value outcomes.

Never assume transparency alone prevents manipulation.

---

## 13. Reputation should reflect delivered outcomes

A useful supplier reputation model includes:

```text
reputation = f(
  verified_success_rate,
  quality_score,
  SLA_performance,
  dispute_rate,
  refund_rate,
  delivery_timeliness,
  transaction_volume,
  counterparty_diversity,
  evidence_quality,
  recency
)
```

Avoid simple star ratings as the primary signal.

Weight:

- verified transactions over self-reported claims,
- recent outcomes over ancient ones,
- large representative samples over one-off wins,
- comparable-category performance over unrelated activity.

Keep raw evidence available so ranking systems can recalculate reputation for different buyers.

---

## 14. Prevent reputation gaming

Watch for:

- new-account cycling,
- reciprocal review rings,
- self-purchases,
- tiny cheap transactions used to manufacture trust,
- sudden volume spikes,
- correlated reviewers,
- copied evidence,
- identity splitting after poor outcomes.

Possible controls:

- transaction-weighted reputation,
- counterparty diversity requirements,
- identity continuity,
- cost-to-create-trust,
- reputation decay,
- category-specific histories,
- dispute-adjusted scores,
- verified delivery receipts.

High-stakes procurement should never depend on reputation alone.

---

## 15. Keep approval proportional to risk

Not every purchase needs human approval, but not every purchase should auto-close.

Example tiers:

| Tier | Example | Authority |
|---|---|---|
| 0 | $0.02 research API call | auto-buy |
| 1 | $20 recurring tool | auto-buy from allowlisted sellers |
| 2 | $500 workflow contract | agent negotiates, human approves |
| 3 | $25k annual service | legal/security/finance approval |
| 4 | regulated/high-impact vendor | specialist review required |

Escalation triggers can include:

- total commitment,
- new supplier,
- unusual terms,
- sensitive data,
- long contract duration,
- cross-border data transfer,
- high switching cost,
- low confidence in verification,
- reputational risk.

Approval policy belongs outside the negotiating model.

---

## 16. Award with explicit acceptance criteria

A purchase order or agent contract should specify:

- exact capability/version,
- inputs,
- output schema,
- volume,
- price,
- service window,
- quality threshold,
- verification method,
- SLA,
- retry policy,
- refund/credit terms,
- data handling,
- permitted subprocessors,
- dispute process,
- settlement trigger,
- termination rights.

“Provide good results” is not an acceptance criterion.

Where possible use executable tests.

---

## 17. Verification is part of procurement economics

Autonomous buyers need cheap evidence that a seller delivered.

Verification patterns:

- schema validation,
- deterministic tests,
- benchmark subsets,
- randomized sampling,
- cross-provider comparison,
- signed delivery receipts,
- human review for high-risk samples,
- third-party attestation,
- outcome confirmation from downstream systems.

Model verification cost before purchasing.

If a $0.05 output needs $1.00 of human review, the product is not a $0.05 output.

---

## 18. Use escrow and milestone settlement when outcomes are uncertain

For asynchronous or high-value delivery, structure settlement around evidence.

```text
Fund -> Deliver -> Verify -> Release
                  | failure
                  v
             Retry / Refund / Dispute
```

Milestones can reduce risk:

- 20% on accepted plan,
- 40% on intermediate artifact,
- 40% on verified completion.

Rules should specify:

- who controls escrow,
- verification deadline,
- auto-release conditions,
- dispute window,
- allowed evidence,
- refund conditions,
- arbitration/escalation path.

Do not let the same unconstrained model both decide acceptance and release funds.

---

## 19. Make disputes evidence-first

Store an auditable transaction packet:

```text
mandate
+ RFQ
+ bids
+ negotiation transcript
+ policy decisions
+ approvals
+ signed award
+ delivery receipts
+ verification results
+ payment receipts
+ support messages
+ dispute actions
```

A dispute system should be able to answer:

- what was requested,
- what was promised,
- who had authority,
- which version of the terms applied,
- what was delivered,
- how acceptance was measured,
- why payment was released or withheld.

The audit trail is a business asset, not just compliance overhead.

---

## 20. Protect against runaway spend

Autonomous procurement creates a direct path from model output to money movement.

Use deterministic controls:

- per-call cap,
- per-transaction cap,
- per-supplier cap,
- category cap,
- hourly/daily/monthly budget,
- concurrency limit,
- retry budget,
- maximum active negotiations,
- commitment horizon,
- velocity anomaly threshold,
- kill switch.

Example:

```text
if projected_monthly_commitment > remaining_budget:
    DENY
elif new_supplier and transaction_value > 250:
    REQUIRE_APPROVAL
elif spend_velocity > 3x_baseline:
    FREEZE_CATEGORY
else:
    ALLOW
```

Treat retries and duplicate purchases as spend events.

---

## 21. Manage concentration and switching risk

A cheap supplier can become expensive if switching becomes impossible.

Track:

- spend share by supplier,
- percentage of critical workflows on one vendor,
- data/export portability,
- proprietary integration depth,
- replacement lead time,
- migration cost,
- alternate supplier readiness.

Set concentration limits for critical categories.

For example:

```text
no single external model provider > 70% of production inference spend
```

Use multi-source routing when resilience value exceeds coordination cost.

---

## 22. Recurring procurement should continuously re-evaluate

Do not freeze supplier choices forever.

A recurring buyer agent can periodically:

1. measure actual performance,
2. compare current market alternatives,
3. estimate switching cost,
4. request fresh bids,
5. renegotiate current supplier,
6. shift a small test allocation,
7. expand only after successful verification.

This creates continuous procurement rather than annual vendor-selection theater.

Protect against over-switching: transaction costs, learning curves, and instability can erase price savings.

---

## 23. Design marketplace liquidity before monetization

A marketplace is not useful because it has listings. It is useful because qualified buyers can reliably find qualified supply and complete transactions.

Track both sides:

### Buyer liquidity

- active buyers,
- RFQs per buyer,
- repeat purchase rate,
- time to first acceptable bid,
- fill rate.

### Seller liquidity

- active sellers,
- qualified bids per RFQ,
- win-rate distribution,
- utilization,
- seller retention.

### Market health

- median bids per RFQ,
- price dispersion,
- concentration,
- transaction success rate,
- dispute rate,
- time to award,
- time to settlement.

A marketplace with 10,000 listings and zero successful repeat purchases has weak liquidity.

---

## 24. Solve cold start with a narrow wedge

Do not launch as “the marketplace for all agents.”

Pick a category with:

- standardized inputs/outputs,
- repeated demand,
- multiple credible suppliers,
- measurable quality,
- meaningful price dispersion,
- low integration friction.

Good early categories may include:

- web search/research APIs,
- enrichment/data services,
- OCR/document extraction,
- transcription,
- model inference,
- browser automation,
- code execution,
- security scanning,
- identity verification.

Seed supply manually. Bring a few real buyers. Measure completed transactions before expanding categories.

---

## 25. Marketplace monetization models

### Transaction take rate

Charge a percentage of completed GMV.

Best when the marketplace creates discovery, trust, transaction, and dispute value.

### Buyer procurement subscription

Charge buyers for sourcing, negotiation, policy, reporting, or savings automation.

### Seller subscription

Charge for enhanced tooling, analytics, integration, or lead management.

### Verification fee

Charge per independently verified delivery or credential.

### Brokerage / savings share

Charge a percentage of measurable negotiated savings.

Be careful: a pure savings-share incentive can encourage short-term price pressure that damages quality.

### Infrastructure/API fee

Charge for RFQ, bidding, negotiation, escrow, identity, or settlement APIs independent of marketplace ownership.

---

## 26. Strong business opportunities around agent procurement

Potential businesses include:

- autonomous procurement SaaS,
- RFQ and bid protocol infrastructure,
- negotiation engines with deterministic policy controls,
- supplier identity and verification,
- machine-readable contract services,
- agent escrow/dispute infrastructure,
- procurement observability,
- supplier reputation APIs,
- agent marketplace clearinghouses,
- market-surveillance and anti-collusion systems,
- spend-control wallets,
- procurement benchmark data,
- vendor-switching optimization,
- delegated-authority infrastructure,
- agent sourcing brokers.

The durable moat is likely to come from trusted transaction data, integrated policy, verified outcomes, and liquidity—not merely an LLM negotiating interface.

---

## 27. Procurement KPIs

Track at least:

### Economics

- cost per successful outcome,
- savings vs benchmark/BATNA,
- realized vs quoted price,
- verification cost,
- dispute cost,
- switching cost,
- marketplace take rate,
- buyer ROI.

### Quality

- supplier success rate,
- acceptance rate,
- SLA attainment,
- retry rate,
- refund rate,
- dispute rate.

### Speed

- time to first qualified bid,
- negotiation rounds,
- time to award,
- time to verified delivery,
- time to settlement.

### Risk

- policy violation attempts,
- spend anomalies,
- supplier concentration,
- percentage of new counterparties,
- override rate,
- approval escalation rate.

### Market health

- qualified bids per RFQ,
- fill rate,
- repeat buyer rate,
- repeat seller rate,
- price dispersion,
- GMV concentration,
- successful transactions per active participant.

---

## 28. Eval autonomous buyers before real spend

Build scenarios such as:

- cheapest supplier violates data residency,
- seller offers a hidden long-term commitment for a discount,
- quote expires during negotiation,
- supplier reputation drops mid-deal,
- two sellers appear to collude,
- buyer approaches daily budget cap,
- duplicate RFQ creates duplicate award risk,
- seller changes terms after acceptance,
- best bid is above BATNA value,
- seller offers an unauthorized side benefit,
- high-value deal needs approval,
- preferred supplier fails verification.

Measure:

```text
hard_constraint_violation_rate == 0
unauthorized_commitment_rate == 0
duplicate_purchase_rate == 0
budget_breach_rate == 0
```

Then optimize utility and speed.

---

## 29. Minimum viable autonomous procurement system

A founder does not need a full exchange on day one.

Start with:

1. one narrow purchase category,
2. 3–10 known suppliers,
3. a structured RFQ,
4. hard eligibility filters,
5. a transparent utility score,
6. one negotiation policy,
7. human approval above a threshold,
8. deterministic verification,
9. transaction logging,
10. monthly supplier re-evaluation.

This is enough to test whether autonomous procurement creates measurable economic value.

---

## 30. Launch checklist

Before letting an agent spend:

- [ ] buying mandate is explicit and revocable
- [ ] hard constraints are machine-enforced
- [ ] budget ceilings exist at transaction and aggregate levels
- [ ] suppliers have verifiable identities
- [ ] RFQ and bid formats are structured
- [ ] ranking uses total cost of outcome
- [ ] BATNA or reservation utility is known
- [ ] negotiation concessions are bounded
- [ ] approval thresholds are deterministic
- [ ] awards contain explicit acceptance criteria
- [ ] verification is independent from unconstrained generation
- [ ] settlement depends on verified state where appropriate
- [ ] duplicate purchases are prevented
- [ ] disputes have an evidence trail
- [ ] reputation uses verified transaction outcomes
- [ ] concentration risk is measured
- [ ] kill switch and spend freeze work
- [ ] market-abuse monitoring exists for marketplace designs
- [ ] recurring purchases are periodically re-bid or benchmarked

---

## Core principle

**Autonomous procurement should maximize verified outcome value inside a delegated mandate—not maximize transactions, minimize headline price, or close every negotiation.**

The winning procurement systems will combine machine-speed discovery and bargaining with deterministic authority, evidence-backed verification, resilient market design, and auditable settlement.