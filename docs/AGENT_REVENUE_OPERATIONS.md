# Agent Sales Pipeline, Opportunity, Forecasting, and Revenue Operations

Agent founders need more than prospecting automation. They need a defensible system for deciding **which accounts are real opportunities, why a deal is in its current stage, what the next authorized action is, and how much pipeline should actually count in a forecast**.

This guide turns CRM state into an evidence-backed operating contract for autonomous and human-agent sales teams.

## Core rule

> A model may recommend a stage, forecast, contact, or next action. It may not convert that recommendation into commercial fact without evidence and authority.

Keep four things separate:

1. **buyer evidence** — what a buyer or commercial artifact actually established,
2. **seller/agent inference** — useful hypotheses that still need confirmation,
3. **CRM state** — the operational representation of the deal,
4. **authority** — what the agent or operator is allowed to change or send.

A writable CRM token is not permission to contact a customer, send a quote, make a pricing promise, commit a forecast, or mark revenue won.

## Canonical artifacts

- Playbook: `docs/AGENT_REVENUE_OPERATIONS.md`
- Schema: `schemas/revenue-opportunity-record.schema.json`
- Safe starter: `templates/REVENUE_OPPORTUNITY_RECORD.json`
- Validator: `scripts/validate_revenue_opportunity.py`

Validate the starter:

```bash
python scripts/validate_revenue_opportunity.py templates/REVENUE_OPPORTUNITY_RECORD.json
```

## Opportunity lifecycle

Use a small lifecycle with deterministic entry/exit rules:

```text
target_account
  -> lead
  -> qualified_opportunity
  -> evaluation
  -> commercial_review
  -> commit
  -> won / lost

Any open stage may move to nurture when timing is not active.
```

### Target account

Use when the account matches an ICP or deserves research, but no buyer problem has been established.

Do not call an account an opportunity merely because it raised funding, hired a role, visited a website, or uses a relevant technology. Those are prioritization signals, not proof of pain or buying intent.

### Lead

Use when there is a concrete reason to investigate or engage, but qualification is incomplete.

Examples:

- inbound request,
- authorized referral,
- public buying signal,
- explicit response to outreach,
- product-qualified usage signal.

### Qualified opportunity

Require at minimum:

- directly observed problem evidence,
- current evidence supporting the stage,
- a plausible value hypothesis,
- an authorized next step.

The repository validator rejects advanced stages supported only by seller/agent inference.

### Evaluation

Use when the buyer is actively evaluating the offer or solution.

Know at least enough of the decision process to explain what must happen next. A demo request alone does not prove procurement path, budget, or authority.

### Commercial review

Use when price/package, security, procurement, legal, or contract work is active.

Require:

- observed economic-buyer identity,
- known decision process,
- `pricing-deal-desk` package reference,
- close-date hypothesis,
- explicit blockers.

### Commit

Reserve this for unusually strong evidence. Require:

- observed economic buyer,
- current buyer/commercial evidence,
- sent or accepted quote,
- explicit forecast authority,
- a close date,
- no reliance on seller confidence alone.

“Great call,” “verbal enthusiasm,” or “champion thinks legal is fine” should not automatically become commit.

### Won

Require an accepted commercial state plus enough handoff detail to preserve what was actually sold:

- accepted scope,
- success criteria,
- accepted quote/package,
- observed commercial evidence,
- authority to mark won/lost.

A won record should be ready to hand directly into contracting, billing, and customer success without reconstructing promises from chat history.

### Lost

Close explicitly and preserve the best available loss reason. Do not silently delete or recycle failed deals because it corrupts conversion and cycle-time evidence.

### Nurture

Use when the account remains relevant but no active buying process exists. Nurture is not a hiding place for stale pipeline.

## Buyer map

Track roles, not invented people.

Useful roles:

- champion,
- economic buyer,
- end user,
- technical buyer,
- procurement,
- security,
- legal,
- executive sponsor.

Each identity state should be one of:

- `unknown`,
- `inferred`,
- `observed`.

An inferred role can help plan discovery, but it should not satisfy stage gates requiring an observed economic buyer.

Never manufacture a contact because an org chart suggests one probably exists.

## Evidence hierarchy

For stage and forecast decisions, prefer evidence in roughly this order:

1. accepted contract, quote, or payment evidence,
2. explicit buyer statement,
3. meeting note capturing a buyer statement or agreed next step,
4. CRM event backed by a real external event,
5. public buying signal,
6. seller/agent inference.

Seller inference is useful for prioritization. It is weak evidence for advancing stage or forecast category.

Evidence can be:

- `current`,
- `stale`,
- `disputed`,
- `draft`.

Only current evidence should support material stage and commit decisions.

## Qualification without fake precision

A compact qualification model asks four questions:

| Dimension | Question |
|---|---|
| Problem | Has the buyer actually confirmed a painful workflow or desired outcome? |
| Value | Is the economic value observed or reasonably estimated? |
| Timing | Is there buyer-backed timing, or only seller urgency? |
| Decision process | Do we know who/what must approve purchase? |

The record deliberately distinguishes `observed`, `estimated`/`inferred`, and `unknown` states.

Do not turn a generic scoring model into false certainty. A 92/100 lead score is not more trustworthy than its inputs.

## Forecast discipline

Use four forecast categories:

- `pipeline` — active but not strong enough for best case,
- `best_case` — plausible upside with meaningful buyer evidence,
- `commit` — strong buyer/commercial evidence and authorized commitment,
- `closed` — won or lost.

Keep `probability_bps` separate from `seller_confidence`.

A probability is a modeling input. Confidence says how strong the evidence behind the estimate is. Neither should erase the raw evidence.

### Weighted pipeline

For a set of opportunities:

```text
weighted_pipeline
= sum(expected_value * probability)
```

Treat this as a planning estimate, not booked revenue.

### Coverage

```text
pipeline_coverage
= qualified_pipeline / revenue_target
```

Coverage is useful only when stage definitions are stable and stale pipeline is removed.

### Forecast error

After periods close, compare predicted and realized outcomes:

```text
forecast_error
= predicted_revenue - realized_revenue
```

Track bias over time. Consistent overforecasting is often a stage/evidence problem, not just a model-calibration problem.

## Pipeline hygiene

### Duplicate detection

Every opportunity record has an account `duplicate_key` so the operating system can detect duplicate account/opportunity creation before autonomous outreach multiplies it.

In a real CRM also compare:

- normalized domain,
- parent/subsidiary relationship,
- external account IDs,
- active opportunity scope,
- product/region when multiple parallel opportunities are legitimate.

### Stale opportunities

Define an aging policy by stage. Useful triggers include:

- no buyer evidence within the expected stage window,
- overdue next action,
- repeated close-date slippage,
- quote expired,
- champion left,
- blocker unchanged across multiple reviews.

Do not auto-close solely because a timer fired. Reassess and record the decision.

### Close-date drift

Track every material close-date change. Repeated slippage should reduce forecast confidence until new buyer evidence supports the new date.

### CRM conflicts

When an agent, rep, enrichment tool, and integration disagree, preserve provenance rather than last-write-wins truth.

Escalate contradictions in:

- stage,
- buyer role,
- forecast category,
- deal amount,
- close date,
- quote status,
- loss reason.

## Next-action contract

Every open active deal should have a concrete next action with:

- action type,
- owner,
- due time when applicable,
- whether external contact is required,
- supporting evidence.

Examples:

- research an unresolved stakeholder,
- qualify timing,
- hold agreed meeting,
- send approved follow-up,
- complete security review,
- route procurement,
- send approved quote,
- prepare contract,
- hand off a won deal.

“No next step” is a signal that the opportunity may be stale or mis-staged.

## Communications handoff

Before any external contact, apply `docs/AGENT_COMMUNICATIONS_CONSENT.md`.

Check:

- recipient eligibility,
- consent or applicable communication basis,
- suppression state,
- frequency caps,
- channel rules,
- sender identity,
- required human approval.

A qualified opportunity does not override a suppression list.

## Pricing and commercial handoff

Use `pricing-deal-desk` for packages and quotes.

The opportunity record references the package; it should not duplicate or silently mutate the pricing contract.

Separate permissions for:

- sending a quote,
- making pricing claims,
- changing CRM stage,
- committing a forecast.

A sales agent that can update an opportunity should not automatically be able to discount it.

## Won-deal handoff

Preserve at least:

- accepted scope,
- success criteria,
- stakeholders,
- package/quote reference,
- commercial blockers that became obligations,
- promised dates or outcomes when properly authorized.

Feed this into service contracting, billing/revenue assurance, and `customer-success`.

The goal is to prevent the classic failure where the sales agent promises one thing and the delivery agent starts from a generic account summary.

## Authority model

Keep these permissions distinct:

- `can_write_crm`,
- `can_contact`,
- `can_change_stage`,
- `can_send_quote`,
- `can_make_pricing_claims`,
- `can_commit_forecast`,
- `can_mark_won_lost`.

Any granted authority needs provenance and a review timestamp.

Repository templates grant none of these rights by default.

## Metrics worth tracking

Prefer operating metrics tied to real sales quality:

- qualified opportunities created,
- qualified-to-evaluation conversion,
- evaluation-to-commercial conversion,
- win rate,
- median stage duration,
- close-date slippage,
- stale-opportunity rate,
- duplicate-opportunity rate,
- false-positive qualification rate,
- forecast error and bias,
- accepted next-step rate,
- meetings per qualified opportunity,
- human review minutes per opportunity,
- unauthorized-action blocks.

Do not optimize raw emails sent, CRM writes, or “agent activity.” Those can rise while pipeline quality falls.

## Failure-mode evals

At minimum test:

1. **Hallucinated buyer** — inferred contact is treated as observed economic buyer. Reject stage advancement.
2. **Stale buying signal** — old public signal supports current qualification. Reject when current evidence is required.
3. **Duplicate prospect** — second autonomous flow creates another opportunity for the same active scope. Detect using stable duplicate keys.
4. **Unsupported stage advancement** — seller inference alone moves lead to qualified. Reject.
5. **Fake verbal commit** — optimistic seller note becomes commit forecast without buyer evidence. Reject.
6. **Close-date drift** — repeated date changes preserve high confidence without new evidence. Flag for review.
7. **Suppressed outreach** — sales next action tries to contact a suppressed recipient. Communications policy must block it.
8. **Unauthorized quote** — agent prepares/sends quote without quote authority. Reject send action.
9. **Pipeline inflation** — inactive/nurture records counted as qualified pipeline. Exclude by metric definition.
10. **CRM write conflict** — two systems disagree on stage or amount. Preserve both provenance paths and escalate.
11. **Premature won** — deal marked won before accepted commercial evidence and handoff scope exist. Reject.
12. **Authority collapse** — CRM-write permission is treated as contact/forecast/discount permission. Reject.

## Safe automation pattern

```text
observe signal
  -> classify evidence
  -> recommend CRM change
  -> validate stage criteria
  -> validate real authority
  -> write state
  -> choose next action
  -> apply communications/commercial policy
  -> execute only authorized action
  -> record resulting evidence
```

This lets agents move quickly without allowing generated confidence to become generated revenue.

## Business opportunities

The operating gap also creates product opportunities:

- evidence-backed autonomous CRM middleware,
- forecast-verification agents,
- duplicate/stale-pipeline cleanup agents,
- buyer-map evidence services,
- sales-to-CS promise provenance,
- cross-CRM agent audit layers,
- agent sales authority policy engines,
- forecast calibration and false-positive qualification benchmarks.

The durable advantage is not “AI that updates Salesforce.” It is a revenue system where another agent, founder, buyer, or auditor can reconstruct **why the pipeline says what it says**.
