# Agent Marketplace Storefronts, Listings & Commercial Conversion

Agent businesses are moving from a world where discovery means "someone found my website" to a world where software buyers can search, compare, qualify, invoke, pay, verify delivery, and repurchase another software agent.

That creates a new founder job:

> **Maintain one canonical commercial truth that machines can safely compare and marketplaces can project without drifting.**

A marketplace listing is not merely marketing copy. For an autonomous buyer it can become an input to a purchase decision. Stale pricing, unsupported protocols, ambiguous service levels, over-broad verification badges, hidden dependencies, or unclear payment semantics can therefore turn a distribution mistake into a transaction mistake.

This playbook treats marketplace listings as versioned commercial operating artifacts.

It complements:

- `docs/AGENT_DISCOVERY_DISTRIBUTION.md` — how capabilities become discoverable,
- `docs/AGENT_CAPABILITY_ASSURANCE.md` — how performance claims become scoped evidence,
- `docs/AGENT_PRICING_PACKAGING_DEAL_DESK.md` — how pricing and commercial authority are governed,
- `docs/AGENT_SERVICE_CONTRACTING.md` — how delivery and acceptance become contractual,
- `docs/AGENT_AUTHORITY_DELEGATION.md` — how buyer and seller authority are bounded,
- `docs/AGENT_MACHINE_PAYMENTS.md` — how machine-speed payment and settlement are controlled.

The storefront layer binds those systems into the commercial object a buyer actually evaluates.

---

## 1. The commercial listing lifecycle

Use an explicit lifecycle rather than treating every uploaded profile as equally trustworthy.

```text
draft
  -> evidence_reviewed
  -> published
  -> listing_discovered
  -> capability_inspected
  -> buyer_qualified
  -> quote_or_checkout_started
  -> paid_transaction
  -> successful_delivery
  -> repeat_purchase
```

Operational states can branch after publication:

```text
published -> suspended -> published
published -> retired
```

A listing should be publishable only when:

- provider identity is explicit,
- the capability is narrow enough to compare,
- inputs and outputs are explicit,
- service levels are explicit,
- dependencies and compliance constraints are visible,
- supported protocols are current and evidenced,
- pricing is reconstructable,
- advertised payment options are current and evidenced,
- material claims are classified and evidenced,
- marketplace verification is scoped to the marketplace that issued it,
- buyer authority and acceptance requirements are explicit,
- privacy-safe public disclosure is confirmed,
- every live marketplace copy represents the current canonical version.

---

## 2. One canonical storefront, many projections

Do not maintain separate commercial truth manually in every directory.

Maintain one canonical record:

```text
canonical listing record
        |
        +--> own website / API catalog
        +--> MCP registry projection
        +--> A2A / Agent Card projection
        +--> cloud marketplace listing
        +--> private enterprise catalog
        +--> vertical agent marketplace
```

Each channel may require a different schema or prose format. The underlying business truth should remain the same.

Canonical fields should include:

- stable listing ID,
- listing version,
- provider identity reference,
- capability ID,
- capability name and summary,
- categories and synonyms,
- inputs and outputs,
- human-review mode,
- regions,
- service-level expectations,
- dependencies,
- compliance constraints,
- protocol/version/endpoint metadata,
- pricing model and currency,
- minimum commitment,
- variable price components,
- advertised payment and settlement options,
- buyer qualification requirements,
- claims and their evidence,
- marketplace projection state,
- conversion event contract,
- public-data safety flags.

Canonical artifacts:

```text
docs/AGENT_MARKETPLACE_STOREFRONT.md
schemas/agent-marketplace-listing.schema.json
templates/AGENT_MARKETPLACE_LISTING.json
scripts/validate_marketplace_listing.py
```

Validate the safe starter:

```bash
python scripts/validate_marketplace_listing.py templates/AGENT_MARKETPLACE_LISTING.json --allow-draft
```

Validate a real publication candidate:

```bash
python scripts/validate_marketplace_listing.py path/to/listing.json
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
fit
+ price
+ service level
+ dependencies
+ evidence
+ authority
+ risk
+ payment path
+ acceptance
```

That makes machine selection substantially safer.

---

## 4. Design metadata for retrieval and purchase

A useful commercial capability record should answer:

1. What business job is performed?
2. What input does the buyer provide?
3. What output is returned?
4. What actions or side effects can occur?
5. Is human review required?
6. Which protocols can invoke it?
7. Which regions apply?
8. What service level should the buyer plan around?
9. Which dependencies must exist first?
10. Which compliance constraints narrow use?
11. What does it cost?
12. Which payment options are actually available?
13. What evidence supports the material claims?
14. What must the buyer prove before purchase?
15. What constitutes successful delivery?

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

For invoice reconciliation:

```text
invoice matching
AP reconciliation
PO matching
three-way match
vendor invoice validation
```

Do not stuff unrelated keywords into the listing. Qualified selection is more valuable than raw impressions.

---

## 5. Service levels belong in the storefront

A buyer planning a multi-agent workflow needs more than a capability name.

Useful service-level fields include:

- availability target,
- p95 latency,
- maximum completion deadline,
- support or escalation window.

Not every seller can promise all four. Unknown is better than invented precision.

For a published listing, however, expose at least one meaningful service-level value so a buyer does not have to infer that the service is instantaneous, always available, or supported 24/7.

Example:

```json
{
  "availability_target": 0.995,
  "p95_latency_seconds": 90,
  "completion_deadline_seconds": 300,
  "support_window": "business-hours escalation"
}
```

A target is not the same as measured historical performance. If you advertise an observed reliability claim, attach evidence through the claim system.

---

## 6. Dependencies and compliance constraints must be visible before purchase

An agent can appear compatible while depending on hidden prerequisites.

Examples of dependencies:

- buyer-provided CRM access,
- a particular accounting system,
- a supported data format,
- a minimum knowledge-base freshness level,
- a customer-managed identity provider,
- a human approver,
- a third-party API that must already be licensed.

Examples of compliance constraints:

- not approved for payment execution,
- no medical diagnosis,
- EU-only data processing configuration required,
- no regulated securities advice,
- no export-controlled data,
- customer must have rights to supplied documents.

These fields improve two things at once:

```text
retrieval precision
+ pre-purchase qualification
```

A marketplace that hides them may generate more clicks but worse conversion and more disputes.

---

## 7. Protocol support is a claim

Advertising A2A, MCP, HTTPS API, or another interface is not a decorative badge.

It is a promise that a buyer can use that interface now.

Every published protocol entry should include:

- protocol type,
- supported version,
- current endpoint,
- current evidence that the endpoint/protocol works.

Useful evidence includes:

- public protocol probe,
- conformance test,
- live capability descriptor,
- reachable metadata endpoint,
- versioned API documentation.

### Change rule

If a deployment, domain, authentication method, transport, protocol adapter, or incompatible behavior changes materially:

```text
mark affected evidence stale
-> re-probe
-> update canonical listing
-> increment listing version
-> re-project affected marketplaces
```

Do not advertise protocol support because it worked months ago.

---

## 8. Price must be machine-reconstructable

A listing that says "starting at $5" while hiding a $500 minimum is not machine-readable pricing.

Represent separately:

- pricing model,
- currency,
- headline pricing description,
- minimum commitment,
- usage or outcome unit,
- variable components,
- current commercial terms reference.

Examples:

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

Use `quote` when the price genuinely requires scope review. State the variables that drive the quote instead of inventing false precision.

---

## 9. Payment options are capabilities, not authority

If the listing advertises a card rail, bank transfer, marketplace balance, stablecoin rail, machine-payment protocol, or another settlement option, treat that as a current capability claim.

A payment option should state:

- rail,
- asset or currency,
- settlement semantics,
- current evidence that the option is available.

Example:

```json
{
  "id": "marketplace-card",
  "rail": "marketplace-card-settlement",
  "asset_or_currency": "USD",
  "settlement_semantics": "Marketplace charges buyer and settles under current payout terms; settlement is not service acceptance.",
  "evidence_ids": ["payment-capability-2026-08"]
}
```

Keep these concepts separate:

```text
commercial offer
purchase authority
payment capability
payment execution
settlement
service delivery
acceptance
remedy / dispute
```

A wallet balance, card credential, payment token, or connected rail does not prove that the buying agent is authorized to spend.

Likewise, successful settlement does not prove that the promised service outcome was delivered or accepted.

---

## 10. Buyer qualification should precede consequential purchase

An autonomous buyer should not turn "I found a listing" into an irreversible purchase without satisfying the seller's commercial gate.

A buyer qualification contract should answer:

- What deliverable is requested?
- What acceptance criteria apply?
- What deadline applies?
- What budget is authorized?
- Which principal authorized the buyer?
- Is automatic purchase allowed?
- What is the maximum autonomous purchase amount?
- What customer data will be sent?
- What restrictions apply to that data?
- What regions or jurisdictions matter?
- What escalation path exists?

### Automatic purchase

If `automatic_purchase_allowed` is true, require at minimum:

- proof of buyer authority,
- explicit acceptance criteria,
- a positive bounded purchase cap.

For a paid published listing, automatic purchase should also require at least one currently evidenced payment option.

The repository validator enforces these boundaries.

Do not infer authority from:

- wallet balance,
- prior purchase history,
- marketplace account ownership,
- possession of a payment credential,
- a previous contract,
- a successful trial.

---

## 11. Verification must stay inside its scope

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
- repository ownership was linked,
- legal entity documents were reviewed,
- an endpoint responded,
- a package passed malware scanning,
- an internal marketplace policy check passed.

Those are different claims.

Never convert:

```text
Marketplace A: verified publisher
```

into:

```text
universally verified agent
```

The canonical record attaches badge evidence to the exact marketplace and requires a plain-language scope.

```json
{
  "name": "Verified publisher",
  "scope": "Marketplace publisher-control check only",
  "evidence_ids": ["marketplace-verification-2026-08"]
}
```

The validator rejects badge evidence issued by another marketplace.

---

## 12. Keep claim classes explicit

Every material public claim should be classified.

### `self_asserted`

The provider says it is true.

### `platform_verified`

A named marketplace verified something under its own process. Always record which marketplace.

### `customer_signal`

A customer review, repeat purchase, or other customer-originated signal. One review is not representative performance.

### `benchmark_evidence`

A claim supported by a benchmark or evaluation artifact. Preserve workload scope, version, and freshness.

### `editorial_interpretation`

A conclusion or explanation made by the provider/editor. It may explain evidence but should not masquerade as observed fact.

Published non-editorial claims should always reference current evidence.

---

## 13. Ratings and reviews are not ground truth

Reputation systems can be manipulated through:

- self-dealing purchases,
- Sybil identities,
- reciprocal reviews,
- incentivized ratings,
- wash transactions,
- selective review requests,
- review brigading,
- transaction splitting,
- fake usage volume.

Treat reputation as a weighted signal rather than a universal score.

A stronger buyer model combines:

```text
provider identity confidence
+ protocol reachability
+ benchmark evidence
+ successful-delivery receipts
+ dispute history
+ customer signals
+ evidence freshness
```

No single badge should dominate all of those dimensions.

---

## 14. Projection drift is a revenue and trust bug

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
- changed service levels,
- new dependencies,
- changed compliance constraints,
- removed integrations,
- new human-review requirements,
- changed payment rails,
- updated terms,
- expired evidence,
- suspended capabilities.

Every published marketplace copy should record:

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

The validator rejects a published marketplace copy when its projected version differs from the canonical version or its sync predates the canonical update.

---

## 15. Build adapters, not duplicate truth

When multiple marketplaces matter, write small projection adapters.

```text
canonical JSON
  -> A2A / Agent Card fields
  -> MCP registry/package metadata
  -> cloud marketplace form/export
  -> vertical marketplace API
  -> public website structured data
```

Adapters may omit unsupported fields.

They should not invent new commercial truth.

If a marketplace requires a field the canonical record lacks:

1. decide whether it is channel-specific or universally useful,
2. if universally useful, extend the canonical contract,
3. if channel-specific, keep it in projection metadata,
4. preserve evidence and freshness.

---

## 16. Optimize for verified paid delivery

Listing impressions are not the business outcome.

Track the full funnel:

```text
listing_discovered
  -> capability_inspected
  -> buyer_qualified
  -> quote_or_checkout_started
  -> paid_transaction
  -> successful_delivery
  -> repeat_purchase
```

Useful rates:

```text
inspection_rate
= capability_inspected / listing_discovered

qualification_rate
= buyer_qualified / capability_inspected

paid_conversion
= paid_transaction / buyer_qualified

delivery_success
= successful_delivery / paid_transaction

repeat_rate
= repeat_purchase / successful_delivery
```

### Diagnose the leak

High discovery, low inspection:

- poor title/category fit,
- vague capability,
- weak search positioning.

High inspection, low qualification:

- wrong buyer segment,
- hidden dependency becoming visible late,
- region/data/compliance incompatibility,
- excessive authority requirements.

High qualification, low purchase:

- pricing friction,
- missing trust evidence,
- unclear terms,
- weak payment options,
- checkout friction.

High purchase, low successful delivery:

- reliability problem,
- acceptance mismatch,
- service-level overclaim,
- dependency failure.

High delivery, low repeat:

- weak ROI,
- poor recurring fit,
- support friction,
- price/value mismatch.

---

## 17. Attribute economics by marketplace

For every channel, track:

- listing discoveries,
- qualified buyers,
- paid transactions,
- successful deliveries,
- repeat purchases,
- gross revenue,
- marketplace fees,
- payment fees,
- refunds and credits,
- variable delivery cost,
- channel-specific support burden.

Then calculate:

```text
channel_contribution_margin
= channel_revenue
- marketplace_fees
- payment_fees
- variable_delivery_cost
- refunds_and_credits
- channel_specific_support_cost
```

A marketplace with many views can be worse than a small directory that sends repeat buyers with low support burden.

A useful top-level metric is:

```text
marketplace_contribution_per_qualified_buyer
= channel_contribution_margin / qualified_buyers
```

Pair it with delivery success and repeat purchase rate.

---

## 18. Treat marketplace terms as dependencies

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

## 19. Marketplace portability is strategic leverage

A founder who can only sell through one marketplace has channel concentration risk.

Portability improves when the business owns:

- canonical identity,
- capability metadata,
- pricing truth,
- service-level definitions,
- dependency/compliance definitions,
- evidence,
- benchmark records,
- customer references it is authorized to use,
- service-contract definitions,
- payment reconciliation,
- transaction and acceptance receipts,
- customer relationship where permitted.

Marketplace-specific ratings may not be portable.

The underlying evidence should be.

---

## 20. Marketplace launch checklist

### Capability

- [ ] one narrow buyer job,
- [ ] stable capability ID,
- [ ] concrete input/output contract,
- [ ] human-review mode explicit,
- [ ] regions explicit,
- [ ] service levels explicit,
- [ ] dependencies explicit,
- [ ] compliance constraints explicit.

### Protocols

- [ ] supported protocol/version listed,
- [ ] endpoint reachable,
- [ ] current protocol evidence attached,
- [ ] authentication requirements documented without public secrets.

### Pricing and payment

- [ ] pricing model explicit,
- [ ] currency explicit for paid offers,
- [ ] minimum commitment explicit, including zero,
- [ ] variable components reconstructable,
- [ ] current terms reference,
- [ ] every advertised payment option has current capability evidence,
- [ ] settlement semantics do not imply delivery acceptance.

### Claims

- [ ] every material claim classified,
- [ ] every non-editorial claim evidenced,
- [ ] expiry/freshness defined where appropriate,
- [ ] benchmark scope preserved,
- [ ] marketplace badges remain platform-scoped.

### Buyer gate

- [ ] authority proof requirement explicit,
- [ ] acceptance criteria rule explicit,
- [ ] autonomous purchase cap explicit if enabled,
- [ ] paid automatic checkout has an evidenced payment path,
- [ ] data constraints explicit.

### Projection

- [ ] canonical listing version incremented after material change,
- [ ] each live marketplace copy updated,
- [ ] sync timestamps recorded,
- [ ] listing URLs recorded,
- [ ] badges scoped to their platform evidence.

### Conversion

- [ ] discovery event,
- [ ] inspection event,
- [ ] qualification event,
- [ ] quote/checkout event,
- [ ] payment event,
- [ ] successful-delivery event,
- [ ] repeat-purchase event.

---

## 21. Failure-mode evals

Test these before depending on marketplace distribution.

### Stale capability evidence

Change a material dependency without refreshing a public claim.

Expected: publication/republication blocked.

### Unsupported protocol advertised

Advertise A2A/MCP/API support without current evidence.

Expected: published record rejected.

### Payment rail advertised from memory

List a payment rail whose capability evidence is stale or missing.

Expected: published payment option rejected.

### Price changed without marketplace sync

Increment canonical version after changing price while one marketplace remains on the prior version.

Expected: stale projection rejected.

### Service level omitted

Publish a listing with no meaningful service-level value.

Expected: publication rejected.

### Verification badge universalized

Attach a marketplace badge using evidence from another marketplace.

Expected: badge rejected.

### Benchmark cherry-pick

Publish a performance claim with expired or stale benchmark evidence.

Expected: claim rejected.

### Buyer lacks purchase authority

Enable automatic purchase without authority proof.

Expected: automatic purchase rejected.

### No acceptance criteria

Enable automatic purchase without acceptance criteria.

Expected: automatic purchase rejected.

### Paid auto-purchase without payment path

Enable paid automatic purchase while advertising no evidenced payment option.

Expected: automatic purchase rejected.

### Settlement treated as service proof

Mark a paid transaction as successful delivery without delivery/acceptance evidence in downstream systems.

Expected: funnel stops at `paid_transaction`.

### Expired marketplace verification

Let badge evidence expire while the badge remains public.

Expected: published listing fails until refreshed or badge removed.

### Sync before canonical update

Record a marketplace sync timestamp older than the canonical listing update.

Expected: projection rejected as stale.

### Sensitive data placed in listing

Attempt to store API keys, credentials, private prompts, customer secrets, or payment credentials.

Expected: validation fails closed.

---

## 22. Operating cadence

### On every material capability change

Review:

- listing version,
- service levels,
- dependencies,
- compliance constraints,
- protocol evidence,
- pricing,
- payment options,
- claims,
- regions,
- human-review mode,
- terms,
- marketplace projections.

### Weekly for active channels

Review:

- endpoint reachability,
- evidence expiry,
- listing status,
- verification status,
- payment capability,
- conversion funnel,
- disputes/refunds,
- channel profitability.

### Monthly

Ask:

- Which marketplace creates the most successful paid deliveries?
- Which creates the highest contribution margin?
- Which creates support burden without durable revenue?
- Which listing attracts the wrong buyers?
- Which claims improve qualified conversion?
- Which capability should split into a narrower listing?
- Which channel should be exited?

---

## 23. New businesses created by this layer

The storefront contract creates opportunities beyond listing your own agent.

### Listing synchronization

Maintain one canonical commercial record and project it into many marketplaces.

Charge for:

- adapter maintenance,
- change propagation,
- drift detection,
- publication automation.

### Evidence freshness monitoring

Detect:

- dead endpoints,
- expired claims,
- changed prices,
- changed service levels,
- stale payment rails,
- changed marketplace terms,
- stale badges,
- benchmark expiry.

### Agent marketplace analytics

Measure:

```text
discovery -> qualified buyer -> paid -> delivered -> repeat
```

instead of vanity impressions.

### Reputation normalization

Convert incompatible marketplace signals into a transparent evidence graph without pretending platform scores are equivalent.

### Buyer qualification infrastructure

Help seller agents determine whether an inbound buyer has:

- real authority,
- budget,
- acceptable task scope,
- acceptance criteria,
- compatible data constraints,
- a supported payment path.

### Channel routing

Route a capability toward the marketplace with the strongest expected contribution margin for a buyer class, within marketplace rules and without manipulating rankings or identities.

### Machine-readable commercial catalogs

A seller with dozens or hundreds of narrow capabilities may need a catalog service publishing:

- current capability metadata,
- service levels,
- dependencies,
- compliance constraints,
- pricing,
- evidence,
- availability,
- protocol endpoints,
- payment options,
- purchasing constraints.

That can become infrastructure for autonomous procurement.

---

## 24. The founder metric that matters

Do not optimize for:

```text
number_of_marketplaces_listed
```

Optimize for:

```text
profitable_successful_deliveries_from_qualified_buyers
```

Track it alongside:

```text
successful_delivery_rate
repeat_purchase_rate
channel_contribution_margin
claim_freshness
protocol_freshness
payment_capability_freshness
projection_freshness
```

The best marketplace strategy is not maximum visibility.

It is **trusted discoverability that converts into repeatable profitable delivery without losing commercial truth across channels**.
