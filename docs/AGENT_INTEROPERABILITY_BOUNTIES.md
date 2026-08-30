# Demand-Backed Interoperability Bounties

The corridor-liquidity analyzer can identify which missing convention blocks the most qualified commerce. A bounty converts that signal into a bounded public-goods work order:

`qualified blocked demand -> bounded sponsor commitments -> builder award -> objective implementation tests -> measured marginal unlock -> earned payout -> external payment settlement`

The repository coordinates evidence and state. It **never holds funds, moves money, or grants transaction/deployment authority**.

## Five states that must stay separate

A useful bounty has five independent state machines:

1. **Demand evidence** — synthetic test, self-declared intent, observed commercial demand, or verified commercial demand.
2. **Sponsor funding** — pledged, verified, revoked, or expired commitments.
3. **External custody** — none, externally asserted, or externally verified. Repository records never equal escrow.
4. **Builder acceptance** — proposal, award, submission, deterministic test result, and marginal-unlock verification.
5. **Payout** — not earned, earned, external execution pending, settled, or failed.

No state promotes another implicitly. A sponsor pledge is not verified funds. Verified funds are not escrow. Acceptance is not payment. A payment request is not settlement.

## Demand backing

Every bounty binds to a disclosure-safe corridor population and selection rule using stable hashes. Demand evidence keeps the same classes used by transaction-corridor liquidity analysis:

- `synthetic_test`
- `self_declared_intent`
- `observed_commercial_demand`
- `verified_commercial_demand`

Only observed or verified commercial demand may carry a qualified-demand value range. `demand_backed_claim: true` additionally requires current evidence references and a nonzero corridor count. Synthetic fixtures may exercise the mechanism but cannot be marketed as committed commercial demand.

## Funding semantics

Each sponsor commitment declares a bounded amount, currency, state, expiry, and optional verification evidence. The validator derives pledged and verified totals from the sponsor rows.

`repo_custodies_funds` must always be `false`. If an external provider actually holds or escrows funds, that is represented separately with a provider reference and current custody evidence. The repository does not infer custody from a pledge, bank screenshot, API capability, or sponsor statement.

Awarded bounties must have enough **verified sponsor commitments** to cover the payout cap. That still does not mean funds are escrowed or that a future payout is authorized.

## Builder award and frozen acceptance criteria

The target defines:

- convention/capability and semantic version,
- the corridor population and selection-rule hashes,
- minimum incremental reachable corridors,
- an acceptance-criteria hash,
- deterministic test identifiers and commands or evidence procedures.

At award time, the award snapshot must copy the same acceptance-criteria hash. The active acceptance object must retain it. This prevents a record from silently changing the success condition after a builder has been selected.

Acceptance commands are **descriptive artifacts only**. The bounty validator never executes arbitrary commands. Real runners should use a separately controlled allowlist/sandbox.

## Marginal unlock verification

Technical test success alone is insufficient. An accepted demand-backed bounty also compares a pre-implementation and post-implementation corridor-liquidity snapshot using the **same declared population and selection rule**.

The record must confirm the hashes match and show at least the bounty's minimum incremental reachable-corridor threshold. This does not prove the implementation caused unrelated market growth; it only verifies the bounded before/after corridor result for the declared population.

## Anti-gaming rules

- corridor populations and selection rules are fixed before award;
- sponsor and builder related-party relationships must be explicitly disclosed;
- duplicate or overlapping bounties declare an overlap group/policy;
- exclusive incremental-value claims require a disjoint-population policy plus overlap evidence;
- synthetic/self-declared demand cannot become a commercial-value claim;
- revoked/expired commitments do not count as verified funding;
- test pass never becomes payout settlement;
- compatibility or bounty acceptance never grants payment, contract, transaction, or deployment authority.

## Payout semantics

`accepted` means the agreed tests and marginal-unlock verification passed. It may make a payout **earned** under the bounty terms, but the payment remains a separate external economic action.

`external_execution_pending` requires a separate payout-authority reference and payment reference. `settled` additionally requires independent settlement evidence. A machine-payment record is a natural external reference, but its own authority and settlement rules remain authoritative.

## Sponsor economics

A sponsor can compare:

`bounded contribution / incremental qualified corridors plausibly unlocked`

and, only where compatible observed/verified value evidence exists:

`bounded contribution / qualified demand value plausibly unlocked`

These are prioritization signals, not guaranteed returns.

## Builder economics

A builder should compare:

`implementation + maintenance burden`

against:

`bounty payout + future reachable market + reusable capability value`

The bounty can subsidize public-good interoperability that no single counterparty would rationally fund alone.

## Lifecycle

`draft -> open -> awarded -> submitted -> accepted -> closed`

with `cancelled` as an allowed terminal path before settlement.

Recommended gates:

- `open`: target and demand evidence are publication-safe; funding may still be pledged.
- `awarded`: enough verified sponsor commitments cover the payout cap; builder selected; criteria frozen.
- `submitted`: implementation/evidence delivered against the frozen target.
- `accepted`: deterministic tests passed and marginal unlock verified on the declared population.
- `closed`: payout settled externally with independent evidence.

## Validation

```bash
python scripts/validate_interoperability_bounty.py templates/INTEROPERABILITY_BOUNTY.json --allow-draft
```

The starter intentionally fails closed: zero funding, no builder, no external custody, no payout authority, no acceptance, and no claim of commercial demand.

## Strategic loop

With the demand exchange, compatibility handshake, deal compiler, and corridor-liquidity analyzer, the repository can now describe a full market-improvement loop:

`observe blocked commerce -> identify highest-value missing convention -> publish bounded bounty -> build -> test -> verify marginal unlock -> settle externally -> recompute market bottlenecks`

That turns interoperability from a standards discussion into an evidence-backed allocation problem.