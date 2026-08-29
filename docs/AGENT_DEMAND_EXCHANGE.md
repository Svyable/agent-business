# Agent Demand Exchange, Buyer Intent, and Machine RFQs

Seller storefronts answer **what can agents sell?** A demand exchange answers the equally important question:

> **What outcomes are buyers actually trying to purchase right now, under what constraints, and with what evidence of willingness to pay?**

This layer turns buyer needs into bounded, comparable machine-readable requests without confusing exploration, synthetic tests, or vague interest with commercial demand.

It complements:

- `docs/AGENT_MARKETPLACE_STOREFRONT.md` — canonical seller-side listings,
- `docs/AGENT_PROCUREMENT_MARKET_DESIGN.md` — sourcing, award, and procurement controls,
- `docs/AGENT_SERVICE_CONTRACTING.md` — contract and acceptance semantics,
- `docs/AGENT_MACHINE_PAYMENTS.md` — payment authority and settlement,
- `docs/AGENT_CAPABILITY_ASSURANCE.md` — evidence-backed seller claims.

A demand request is not a contract, an award is not payment authority, payment is not acceptance, and synthetic demand is not willingness-to-pay.

---

## 1. The demand-side lifecycle

Use explicit states:

```text
draft
  -> published_or_invited
  -> matched
  -> bids_received
  -> shortlisted
  -> awarded
  -> contracted
  -> paid
  -> delivered
  -> accepted | disputed
  -> closed
```

A request can also be cancelled or expired before award.

State must reflect observed commercial progress rather than model confidence.

---

## 2. Classify demand quality before counting it

Every request must declare one evidence class:

| Class | Meaning | May count as verified willingness-to-pay? |
|---|---|---|
| `verified_commercial` | Current buyer authority and spend evidence support a real sourcing event | yes |
| `self_declared_intent` | Buyer says the need is real but authority/budget is not independently evidenced | no |
| `exploratory_research` | Market research, discovery, benchmarking, or category exploration | no |
| `synthetic_test` | Test fixture, demo, eval, load test, or simulated demand | no |

Never aggregate all four into a headline such as “$10M of demand.”

For public statistics, disclose at minimum:

```text
evidence class
sample size
measurement window
compatible category / unit definition
freshness cutoff
```

---

## 3. Canonical demand request

The machine-readable starter is:

```text
templates/AGENT_DEMAND_REQUEST.json
```

The schema is:

```text
schemas/agent-demand-request.schema.json
```

The semantic validator is:

```bash
python scripts/validate_agent_demand.py templates/AGENT_DEMAND_REQUEST.json --allow-draft
```

A demand request should bind:

- stable request ID and version,
- buyer/principal reference,
- demand quality class,
- requested business outcome,
- capability category,
- required inputs and expected outputs,
- quantity or volume range,
- budget range and currency when disclosure is permitted,
- timing, deadline, and recurrence,
- service-level requirements,
- human-review expectations,
- region/data/compliance constraints,
- required protocols or integrations,
- acceptance criteria,
- buyer authority evidence reference,
- maximum authorized spend,
- disclosure tier,
- bid window,
- award method,
- public-data safety flags.

---

## 4. Hard constraints before ranking

Matching should be two-stage.

First determine eligibility:

```text
protocol compatibility
AND region compatibility
AND data/compliance compatibility
AND required service level
AND budget compatibility
AND current seller evidence
AND buyer authority where consequential
```

Only then rank eligible sellers on commercial fit.

Do not let sponsorship, popularity, or a high review score override a hard incompatibility.

Useful ranking inputs after eligibility include:

- price or expected total cost,
- delivery latency,
- capability evidence strength,
- relevant execution history,
- review burden,
- reliability,
- integration friction,
- buyer preference.

Sponsored placement must be visibly separate from matching quality.

---

## 5. Public versus private demand

A public demand surface can create useful market intelligence, but public artifacts must not leak customer-sensitive context.

### Public mode

Publish only what is intentionally disclosure-safe, such as:

- capability category,
- generalized business outcome,
- budget band,
- timing window,
- compatible region band,
- required protocols,
- high-level constraints,
- bid deadline,
- evidence class.

### Private / invite-only mode

Keep the same canonical structure but expose sensitive fields only to authorized participants.

Examples of fields that often belong outside public artifacts:

- buyer identity when confidential,
- customer names,
- proprietary data samples,
- internal architecture,
- private contract text,
- credentials or access tokens,
- unpublished pricing strategy,
- security-sensitive system details.

---

## 6. Buyer authority is independent from marketplace access

The ability to post an RFQ does not prove authority to spend.

For a request that can lead to automatic award or purchase, require current evidence for:

- principal/buyer identity,
- authorized spend ceiling,
- allowed category/purpose,
- effective and expiry times,
- relevant approval or mandate reference.

The maximum autonomous award must never exceed the evidenced spend ceiling.

If buyer authority is absent, expired, disputed, or narrower than the request, fail closed to human review or non-binding discovery.

---

## 7. Budget semantics

Separate three concepts:

```text
observed budget band
maximum authorized spend
final awarded price
```

A public budget band can be intentionally coarse. The authorization limit may be private. The award price can differ from both.

Automatic award requires a bounded authorized amount. A request with no usable budget or spend authority can still collect indicative proposals, but it cannot silently become a purchase.

---

## 8. Seller proposals must expose deviations

The seller-side proposal contract is a follow-up layer. At minimum, every bid should reference:

- demand request ID/version,
- canonical seller listing ID/version,
- proposed price and validity window,
- offered service level,
- delivery assumptions,
- capacity assumptions,
- evidence freshness,
- explicit deviations.

Machine-visible deviations include changes to:

- price,
- scope,
- SLA,
- dependencies,
- protocol/integration,
- payment path,
- acceptance criteria,
- region/data treatment.

A proposal that silently violates a hard requirement is ineligible, not merely lower-ranked.

See backlog issue #149 for the reusable proposal object.

---

## 9. Award semantics

An award means **selection**, not every downstream authority.

Keep separate:

```text
seller selected
commercial terms accepted
contract effective
purchase authority current
payment executed
service delivered
buyer accepted
```

Automatic award should require:

- `verified_commercial` demand,
- current buyer authority,
- explicit maximum autonomous award,
- at least one eligible bid,
- no unresolved hard-constraint deviation,
- explicit award method,
- current seller evidence.

For material or regulated purchases, human approval may remain appropriate even when all machine gates pass.

---

## 10. Demand exchange metrics

A useful demand network measures more than request count.

Track:

```text
time to first qualified bid
qualified bids per verified request
award rate
award-to-contract conversion
contract-to-delivery conversion
accepted-delivery rate
dispute rate
repeat demand by buyer/category
unfilled verified demand
```

Also classify why demand goes unfilled:

- no eligible supply,
- price mismatch,
- service-level mismatch,
- unsupported integration,
- region/data constraint,
- stale seller evidence,
- insufficient buyer authority,
- timeline/capacity mismatch.

That blocked-demand taxonomy is often more useful to founders than raw marketplace traffic.

---

## 11. Unmet-demand index

An unmet-demand index should use only compatible definitions.

For one capability category and measurement window, publish:

- verified request count,
- total or median disclosed budget only when semantically compatible,
- median qualified bids per request,
- median time to first qualified bid,
- unawarded verified request share,
- successful-delivery share,
- repeat-demand rate,
- top blocking constraint classes.

Never combine different currencies, quantity units, service definitions, or evidence classes without explicit normalization.

Do not infer market size from a tiny or self-selected sample.

Issue #148 tracks the founder-facing analytics layer.

---

## 12. Anti-abuse controls

### Fake demand

Do not reward request volume without evidence quality. Synthetic or exploratory requests must remain visibly classified.

### Lead harvesting

Do not expose private buyer contact or customer data merely because a seller wants to bid.

### Sybil bidding

Detect multiple apparently independent bids controlled by the same provider or economic principal where that matters to liquidity statistics.

### Self-dealing

Do not treat a buyer and seller under common control as independent market demand without disclosure.

### Bid spam

Rate-limit or economically constrain low-quality automated proposals. Prefer hard eligibility filters before accepting bids.

### Bait-and-switch RFQs

Material scope changes after bidding require a new version, requalification, and where needed repricing/reapproval.

### Collusive signaling

Avoid public bid mechanics that unnecessarily expose real-time competitor pricing or enable coordination. Competition-law concerns may require qualified review.

---

## 13. Failure-mode evals

The repository validator and tests should reject or flag at least these conditions:

1. published public request contains secrets/private customer data,
2. `synthetic_test` demand is marked as verified commercial,
3. automatic award is enabled without current spend authority,
4. autonomous award ceiling exceeds authorized spend,
5. verified commercial request has no buyer authority evidence,
6. bid deadline precedes request publication/update time,
7. hard requirements are empty for an automatic award,
8. public request exposes confidential disclosure tier,
9. request is awarded without an award method,
10. payment state is treated as acceptance,
11. closed accepted request lacks acceptance criteria,
12. stale/expired authority supports consequential award.

---

## 14. Founder opportunities enabled by the demand layer

A shared demand surface enables businesses beyond a generic marketplace:

- reverse marketplace for agent work,
- qualified-demand feeds,
- vertical RFQ networks,
- bid-management agents,
- buyer-side sourcing agents,
- seller-side response agents,
- demand intelligence subscriptions,
- market-making services that seed supply after repeated verified demand,
- workflow-product discovery based on blocked demand,
- escrow/payment/contract orchestration after award.

The important strategic shift is:

> **Founders can decide what to build from observed buyer demand rather than only from seller-side supply or search traffic.**

---

## 15. Safe operating rule

A demand exchange should preserve the following invariants:

```text
listing != capability proof
request != buyer authority
match != award
award != contract
contract != payment authority
payment != delivery
settlement != acceptance
synthetic activity != market demand
```

If one of those boundaries becomes ambiguous, stop automation and require explicit review.