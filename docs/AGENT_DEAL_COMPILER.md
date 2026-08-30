# Agent Deal Compiler

The deal compiler turns compatible commercial primitives into an explainable transaction corridor. It answers **what would have to be true next**. It never answers **you are authorized to do it**.

## Core equation

`buyer intent + seller proposal + compatibility intersection + current authority/evidence -> transaction corridor`

The corridor preserves separate states for qualification, comparison, selection, contract, payment authority, execution, settlement, delivery, acceptance, and dispute/closure. A later state is never inferred from an earlier one.

## Why founders should care

Interoperability is economically useful only when it removes coordination work. The compiler exposes that benefit directly. A highly compatible pair of agents gets more `ready` transitions. A partially compatible pair gets explicit human-reviewed fallbacks. A pair missing required conventions gets blocked rather than conversationally improvising around the gap.

The `coordination_friction` object counts blocked transitions, human reviews, unsupported transitions, and fallbacks. The `minimum_work_to_transact` list converts those gaps into an integration backlog. This creates a measurable adoption target: reduce the transitions and manual handoffs required to reach accepted paid delivery.

## State corridor

1. `qualify` — bind the buyer's request and hard constraints.
2. `compare` — normalize an eligible seller proposal.
3. `select` — record buyer selection separately from a contract.
4. `contract` — bind current commercial truth and terms.
5. `authorize_payment` — prove bounded external authority for the proposed spend.
6. `execute_payment` — execute only under separate transaction controls.
7. `settle` — establish settlement state without calling it delivery.
8. `deliver` — attach execution/delivery evidence.
9. `accept` — evaluate the buyer's acceptance criteria independently of payment.
10. `close_or_dispute` — close only after the economic states reconcile, otherwise preserve a dispute path.

Every transition is one of `ready`, `blocked`, `human_review`, or `unsupported` and always carries `grants_authority: false`.

## Fail-closed contradictions

The compiler blocks downstream transitions when the proposal is not eligible, when no selection exists, or when the buyer's current payment authority does not cover the proposal price. It never treats selection as contract, credentials as authority, settlement as delivery, or payment as acceptance.

## Usage

```bash
python scripts/compile_agent_deal.py RFQ.json PROPOSAL.json BUYER_COMPATIBILITY.json SELLER_COMPATIBILITY.json --output AGENT_DEAL_PLAN.json
```

Exit code `0` means the plan has no blocked transitions. Exit code `3` means the plan was produced but has blockers. Neither exit code authorizes an action.

## Product direction

The compiler can become the bridge between demand exchanges, marketplaces, procurement agents, payment agents, and delivery agents. Protocol adapters can project inputs into the canonical records while the compiler remains transport-neutral.

A future marketplace can rank integrations by *coordination work removed* rather than by vague protocol badges: how many counterparties move from blocked/manual corridors to structured corridors after implementing one missing convention.
