# Transaction-Corridor Liquidity and Integration ROI

Agent Business now has machine RFQs, seller proposals, compatibility handshakes, and a deal compiler. This layer asks the next economic question:

> If an agent implements one missing interoperability capability, how much more qualified market becomes reachable?

This is not a protocol-popularity score. It is a counterfactual analysis over disclosure-safe deal-plan summaries.

## Core metrics

- `reachable_counterparty_rate`: share of corridors with no `blocked` or `unsupported` transition. Human-reviewed fallbacks may still be reachable.
- `structured_corridor_rate`: share with every modeled transition `ready`.
- `manual_handoffs_per_deal`: average `human_review` transitions.
- `blocked_transition_rate`: blocked transitions divided by all modeled transitions.
- `unsupported_transition_rate`: unsupported transitions divided by all modeled transitions.
- `median_minimum_work_items`: median non-ready transitions remaining.

`reachable` never means authorized, contracted, paid, delivered, or accepted.

## Counterfactual unlock analysis

For each missing convention, the analyzer asks what changes if that convention becomes interoperable. It may convert convention-specific `unsupported` or `human_review` transitions to `ready`. A required compatibility blocker may be removed only when the modeled implementation covers that blocker.

The analyzer does **not** convert real authority, eligibility, contractual, or payment-limit blockers into interoperability successes. A corridor blocked because the principal did not authorize the spend stays blocked even if both agents speak the `bounded-authority` convention perfectly.

For every candidate convention the report includes:

- incremental reachable corridors and rate,
- post-change reachable-counterparty rate,
- manual handoffs removed per deal,
- unique corridor IDs unlocked, avoiding double-counting,
- optional qualified-demand value range when the source cohort contains compatible observed/verified commercial evidence.

## Complementarity

Some corridors require two capabilities together. The analyzer tests convention pairs and reports `complementarity_gain_over_best_single` when the pair unlocks more unique corridors than either convention alone.

This matters because agent-market infrastructure is often complementary: payment reconciliation may have little standalone value for a corridor that also lacks execution evidence, while implementing both may unlock it completely.

## Evidence separation

The analyzer keeps these cohorts separate:

- `synthetic_test`
- `self_declared_intent`
- `observed_commercial_demand`
- `verified_commercial_demand`

Synthetic or self-declared activity must never become a willingness-to-pay number. `qualified_demand_value_minor_range` is accepted only for observed or verified commercial cohorts.

Datasets must declare a population definition, selection rule, known exclusions, unique corridor IDs, and `synthetic_separated: true`. These fields make denominator choices visible and reduce cherry-picking risk.

## Freshness and publication

Stale corridor observations are excluded using `--max-age-days`. Each evidence cohort has a minimum sample threshold. Results below the threshold can still be computed for internal debugging but are labeled `publishable: false`.

## Integration ROI

An optional cost model can supply implementation and annual-maintenance cost ranges by convention. When an observed/verified cohort also supplies compatible qualified-demand value ranges in the same currency, the analyzer reports:

- year-one cost range,
- cost per incremental reachable corridor,
- unlocked qualified-demand value range,
- year-one ROI range.

Ranges are deliberate. Do not turn uncertain implementation cost or demand value into fabricated point precision.

## Usage

```bash
python scripts/analyze_corridor_liquidity.py \
  examples/CORRIDOR_LIQUIDITY_SYNTHETIC.json \
  --costs examples/CORRIDOR_INTEGRATION_COSTS_SYNTHETIC.json \
  --as-of 2026-08-30T18:00:00Z
```

The committed example is entirely synthetic. Its cost ranges are test hypotheses, not market facts, and therefore do not produce commercial-demand ROI claims.

## Strategic use

This creates an interoperability demand curve. A founder can rank protocol or integration work by the marginal transaction corridors it plausibly unlocks. A marketplace can identify the conventions causing the most blocked commerce. A protocol maintainer can measure coordination work removed instead of counting badges or SDK installs.

Combined later with demand-exchange analytics, the decision surface becomes:

`unmet qualified demand × corridor blockers × integration cost × evidence quality`

That is a practical map of what the agent economy should build next.
