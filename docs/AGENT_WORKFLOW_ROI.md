# Agentic Workflow ROI and Cost-versus-Value Operating Model

Agent founders should decide whether a workflow deserves autonomy by comparing the **fully loaded cost to complete a customer-visible outcome** with the **value created by that completed outcome**.

Token cost is an input. It is not the business result.

This guide extends [Agent Unit Economics](AGENT_UNIT_ECONOMICS.md) from operating metrics into a reproducible decision system for comparing workflow designs before and after deployment.

## Core question

For the same customer-visible success event:

> Which workflow design creates the highest defensible economic value after model/tool costs, retries, review, support, failures, fixed operations, and implementation investment—subject to quality, safety, authority, and latency constraints?

A cheaper model call can lose this comparison if it creates more retries, review, failures, or customer recovery work.

A more autonomous design can also lose if its lower labor cost comes with a materially worse success rate or larger failure loss.

## Canonical artifacts

- Schema: `schemas/workflow-roi-analysis.schema.json`
- Safe starter: `templates/WORKFLOW_ROI_ANALYSIS.json`
- Validator/calculator: `scripts/workflow_roi.py`
- Founder outcome evidence: `docs/FOUNDER_OUTCOME_CASE_STUDIES.md`
- Unit economics: `docs/AGENT_UNIT_ECONOMICS.md`

Validate the starter:

```bash
python scripts/workflow_roi.py templates/WORKFLOW_ROI_ANALYSIS.json --validate-only
```

Calculate pessimistic, base, and optimistic cases:

```bash
python scripts/workflow_roi.py templates/WORKFLOW_ROI_ANALYSIS.json
```

Machine-readable output:

```bash
python scripts/workflow_roi.py templates/WORKFLOW_ROI_ANALYSIS.json --json
```

The public template is intentionally a `draft`. Its numbers are illustrative assumptions, not ecosystem benchmarks.

## Why this needs a separate operating model

The repository already tells founders to track cost per successful outcome. A real investment decision needs more structure:

1. define the same success event for every alternative,
2. preserve a real baseline rather than comparing an agent to zero cost,
3. separate observed inputs from self-reports, estimates, and external benchmarks,
4. carry ranges instead of one false-precision number,
5. include failure and human-review economics,
6. amortize fixed operating costs over actual outcome volume,
7. include implementation investment when computing first-year ROI,
8. compare incremental payback against the current workflow,
9. preserve non-economic constraints that can invalidate the apparent winner.

The calculator encodes those rules without pretending economics alone can authorize a workflow.

## Evidence before arithmetic

Every numeric input has:

```json
{
  "value": 0.92,
  "low": 0.85,
  "high": 0.96,
  "classification": "observed_fact | self_reported | estimate | benchmark",
  "basis_ids": ["evidence-or-assumption-id"]
}
```

### `observed_fact`

Use only for a measured value whose uncertainty is not being represented inside this field. The validator requires:

```text
low == value == high
```

Sampling uncertainty can still be modeled as an estimate in a separate analysis.

### `self_reported`

Use for a value reported by a founder, customer, operator, or team that the repository cannot independently verify.

### `estimate`

Use for a modeled input based on explicit assumptions.

### `benchmark`

Use for an external comparison value. Record the source and observation date because agent economics change quickly.

## Evidence and assumptions are different

An evidence record represents something observed or published.

An assumption represents something the decision still needs to suppose.

Assumptions must have:

- an owner,
- a reason,
- a revisit trigger.

This turns uncertainty into an operating queue instead of hiding it inside a spreadsheet cell.

Examples of useful revisit triggers:

- after 100 representative production outcomes,
- after the next provider pricing change,
- when review rate exceeds 20%,
- after a material workflow redesign,
- when customer price changes,
- after a new failure class appears.

## 1. Define one customer-visible outcome

Do not compare alternatives using different definitions of success.

Good outcome units:

- resolved support request accepted by the customer,
- qualified sales opportunity meeting a fixed rubric,
- paid invoice reconciled correctly,
- accepted proposal delivered before deadline,
- completed onboarding that passes compliance review,
- claim resolved without avoidable rework,
- code change accepted by the required test/review gate.

Bad outcome units:

- agent turn,
- token,
- tool call,
- generated document,
- workflow invocation,
- “task completed” without an acceptance test.

Those are activity units, not business-value units.

## 2. Preserve the current workflow as the baseline

Every analysis has `baseline_scenario_id`.

The baseline may be:

- entirely manual,
- a legacy automation,
- a deterministic software workflow,
- the current production agent,
- a vendor/service already doing the work.

Do not model the alternative against a fictional zero-cost world.

The calculator reports incremental recurring surplus and incremental payback versus this baseline.

## 3. Model annual opportunity volume

`annual_requested_outcomes` is the number of customer outcomes requested—not the number successfully completed and not the number of model attempts.

Keep volume at a common base when comparing designs unless the design itself changes addressable throughput.

If throughput expansion is part of the thesis, model it explicitly and explain why demand exists for the extra capacity.

Unused automation capacity has no customer value by itself.

## 4. Model probability of success

For each scenario:

```text
expected_successes = requested_outcomes * success_rate
expected_failures = requested_outcomes - expected_successes
```

A higher success rate can justify more expensive inference or review.

A lower success rate can erase apparent savings because failed outcomes consume work while producing no paid result and may create recovery cost.

Use an acceptance rubric stable enough to compare the baseline and alternative.

## 5. Model retries and refinement

`average_attempts_per_request` includes the initial attempt.

It must never be below 1.

```text
expected_attempts = requested_outcomes * average_attempts_per_request
```

Attempt cost includes:

- inference,
- context/retrieval,
- tools/APIs,
- paid data,
- compute/storage,
- other per-attempt spend.

Retry economics matter because an apparently cheap model can become expensive after repeated checking, repair, and re-execution.

Set independent production retry limits. The ROI model is not permission to retry indefinitely.

## 6. Include human review as a first-class cost

Human review is modeled as:

```text
review_cost
= requested_outcomes
* review_rate
* minutes_per_review / 60
* reviewer_hourly_cost
```

Measure the actual reviewer population when possible. Risk/compliance specialists may cost much more than generic labor assumptions.

Also track whether review catches errors. Removing review is only a gain if quality and risk remain acceptable.

A useful experiment changes one of:

- review rate,
- minutes per review,
- reviewer tier,
- automated prechecks,

while keeping the same acceptance outcome.

## 7. Include failure recovery

For a failed request:

```text
failure_recovery_cost
= expected_failures
* recovery_cost_per_failed_request
```

Recovery can include:

- rework,
- refunds/credits,
- customer support,
- specialist intervention,
- incident response,
- compensating transactions,
- manual repair of external state.

For consequential workflows, failure cost can be larger than normal delivery cost.

Do not model regulatory fines or catastrophic tail loss as a casual expected-value input when the correct operating response is to prohibit or escalate the action.

## 8. Include variable support

Some customer or workflow cohorts generate onboarding and exception work outside formal review.

```text
variable_support_cost
= requested_outcomes * support_cost_per_request
```

If support is actually customer-level rather than outcome-level, convert it carefully using observed customer volume or model it in a separate customer profitability analysis.

## 9. Include fixed operating costs

The schema separates annual fixed costs into:

- infrastructure,
- orchestration/maintenance,
- eval/security/compliance,
- other fixed operations.

These costs matter when volume is small.

A workflow with excellent variable economics can still be a bad product if its fixed operational burden is larger than the opportunity pool.

## 10. Include implementation investment

Implementation investment is separated from recurring operating cost.

Examples:

- integration engineering,
- migration,
- eval construction,
- workflow redesign,
- change management,
- security review,
- initial data cleanup.

The calculator includes implementation investment in first-year cost and computes incremental payback against the baseline.

Do not treat sunk implementation cost as a reason to continue a workflow with poor forward economics.

## 11. Model revenue and non-revenue value separately

Per successful outcome the schema records:

- `revenue_per_success_minor`
- `non_revenue_value_per_success_minor`

Revenue is cash or earned commercial value attributable to success.

Non-revenue value can represent defensible:

- labor cost avoided,
- loss avoided,
- faster cycle time with measurable economic value,
- retention value,
- risk reduction.

Do not monetize every qualitative improvement merely to make ROI positive.

If an improvement matters but cannot be valued defensibly, put it in scenario constraints/decision notes rather than inventing a dollar amount.

## 12. Fully loaded operating cost

For each scenario:

```text
variable_cost
= attempt_cost
+ human_review_cost
+ failure_recovery_cost
+ variable_support_cost

annual_operating_cost
= variable_cost
+ annual_fixed_cost

fully_loaded_cost_per_success
= annual_operating_cost / expected_successes
```

This is deliberately broader than provider spend.

## 13. Contribution economics

The calculator reports:

```text
contribution_profit
= annual_revenue - variable_cost

contribution_per_success
= contribution_profit / expected_successes
```

This helps price paid agent products without pretending fixed investment disappears.

For customer-level profitability, continue using the broader guidance in `AGENT_UNIT_ECONOMICS.md`.

## 14. Economic surplus and ROI

Recurring economic surplus:

```text
annual_total_value
= annual_revenue + annual_non_revenue_value

recurring_economic_surplus
= annual_total_value - annual_operating_cost
```

First-year economics:

```text
first_year_cost
= annual_operating_cost + implementation_investment

first_year_surplus
= annual_total_value - first_year_cost

first_year_roi
= first_year_surplus / first_year_cost
```

ROI is computed from measured/modeled KPIs. It is not itself an operating KPI.

## 15. Incremental payback versus baseline

For every alternative:

```text
incremental_recurring_surplus
= alternative_recurring_surplus - baseline_recurring_surplus

incremental_investment
= max(0, alternative_implementation - baseline_implementation)

payback_months
= incremental_investment / (incremental_recurring_surplus / 12)
```

If incremental recurring surplus is not positive, payback is undefined rather than an invented large number.

## 16. Sensitivity cases

The calculator emits three cases.

### Pessimistic

Uses:

- lower success,
- lower revenue/value,
- higher attempts,
- higher model/tool/data/compute costs,
- higher review rate/time/cost,
- higher failure recovery,
- higher support,
- higher fixed cost,
- higher implementation investment.

### Base

Uses each input's `value`.

### Optimistic

Uses the inverse favorable bounds.

Volume stays at the base value so the comparison isolates workflow economics rather than disguising a weak design behind demand growth.

This is a simple bounded sensitivity model, not a probability distribution or Monte Carlo forecast.

## 17. Read the ranges before the ranking

The script gives a base-case ranking by recurring economic surplus.

Do not auto-select the top row.

Ask:

- Does the alternative still work in the pessimistic case?
- Which input flips the decision?
- Is that input observed or assumed?
- Can a cheap experiment reduce that uncertainty?
- Does the recommended design meet quality, safety, privacy, authority, latency, and contractual requirements?
- Is the implementation investment compatible with cash/runway?

The best next move may be to improve evidence rather than to build the workflow.

## 18. Decision states

### `draft`

Safe working state. May contain public-template assumptions and unresolved fields.

### `candidate`

A real comparison with provenance on every economic input, still under review.

### `decision_ready`

A reviewed decision record with:

- a recommended scenario,
- completed review timestamp,
- no template placeholder text,
- valid scenario/baseline references,
- current referenced evidence,
- explicit assumptions and revisit triggers.

The validator checks machine-verifiable constraints. It does not certify that the business assumptions are true.

### `retired`

Preserve historical analyses after the workflow or economics are no longer current.

## 19. Connect ROI to founder outcome evidence

A workflow ROI model should get stronger after deployment.

When a real founder outcome exists, connect the analysis to the corresponding founder-outcome record and update inputs from:

- measured success rate,
- actual retry behavior,
- actual tool/provider bills,
- review minutes,
- recovery incidents,
- paid outcome value,
- support burden.

Keep the classifications intact. A self-reported payment remains self-reported unless separately verified.

The feedback loop is:

```text
business hypothesis
-> workflow ROI model
-> bounded pilot
-> founder outcome record
-> updated workflow economics
-> scale / redesign / stop decision
```

## 20. Productized agent-service example

Example: an accounts-receivable follow-up service charges per successfully recovered or progressed invoice.

Baseline:

- staff manually reviews every account,
- high labor minutes per requested outcome,
- strong success rate,
- low infrastructure cost.

Agent alternative:

- model drafts/selects follow-up actions,
- tools update CRM/accounting state,
- a minority of accounts receive human review,
- failed actions may create support/recovery cost,
- implementation requires integrations and consent/compliance controls.

Decision levers:

- success rate,
- reviewer minutes,
- tool cost,
- customer value per successful progression,
- failure/recovery cost,
- annual account volume.

Do not count emails sent as value. The success event should be closer to a customer outcome such as a qualified payment commitment, reconciled payment, or approved escalation.

## 21. Vertical SaaS workflow example

Example: an AI receptionist for local service businesses.

Baseline:

- owner/staff or answering service handles calls/messages,
- cost is dominated by labor/service fees,
- missed calls can lose bookings.

Agent alternative:

- inference and telephony/tool costs occur per interaction,
- some conversations require human escalation,
- mistakes can create booking/support recovery work,
- fixed costs include integrations, monitoring, evals, and compliance.

Customer-visible outcome:

- qualified inquiry correctly resolved, booked, or escalated according to policy.

Value can include:

- revenue from incremental accepted bookings,
- defensible avoided answering-service cost,
- but not the raw number of conversations.

Sensitivity should test whether lower review or cheaper models reduce total economics once booking errors and escalations are included.

## 22. Outcome-fee business example

Example: proposal/RFP agent paid only when an accepted deliverable reaches a defined commercial milestone.

The seller may absorb failed attempts.

Model:

```text
revenue = successes * outcome_fee
cost = all attempts + review + recovery + support + fixed operations
```

This makes success probability and attempts-per-request especially important.

A high-priced model can be the lower-cost option when it materially improves acceptance or reduces review/rework.

Do not assume the agent caused the commercial win merely because it produced the proposal. Use a success event that matches the contract and state attribution limits.

## 23. Failure-mode examples

### Cheaper inference, worse business

A lightweight model cuts inference cost 70% but increases attempts from 1.2 to 2.1 and review from 10% to 35%.

Compare fully loaded cost per success, not inference spend.

### Higher automation, worse business

Review drops from 30% to 5%, but failure rate rises and recovery requires senior operators.

The saved review cost can be smaller than expected failure loss.

### Faster workflow, no demand value

Latency falls by 80%, but customers do not pay more, churn less, or complete more useful work.

Do not assign monetary value to speed without evidence.

### Strong ROI at impossible volume

Fixed costs look attractive at 1 million annual outcomes, but the reachable market only produces 20,000.

Use defensible opportunity volume.

### Great recurring margin, bad cash decision

The workflow has strong steady-state surplus but requires implementation investment that exceeds runway.

Payback and cash constraints still matter.

### Successful tasks, negative contribution

Task success improves while human review and paid tools make variable cost exceed revenue.

Success rate is not profitability.

## 24. Optimization experiments after baseline

Change one important lever at a time where possible.

Examples:

- route easy requests to deterministic code,
- use a cheaper model only for a bounded task class,
- replace repeated tool sequences with deterministic meta-tools,
- cap/restructure context,
- reduce retries with better stop/escalation rules,
- target review to high-risk requests,
- improve validation before expensive downstream actions,
- batch low-latency-value work,
- cache stable retrieval where invalidation risk is controlled.

For every experiment compare:

- success rate,
- attempts per request,
- review rate/minutes,
- failure recovery,
- latency if customer value depends on it,
- fully loaded cost per success,
- contribution/economic surplus.

## 25. What the calculator deliberately does not do

It does not:

- fetch live provider prices,
- infer customer willingness to pay,
- claim causal ROI from before/after data,
- convert tail legal/safety risks into permission to operate,
- authorize spend,
- choose a model/provider automatically,
- treat benchmarks as your production evidence,
- hide uncertainty behind one score.

Those boundaries keep the artifact portable and GitHub-native.

## 26. Operating review cadence

Re-run the analysis when:

- pricing changes materially,
- a model/provider changes,
- the workflow architecture changes,
- success or review rates drift,
- a new incident/failure class appears,
- the customer-visible success definition changes,
- volume changes enough to alter fixed-cost amortization,
- a major assumption reaches its revisit trigger.

Do not preserve an old favorable ROI number after the inputs changed.

## 27. Founder decision checklist

Before marking an analysis `decision_ready`:

- [ ] Same customer-visible outcome across scenarios.
- [ ] Real baseline represented.
- [ ] At least two alternatives compared.
- [ ] Success rate has provenance and range.
- [ ] Retry/refinement cost included.
- [ ] Model/context/tool/data/compute spend included.
- [ ] Human review rate, time, and labor cost included.
- [ ] Failure recovery included.
- [ ] Variable support included.
- [ ] Fixed operations included.
- [ ] Implementation investment included.
- [ ] Revenue and non-revenue value kept separate.
- [ ] Assumptions have owners and revisit triggers.
- [ ] Pessimistic/base/optimistic cases reviewed.
- [ ] Incremental payback versus baseline reviewed.
- [ ] Quality/safety/authority/latency/cash constraints recorded.
- [ ] Recommendation does not claim stronger causality than evidence supports.

## Current ecosystem rationale

Recent 2026 work reinforces these design choices:

- McKinsey's August 24, 2026 agentic-workflow economics analysis emphasizes fully loaded completed-work economics and reports that human oversight can dominate variable costs in some enterprise workflows.
- McKinsey's cost-versus-value analysis highlights long-lived context, refinement/reverification, orchestration choices, and failure recovery as major cost drivers, and argues that agent cost behaves as a distribution rather than one fixed number.
- Microsoft Research's April 2026 study of agentic coding tasks reports very high and highly variable token consumption across repeated tasks and finds that higher token use does not reliably translate into higher accuracy.
- Microsoft Research's January 2026 Agent Workflow Optimization work shows that reducing redundant reasoning/tool sequences can simultaneously reduce calls and improve task success, illustrating why cost and quality should be optimized together.

These are directional ecosystem signals, not universal benchmarks for your workflow. Preserve dated source evidence if you use any external numeric benchmark in a real analysis.

## Operating rule

**Optimize completed-work economics, not agent activity.**

A workflow earns the right to scale when its customer-visible success, fully loaded cost, uncertainty, failure recovery, human oversight, and implementation payback are all explicit enough to support the decision—and its non-economic constraints still permit the work.
