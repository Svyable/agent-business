# Pooled Agent Demand and Group-Buy Procurement

Pooled demand lets independent buyer agents combine compatible demand into one larger commercial signal without combining their identities, wallets, credentials, contracts, or purchasing authority.

The operating sequence is:

`bounded buyer RFQs -> normalize compatible demand -> collect independently evidenced commitments -> cross threshold -> receive volume-tier seller offer -> buyers independently accept -> deterministic allocation -> compile one deal per buyer -> pay/deliver/accept independently`

The pool is a coordination object. It is not a principal, wallet, purchasing consortium, payment credential, contract, or source of authority.

## Why pool demand

Small buyers often cannot justify a seller's integration cost, minimum volume, dedicated capacity, or best pricing alone. Aggregation can make the same work economically attractive without pretending the buyers are one entity.

Useful cases include:

- several agent founders needing the same data/API integration,
- multiple buyers seeking the same bounded managed outcome,
- a marketplace organizing enough demand to justify a new payment or evidence adapter,
- buyers sharing one setup cost while keeping delivery and payment separate,
- demand that becomes viable only after an interoperability bounty removes a shared blocker.

## Normalize before aggregating

Only pool demand that is comparable on the dimensions that determine delivery and price. The canonical lot records one normalized:

- capability category and measurable business outcome,
- quantity unit and commercial unit,
- currency,
- hard requirements,
- regions and material data constraints,
- service-level boundary,
- acceptance criteria,
- scope hash.

Hard requirements are an intersection, not an average. If one buyer requires a region, evidence class, deadline, or compliance boundary that the normalized lot cannot preserve, split the pool or exclude that contribution. Optional preferences can be aggregated separately and must not silently become hard requirements.

## Buyer contribution contract

Each participant references its own versioned machine RFQ. The pool stores only disclosure-safe coordination fields:

- pseudonymous participant ID,
- RFQ ID, version, and digest,
- demand-evidence class,
- minimum/maximum requested quantity,
- explicit committed quantity,
- maximum acceptable unit price,
- total budget cap,
- commitment validity window,
- opt-in state,
- independent authority state and evidence reference,
- related-party disclosure.

Only `verified_commercial` contributions with current independent authority count toward an activatable commercial threshold. Synthetic, exploratory, or merely self-declared interest can help research a category but cannot be represented as committed commercial volume.

A participant's commitment is bounded. Another buyer leaving the pool never increases that participant's quantity, budget, or authority.

## Threshold mechanics

A pool may require any combination of:

- minimum number of committed buyers,
- minimum committed quantity,
- minimum committed budget.

The record stores the computed values as well as the declared thresholds. A validator recomputes them from eligible participants. This prevents a pool operator from announcing that a threshold is met while counting stale, synthetic, withdrawn, or unauthorized volume.

Threshold met means only that the pool has enough independently evidenced demand to activate the next sourcing step. It does not award a seller or authorize a buyer.

## Seller volume offer

The pooled seller offer binds:

- seller listing/version,
- offer identity and validity,
- capacity ceiling,
- contiguous volume tiers,
- non-increasing unit prices as volume grows,
- fixed setup/integration cost,
- setup-cost allocation method,
- dependencies,
- related-party disclosure.

Volume tiers must be deterministic. The same allocated aggregate quantity must always resolve to the same unit price.

The default starter uses `pro_rata_allocated_quantity` for shared setup cost so fixed integration cost follows actual allocated volume. Other allocation methods should be introduced only with equally explicit semantics.

## Independent buyer opt-in

A selected pooled offer still binds nobody automatically. Each buyer independently accepts or declines the concrete seller offer before allocation.

For an accepted buyer, record:

- accepted-offer timestamp,
- still-current authority,
- committed quantity ceiling,
- budget ceiling,
- later per-buyer deal-plan reference.

Pool selection cannot inherit authority from another buyer, the marketplace, the seller, or an earlier RFQ state.

## Oversubscription and allocation

When accepted demand exceeds seller capacity, allocation must use a declared deterministic rule. The reference contract supports `pro_rata_committed_quantity`:

1. compute each accepted buyer's exact proportional share of capacity,
2. allocate the integer floor,
3. assign remaining units by largest fractional remainder,
4. break exact ties by participant ID.

This is deterministic, reproducible, and fixed before allocation. It prevents post-hoc favoritism.

No allocation may exceed that buyer's accepted committed quantity. A withdrawal cannot silently enlarge anyone else's obligation beyond their own commitment.

## Per-buyer transaction corridor

Final allocation is still not a transaction. Every allocated buyer must compile its own deal and preserve distinct evidence for:

`contract -> payment authority -> payment execution -> settlement -> delivery -> acceptance -> dispute/close`

The pooled record may reference each deal plan, but it cannot authorize payment. The reference contract requires `payment_authorized: false` inside every pool allocation.

## Shared fixed-cost economics

A pool can make an otherwise uneconomic integration viable by spreading setup cost across buyers. Keep the math explicit:

`buyer total = allocated quantity × selected pooled unit price + setup share`

`pool total = sum buyer totals`

Setup shares must add exactly to the seller's declared setup cost. There is no hidden subsidy unless an explicit sponsor or bounty record supplies it.

## Savings attribution

Never compare the pool against an invented list price. A buyer-level savings claim requires comparable evidence such as:

- a prior individual quote,
- a current published seller price for the same scope,
- a current comparable market quote.

The baseline must bind the same scope hash and currency. Savings are:

`comparable baseline total - pooled buyer total`

Negative savings are possible and should remain visible.

## Demand quality and publication

Keep these evidence classes distinct:

- `synthetic_test`
- `exploratory_research`
- `self_declared_intent`
- `verified_commercial`

A public aggregate may publish buyer-count or quantity bands only when disclosure rules and sample thresholds permit. Do not publish private buyer identities, confidential RFQs, credentials, exact hidden budgets, or statistically unsafe slices.

## Anti-gaming controls

Fail closed on:

- one RFQ counted twice inside the same pool,
- synthetic or exploratory volume counted as committed commercial demand,
- quantity above the buyer's original maximum,
- budget or price bounds inconsistent with current authority,
- seller tiers that overlap or create ambiguous prices,
- criteria or allocation rules changed after selection,
- seller capacity exceeded,
- allocation to a buyer that did not accept the offer,
- related-party demand used for market claims without disclosure,
- savings calculated from an incomparable or fabricated baseline,
- pool award treated as contract, payment authority, settlement, delivery, or acceptance.

## Dependency risk

Aggregation can create concentrated supplier exposure. Record whether the selected pool relies on one supplier, the concentration risk, and a substitution/exit plan where material. Better unit economics are not automatically better business economics if the pool creates a fragile dependency.

## Machine assets

- `schemas/pooled-demand-lot.schema.json`
- `templates/POOLED_DEMAND_LOT.json`
- `scripts/validate_pooled_demand.py`
- `tests/test_pooled_demand.py`

Validate the safe starter with:

```bash
python scripts/validate_pooled_demand.py templates/POOLED_DEMAND_LOT.json --allow-draft
```

This is a market-design and operating framework, not legal, competition, procurement, tax, or financial advice. Aggregation does not itself create a partnership, purchasing consortium, agency relationship, shared authority, or shared payment obligation.