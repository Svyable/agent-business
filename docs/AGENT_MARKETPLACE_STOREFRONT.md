# Agent Marketplace Storefronts, Listings & Commercial Conversion

Agent businesses are moving from a world where discovery means "someone found my website" to a world where software buyers can search, compare, qualify, invoke, pay, and repurchase another software agent.

That creates a new founder job:

> **Maintain one canonical commercial truth that machines can safely compare and marketplaces can project without drifting.**

A public listing is not merely marketing copy. For an autonomous buyer it can become an input to a purchase decision.

That means stale price, unsupported protocol metadata, an over-broad verification badge, or an ambiguous acceptance rule can turn a distribution mistake into a transaction mistake.

This playbook treats marketplace listings as versioned commercial operating artifacts.

It complements:

- `docs/AGENT_DISCOVERY_DISTRIBUTION.md` — how capabilities become discoverable,
- `docs/AGENT_CAPABILITY_ASSURANCE.md` — how capability claims become evidence-backed,
- `docs/AGENT_PRICING_PACKAGING.md` when present — how price/package logic is governed,
- `docs/AGENT_SERVICE_CONTRACTING.md` — how delivery and acceptance become contractual,
- `docs/AGENT_AUTHORITY_DELEGATION.md` — how buyer/seller authority is bounded,
- machine-payment and recurring-mandate resources — how payment authority and settlement work.

The marketplace storefront layer binds those systems into the thing a buyer actually sees and acts on.

---

## 1. The commercial listing lifecycle

Use an explicit lifecycle rather than treating every uploaded profile as equally trustworthy.

```text
draft
  -> evidence_reviewed
  -> published
  -> discovered
  -> inspected
  -> buyer_qualified
  -> quote_or_checkout_started
  -> paid_transaction
  -> successful_delivery
  -> repeat_purchase
```

Operational states such as suspension and retirement can occur after publication:

```text
published -> suspended -> published
published -> retired
```

A listing should be publishable only when:

- provider identity is explicit,
- capability scope is narrow enough to compare,
- supported protocols are reachable and evidenced,
- pricing semantics are reconstructable,
- material claims are classified and evidenced,
- marketplace-specific verification is scoped to that marketplace,
- buyer authority and acceptance requirements are explicit,
- privacy-safe public disclosure is confirmed,
- every active marketplace copy represents the current canonical listing version.

---

## 2. One canonical storefront, many projections

Do not maintain separate commercial truth manually in every directory.

Maintain one canonical record:

```text
canonical listing record
        |
        +--> own website / API catalog
        +--> MCP registry metadata
        +--> A2A directory / Agent Card projection
        +--> cloud marketplace listing
        +--> private enterprise catalog
        +--> vertical marketplace
```

The channel may require a different schema or prose format. The underlying business truth should remain the same.

Canonical fields should include:

- stable listing ID,
- listing version,
- provider identity reference,
- capability ID,
- capability name and summary,
- categories and synonyms,
- inputs and outputs,
- human-review mode,
- supported regions,
- protocol/version/endpoint metadata,
- pricing model and currency,
- minimum commitment,
- variable price components,
- buyer qualification requirements,
- claims and their evidence,
- marketplace projection state,
- conversion event contract,
- privacy flags.

The repository starter is:

```text
templates/AGENT_MARKETPLACE_LISTING.json
```

The schema is:

```text
schemas/agent-marketplace-listing.schema.json
```

The semantic validator is:

```bash
python scripts/validate_marketplace_listing.py <record>
```

Validate the safe draft starter with:

```bash
python scripts/validate_marketplace_listing.py templates/AGENT_MARKETPLACE_LISTING.json --allow-draft
```

---

## 3. Sell one job, not an identity

A marketplace buyer usually wants a result, not a personality.

Prefer listings such as:

- reconcile vendor invoices against purchase orders,
- classify inbound support requests and draft responses,
- extract renewal clauses from supplier contracts,
- qualify inbound leads against an ICP,
- verify a public compliance artifact,
- enrich one account with public company data.

Avoid listings such as:

- super agent,
- business copilot,
- intelligent worker,
- autonomous assistant,
- general-purpose AI employee.

Broad identities are difficult to price, benchmark, qualify, accept, and compare.

A narrow capability lets the buyer reason about:

```text
fit + price + latency + evidence + authority + risk + acceptance
```

That makes machine selection possible.

---

## 4. Design capability metadata for retrieval and purchase

A useful commercial capability record should answer:

1. What business job is performed?
2. What input does the buyer provide?
3. What output is returned?
4. What actions or side effects can occur?
5. Is human review required?
6. Which protocols can invoke it?
7. Which regions or constraints apply?
8. What does it cost?
9. What evidence supports the material claims?
10. What must the buyer prove before purchase?
11. What constitutes successful delivery?

### Categories

Use categories that reflect a buyer problem.

Good:

```text
finance-operations
accounts-payable
invoice-reconciliation
```

Weak:

```text
ai
agent
automation
```

### Synonyms

Machines may search for the same job using different language.

For invoice reconciliation, useful synonyms might include:

```text
invoice matching
AP reconciliation
PO matching
three-way match
vendor invoice validation
```

Do not stuff unrelated keywords into the listing. Relevance is more valuable than raw impressions.

---

## 5. Protocol support is a claim

Advertising A2A, MCP, HTTPS API, or another interface is not a decorative badge.

It is a promise that a buyer can use that interface now.

Every published protocol entry should include:

- protocol type,
- supported version,
- current endpoint,
- evidence that the endpoint/protocol works,
- freshness or expiry where appropriate.

Useful evidence includes:

- public protocol probe,
- conformance test,
- live capability descriptor,
- reachable metadata endpoint,
- versioned API documentation.

### Failure rule

If a model, deployment, gateway, domain, authentication method, or protocol adapter changes materially:

```text
mark affected evidence stale
-> re-probe
-> update canonical listing
-> increment listing version
-> re-project affected marketplaces
```

Do not advertise protocol support because it worked six months ago.

---

## 6. Price must be machine-reconstructable

A listing that says "starting at $5" while hiding a $500 monthly commitment is not machine-readable pricing.

Represent separately:

- pricing model,
- currency,
- headline pricing description,
- minimum commitment,
- usage unit,
- variable components,
- platform fees where known,
- taxes where separately determined,
- commercial terms reference.

Examples of pricing models:

### Fixed

```text
$250 per completed report
```

### Usage

```text
$0.35 per invoice
$25 minimum purchase
```

### Subscription

```text
$199/month includes 1,000 tasks
$0.12/additional task
```

### Outcome

```text
$40 per verified qualified meeting
```

### Quote

Use `quote` when the price genuinely requires scope review.

Do not publish fake precision merely to satisfy a schema.

For a quote-based service, say what the quote depends on:

- task volume,
- data volume,
- review requirement,
- risk tier,
- SLA,
- custom integrations,
- deployment model.

---

## 7. Separate price from payment connectivity

A marketplace may show that a provider accepts a payment rail.

That does **not** mean:

- the buyer has authority to spend,
- the seller has accepted the requested scope,
- the transaction terms are current,
- the requested task is permitted,
- successful settlement proves successful delivery.

Keep these concepts separate:

```text
commercial offer
purchase authority
payment execution
settlement
service delivery
acceptance
remedy / dispute
```

A wallet, card, tokenized credential, or payment protocol is a payment capability—not purchase authority.

---

## 8. Buyer qualification should happen before consequential execution

An autonomous buyer should not be able to turn "I found a listing" into an irreversible purchase without satisfying the seller's commercial gate.

A buyer qualification contract should answer:

- What deliverable is requested?
- What acceptance criteria apply?
- What deadline applies?
- What budget is authorized?
- Which principal authorized the buyer?
- Is automatic purchase allowed?
- What is the maximum autonomous purchase amount?
- What customer data will be sent?
- What data restrictions apply?
- What regions/jurisdictions matter?
- What escalation path exists?

### Automatic purchase

If `automatic_purchase_allowed` is true, require at minimum:

- proof of buyer authority,
- explicit acceptance criteria,
- a positive bounded purchase cap.

That is enforced by the repository validator.

Do not infer authority from:

- wallet balance,
- prior purchase history,
- marketplace account ownership,
- possession of a payment credential,
- a previous contract,
- a successful trial.

---

## 9. Verification must stay inside its scope

Marketplaces increasingly attach signals such as:

- verified publisher,
- verified domain,
- reviewed integration,
- security reviewed,
- top seller,
- transaction count,
- rating,
- recommended,
- live endpoint.

These signals are useful only when their scope is preserved.

A marketplace's "verified" badge might mean:

- domain control was verified,
- GitHub ownership was linked,
- legal entity documents were reviewed,
- an endpoint responded,
- a package passed malware scanning,
- an internal marketplace policy check passed.

Those are very different claims.

Never convert:

```text
Marketplace A: verified publisher
```

into:

```text
universally verified agent
```

The canonical record therefore attaches badge evidence to the specific marketplace and records a plain-language scope.

Example:

```json
{
  "name": "Verified publisher",
  "scope": "Marketplace publisher-control check only",
  "evidence_ids": ["marketplace-verification-2026-08"]
}
```

The validator rejects badge evidence that belongs to another marketplace.

---

## 10. Keep claim classes explicit

Every material public claim should be classified.

### `self_asserted`

The provider says it is true.

Example:

```text
The service supports 10,000 records per batch.
```

Self-asserted does not mean false. It means the evidence source is the provider.

### `platform_verified`

A named marketplace verified something under its own process.

Always record which marketplace.

### `customer_signal`

A customer rating, review, repeat purchase, or other customer-originated signal.

Do not present one review as representative performance.

### `benchmark_evidence`

A claim supported by a benchmark or evaluation artifact.

Keep the benchmark scope, version, and freshness intact.

### `editorial_interpretation`

A conclusion or explanation made by the publisher or repository editor.

Editorial interpretation may explain evidence but should not masquerade as observed fact.

---

## 11. Ratings and reviews are not ground truth

Reputation systems can be manipulated.

Potential failure modes include:

- self-dealing purchases,
- Sybil identities,
- reciprocal reviews,
- incentivized ratings,
- wash transactions,
- selective requests for reviews,
- review brigading,
- transaction splitting to increase counts,
- fake usage volume.

Treat reputation as a weighted signal rather than a universal score.

A useful buyer might combine:

```text
provider identity confidence
+ current protocol reachability
+ benchmark evidence
+ verified successful deliveries
+ dispute history
+ customer signals
+ evidence freshness
```

No single badge should dominate all of those dimensions.

---

## 12. Projection drift is a revenue and trust bug

Suppose the canonical service changes from:

```text
$0.20/task
```

to:

```text
$0.35/task
```

but one marketplace still advertises `$0.20/task`.

You now have competing public truths.

The same problem occurs with:

- retired endpoints,
- unsupported regions,
- deprecated models,
- changed SLAs,
- removed integrations,
- new human-review requirements,
- updated terms,
- expired evidence,
- suspended capabilities.

### Projection rule

Every published marketplace copy records:

- canonical listing version projected,
- last sync timestamp,
- listing URL,
- marketplace-specific external ID.

For a canonical update:

```text
increment listing version
-> identify affected marketplace copies
-> update each copy
-> record sync timestamp
-> revalidate
```

The validator rejects a published marketplace copy when its projected version does not equal the current canonical version or when its sync predates the canonical update.

---

## 13. Build adapters, not duplicate truth

When multiple marketplaces matter, write small projection adapters.

Conceptually:

```text
canonical JSON
  -> A2A/Agent Card fields
  -> MCP registry/package metadata
  -> cloud marketplace form/export
  -> vertical marketplace API
  -> public website structured data
```

Adapters may omit unsupported fields.

They should not invent new commercial truth.

If a marketplace requires a field the canonical record lacks:

1. decide whether it is channel-specific or universally useful,
2. if universally useful, extend the canonical record,
3. if channel-specific, keep it in the marketplace projection metadata,
4. preserve evidence and freshness.

---

## 14. Optimize for verified paid delivery

Listing impressions are not the business outcome.

Track the whole funnel:

```text
listing_discovered
  -> capability_inspected
  -> buyer_qualified
  -> quote_or_checkout_started
  -> paid_transaction
  -> successful_delivery
  -> repeat_purchase
```

Useful rates include:

```text
inspection rate
= capability_inspected / listing_discovered

qualification rate
= buyer_qualified / capability_inspected

paid conversion
= paid_transaction / buyer_qualified

delivery success
= successful_delivery / paid_transaction

repeat rate
= repeat_purchase / successful_delivery
```

### What each failure suggests

High discovery, low inspection:

- poor title/category match,
- vague capability,
- weak marketplace positioning.

High inspection, low qualification:

- capability mismatch,
- data/region constraints,
- excessive authority requirements,
- wrong buyer segment.

High qualification, low purchase:

- pricing friction,
- missing trust evidence,
- unclear terms,
- checkout or payment friction.

High purchase, low successful delivery:

- product/reliability problem,
- acceptance mismatch,
- overclaiming.

High delivery, low repeat:

- weak ROI,
- poor retention fit,
- transactional rather than recurring job,
- price/value mismatch.

---

## 15. Attribute conversion by marketplace

A founder should know which distribution surfaces create profitable buyers.

For every channel, track:

- listing discoveries,
- qualified buyers,
- paid transactions,
- successful deliveries,
- repeat purchases,
- gross revenue,
- marketplace fees,
- refunds/credits,
- variable delivery cost,
- contribution margin,
- support burden.

Then calculate:

```text
channel contribution margin
= channel revenue
- marketplace fees
- payment fees
- variable delivery cost
- refunds / credits
- channel-specific support cost
```

A marketplace with many views can be worse than a small directory that sends repeat buyers with low support burden.

---

## 16. Treat marketplace terms as dependencies

A marketplace can change:

- listing requirements,
- fees,
- ranking logic,
- verification rules,
- payment terms,
- prohibited use cases,
- refund/dispute procedures,
- data access,
- API availability,
- identity requirements.

These are dependency changes.

For important channels, record:

- policy/terms source,
- observed date,
- effective date when known,
- affected listing fields,
- action required.

Do not assume one marketplace's rules apply to another.

---

## 17. Marketplace portability is strategic leverage

A founder who can only sell through one marketplace has channel concentration risk.

Portability improves when you own:

- canonical identity,
- capability metadata,
- pricing truth,
- evidence,
- benchmark records,
- customer references you are authorized to use,
- service contract definitions,
- payment reconciliation,
- transaction receipts,
- customer relationship where permitted.

Marketplace-specific ratings may not be portable.

Your underlying evidence should be.

---

## 18. Marketplace launch checklist

Before publishing a commercial capability:

### Capability

- [ ] one narrow buyer job,
- [ ] stable capability ID,
- [ ] concrete input/output contract,
- [ ] clear side effects,
- [ ] human-review mode explicit,
- [ ] regions/constraints explicit.

### Protocols

- [ ] supported protocol/version listed,
- [ ] endpoint reachable,
- [ ] current protocol evidence attached,
- [ ] authentication requirements documented outside public secrets.

### Pricing

- [ ] model explicit,
- [ ] currency explicit for paid offers,
- [ ] minimum commitment explicit, including zero,
- [ ] variable components reconstructable,
- [ ] current terms reference.

### Claims

- [ ] every material claim classified,
- [ ] every non-editorial claim evidenced,
- [ ] expiry/freshness defined where appropriate,
- [ ] benchmark scope preserved,
- [ ] no universalization of marketplace-specific badges.

### Buyer gate

- [ ] authority proof requirement explicit,
- [ ] acceptance criteria rule explicit,
- [ ] autonomous purchase cap explicit if automatic purchase is enabled,
- [ ] data constraints explicit.

### Marketplace projection

- [ ] canonical listing version incremented,
- [ ] each live marketplace copy updated,
- [ ] sync timestamps recorded,
- [ ] listing URLs recorded,
- [ ] badges scoped to platform evidence.

### Conversion

- [ ] discovery event,
- [ ] inspection event,
- [ ] qualification event,
- [ ] quote/checkout event,
- [ ] payment event,
- [ ] successful-delivery event,
- [ ] repeat-purchase event.

---

## 19. Failure-mode evals

Test these before depending on marketplace distribution.

### 1. Stale capability claim

Change a material model/tool dependency without refreshing claim evidence.

Expected:

```text
publication/republication blocked
```

### 2. Unsupported protocol advertised

Mark A2A or MCP as supported without current endpoint evidence.

Expected:

```text
published record rejected
```

### 3. Price changed without marketplace sync

Increment canonical listing version after changing price but leave one marketplace on the prior projected version.

Expected:

```text
stale projection rejected
```

### 4. Verification badge treated as universal trust

Attach a marketplace badge using evidence from a different marketplace or omit its scope.

Expected:

```text
badge rejected
```

### 5. Benchmark cherry-pick

Publish a performance claim with expired, stale, or missing benchmark evidence.

Expected:

```text
claim rejected
```

### 6. Buyer lacks purchase authority

Enable automatic purchase without authority proof.

Expected:

```text
automatic purchase rejected
```

### 7. No acceptance criteria

Enable automatic purchase without requiring acceptance criteria.

Expected:

```text
automatic purchase rejected
```

### 8. Duplicate contradictory profiles

Publish two marketplace copies that claim different canonical versions.

Expected:

```text
outdated projection identified and blocked from current state
```

### 9. Rating manipulation

Feed self-dealing or unverified review data into a universal quality claim.

Expected:

```text
claim remains scoped or is excluded
```

### 10. Settlement treated as service proof

Mark a paid transaction as successful delivery without acceptance evidence.

Expected:

```text
conversion funnel stops at paid_transaction
```

### 11. Expired marketplace verification

Let badge evidence expire while the badge remains public.

Expected:

```text
published listing fails validation until refreshed or badge removed
```

### 12. Marketplace sync before canonical update

Record a marketplace sync timestamp older than the canonical listing update.

Expected:

```text
projection rejected as stale
```

---

## 20. Operating cadence

### On every material capability change

Review:

- listing version,
- protocol evidence,
- pricing,
- claims,
- regions,
- human-review mode,
- terms,
- marketplace projections.

### Weekly for active channels

Review:

- reachability,
- expired/stale evidence,
- listing status,
- verification status,
- conversion funnel,
- disputes/refunds,
- channel profitability.

### Monthly

Ask:

- Which marketplace creates the most successful paid deliveries?
- Which creates the highest contribution margin?
- Which creates support burden without revenue?
- Which listing language attracts the wrong buyers?
- Which claims actually improve qualified conversion?
- Which capability should be split into a narrower listing?
- Which channel should be exited?

---

## 21. Machine-to-machine storefront opportunities

This layer creates businesses beyond simply listing your own agent.

Potential products include:

### Listing synchronization

One canonical capability record projected into many marketplaces.

Charge for:

- adapter maintenance,
- change propagation,
- drift detection,
- publication automation.

### Evidence freshness monitoring

Continuously detect:

- dead endpoints,
- expired claims,
- changed prices,
- changed platform terms,
- stale badges,
- benchmark expiry.

### Agent marketplace analytics

Measure:

```text
discovery -> qualified buyer -> paid -> delivered -> repeat
```

rather than vanity impressions.

### Reputation normalization

Convert incompatible marketplace signals into a transparent evidence graph without pretending scores are equivalent.

### Buyer qualification infrastructure

Help seller agents determine whether an inbound agent has:

- authority,
- budget,
- acceptable task scope,
- acceptance criteria,
- compatible data constraints.

### Marketplace arbitrage / channel routing

Route a capability to the marketplace where the expected contribution margin is strongest for a given buyer class.

Do this transparently and within marketplace rules rather than manipulating rankings or identities.

### Machine-readable commercial catalog infrastructure

A seller with dozens or hundreds of narrow capabilities may need an agent-native catalog service that publishes:

- current capability metadata,
- pricing,
- evidence,
- availability,
- protocol endpoints,
- purchasing constraints.

That can become infrastructure for autonomous procurement.

---

## 22. The founder metric that matters

Do not optimize for:

```text
number of marketplaces listed
```

Optimize for:

```text
profitable successful deliveries from qualified machine buyers
```

A useful top-level measure is:

```text
marketplace contribution per qualified buyer
=
(revenue
 - marketplace fees
 - payment fees
 - variable delivery cost
 - credits/refunds
 - variable support cost)
/
qualified buyers
```

Then pair it with:

```text
successful delivery rate
repeat purchase rate
claim freshness
projection freshness
```

The best marketplace strategy is not maximum visibility.

It is **trusted discoverability that converts into repeatable profitable delivery without losing commercial truth across channels**.
