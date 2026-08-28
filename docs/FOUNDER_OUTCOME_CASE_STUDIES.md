# Founder Outcome Evidence and Case Studies

Agent Business should compound **results**, not anecdotes.

This protocol turns a voluntary public adoption report into a reusable, machine-readable founder outcome record and, only when the evidence is strong enough, a published case study.

The governing principle is:

> Usage is not value. A story is not evidence. A correlation is not automatically causation.

The repository should make it easy to say what happened, what evidence supports it, what remains self-reported or estimated, and how confidently the result can be attributed to the intervention.

## Why this matters

Agent founders need examples that answer questions such as:

- Did someone actually use this playbook?
- What business decision or artifact changed?
- Was there a baseline before the change?
- Did revenue, cost, speed, quality, risk, retention, or learning improve?
- What part is directly observed versus self-reported?
- Is the result reproducible?
- What did the agent cost to operate?
- How much human review was required?
- What failed?
- Would another founder know what to copy and what not to infer?

Current agent programs increasingly face the same measurement problem: activity metrics can show that an agent was used, but they do not by themselves establish business value. Agent Business therefore treats outcome evidence as a first-class operating artifact.

## The public evidence pipeline

```text
GitHub discovery
      |
      v
repository usage
      |
      v
Agent / founder adoption issue
      |
      v
candidate outcome record
      |
      +---- insufficient evidence ----> keep as adoption report
      |
      v
editorial evidence review
      |
      +---- disputed / private / unclear ----> do not publish
      |
      v
published outcome record
      |
      v
human-readable case study
      |
      v
reusable benchmark / playbook improvement
```

The adoption issue is the intake channel. The outcome record is the evidence structure. A case study is the editorial presentation built on top of that structure.

## Canonical artifacts

- Schema: `schemas/founder-outcome-record.schema.json`
- Safe starter: `templates/FOUNDER_OUTCOME_RECORD.json`
- Semantic validator: `scripts/validate_founder_outcome.py`
- Published-case registry: `case-studies/README.md`
- Intake form: `.github/ISSUE_TEMPLATE/agent-adoption.yml`

Validate a draft:

```bash
python scripts/validate_founder_outcome.py templates/FOUNDER_OUTCOME_RECORD.json --allow-draft
```

Validate a publication candidate:

```bash
python scripts/validate_founder_outcome.py case-studies/<case>.json
```

## Evidence classifications

Every claim has one explicit classification.

### `observed_fact`

A fact directly supported by public evidence or a reproducible artifact.

Examples:

- a public GitHub issue was opened on a stated date,
- a public benchmark output reports a specific result,
- a repository artifact contains a specific approved decision,
- a public invoice-like test fixture demonstrates a calculation.

Observed does not necessarily mean causal.

### `self_reported`

A claim made by the founder, agent operator, or reporting team that the repository cannot independently verify from public evidence.

Examples:

- “we booked three qualified calls,”
- “the customer paid $500 for the pilot,”
- “human review dropped from 40 minutes to 12 minutes.”

Self-reported claims can be valuable. They must remain labeled as self-reported.

### `estimate`

A calculated or modeled value based on assumptions.

Examples:

- estimated annual savings,
- modeled gross margin,
- estimated hours returned,
- projected conversion value.

The assumptions should be reconstructable from evidence or clearly stated context.

### `editorial_interpretation`

A conclusion drawn by the repository maintainers from the evidence.

Examples:

- “the narrower ICP appears to have improved learning velocity,”
- “this result is promising but attribution is weak,”
- “the workflow is not yet economical at the reported review burden.”

Editorial interpretation should never be written as an observed fact.

## Evidence types

Outcome records can reference several evidence types.

### Public artifact

A public, durable artifact such as:

- GitHub issue,
- pull request,
- public founder packet,
- public benchmark output,
- public customer-facing page,
- public experiment result.

### Public metric

A metric visible in an authorized public source.

### Reproducible calculation

A calculation whose inputs, formula, and output can be reconstructed.

For example:

```text
contribution margin
= pilot revenue
- model/tool variable cost
- contractor/reviewer variable cost
- payment/refund variable cost
```

### Self report

A public statement by the reporter. This is useful evidence of what was reported, not independent verification that the underlying business event occurred.

### Third-party source

A public source outside the founder or repository.

### Editorial note

A repository-maintainer note describing review scope, contradictions, or unresolved uncertainty.

## Baseline before intervention

A result without a baseline is hard to interpret.

Whenever possible, capture the pre-change state before the intervention:

- qualified conversations per week,
- conversion rate,
- time to complete the workflow,
- error rate,
- human-review minutes,
- cost per successful outcome,
- contribution margin,
- churn/retention,
- incident frequency,
- decision cycle time.

A baseline should identify the observation period.

Bad:

```text
Sales improved a lot.
```

Better:

```text
During the two weeks before narrowing the offer, the founder reported zero qualified paid-pilot conversations from 42 targeted contacts.
```

That still may be self-reported. The important improvement is that the comparison is interpretable.

## Outcome value drivers

The schema uses broad value drivers so cases can be compared without forcing every business into the same metric.

### Revenue

Examples:

- paid pilots,
- booked qualified opportunities,
- conversion,
- retained revenue,
- expansion revenue.

### Cost

Examples:

- variable delivery cost,
- model/tool spend,
- human-review labor,
- cost per successful outcome.

### Speed

Examples:

- cycle time,
- time to first response,
- time to complete a customer workflow,
- time to evidence-backed decision.

### Quality

Examples:

- defect rate,
- acceptance rate,
- rework,
- verified task success.

### Risk

Examples:

- unsafe-action rate,
- exception volume,
- policy violations,
- dispute/chargeback rate.

### Retention

Examples:

- repeat usage,
- renewal,
- retained customers,
- expansion.

### Learning

Examples:

- customer/problem decision,
- invalidated hypothesis,
- willingness-to-pay signal,
- channel decision,
- business-model pivot.

A negative result can be a useful learning outcome when it prevents larger wasted spend.

## Attribution confidence

Every outcome carries `low`, `medium`, or `high` attribution confidence.

### Low

Use when:

- no meaningful baseline exists,
- several variables changed at once,
- the result is mostly anecdotal,
- evidence is sparse,
- the time window is extremely short.

### Medium

Use when:

- a baseline exists,
- the intervention is reasonably scoped,
- evidence is concrete,
- alternative explanations still exist.

### High

Reserve for unusually strong evidence, such as:

- controlled experiments,
- repeated measurements with stable methodology,
- tightly isolated workflow changes,
- independent verification.

Do not use “high” merely because the result is large.

## Publication states

### Draft

A work-in-progress record. Drafts may contain placeholders and may have no evidence yet.

The validator requires `--allow-draft` for these records so a draft cannot be mistaken for publication-ready evidence.

### Candidate

A real report with at least one evidence item that is being reviewed for publication.

Candidate does not mean verified.

### Published

A record accepted into the public case-study registry.

Publication requires:

- a positive source GitHub issue number,
- at least one evidence item,
- evidence for every published outcome,
- evidence for every non-editorial claim,
- only current evidence supporting published outcomes,
- no known placeholder text,
- a completed editorial review timestamp,
- explicit public-disclosure confirmation,
- no private-data flags.

### Retired

A previously useful record that should no longer be treated as current. Preserve provenance rather than silently deleting history when appropriate.

## Publication review

Before setting `publication_status` to `published`, review the record in this order.

### 1. Public-data check

Reject or redact the candidate if it contains:

- credentials,
- secrets,
- private prompts,
- payment credentials,
- private customer information,
- personal information not intended for publication,
- evidence the reporter is not authorized to disclose.

When in doubt, do not publish the sensitive detail.

### 2. Repository-use check

Every `repository_usage.resource_id` must exist in `agent-index.json`.

This lets future agents ask:

> Which Agent Business resources are associated with which reported outcomes?

### 3. Evidence-link check

Every evidence reference must resolve inside the record.

Every published outcome must reference current evidence.

### 4. Claim-classification check

Ask of every sentence intended for the case study:

- directly observed?
- self-reported?
- estimated?
- editorial interpretation?

Do not collapse these categories.

### 5. Baseline check

Can a reader tell what happened before the intervention?

If not, reduce attribution confidence and explain the limitation.

### 6. Economics check

When the reporter is comfortable making economics public, record:

- currency,
- revenue,
- variable delivery cost,
- human-review minutes.

Do not require financial disclosure as a condition of participating.

### 7. Contradiction check

If two evidence items conflict:

- mark disputed evidence as `disputed`,
- do not use it to support a published outcome,
- document the conflict in editorial notes,
- reduce confidence or decline publication.

### 8. Final semantic validation

Run:

```bash
python scripts/validate_founder_outcome.py case-studies/<case>.json
```

CI should reject a record that violates machine-verifiable publication constraints.

## Human-readable case study format

A published Markdown case study should be generated from or reviewed against its JSON outcome record.

Recommended structure:

```text
# <case title>

Status and evidence classification
Context
Problem hypothesis
Baseline
Agent Business resources used
Intervention
Outcome table
Economics / review burden, if public
Evidence
What failed or changed
Attribution limits
Reusable lessons
```

### Outcome table

A useful table looks like:

| Metric | Baseline | Result | Attribution | Evidence |
|---|---:|---:|---|---|
| Qualified paid-pilot conversations | 0 | 3 | Medium | Self-report linked to public issue |

Do not turn a self-report into “verified 3 sales” unless the evidence actually supports that stronger claim.

## Negative and null results

Publish useful failures too.

Examples:

- the business model failed the 48-hour commercial-signal test,
- a channel produced replies but no qualified buyers,
- the model cost made the offer unprofitable,
- review burden erased the automation advantage,
- buyers valued the outcome but procurement made the sales cycle unattractive,
- customers wanted a different workflow than the founder initially assumed.

Negative evidence reduces repeated mistakes across the ecosystem.

## Case-study promotion rules

An adoption report should usually remain an adoption report when:

- the outcome is too vague,
- the evidence is entirely private,
- the reporter cannot safely disclose enough context,
- the result is only “I read the repo,”
- the claim cannot be meaningfully separated from hype,
- no durable decision, artifact, or measurable outcome resulted.

Promote it to a case-study candidate when:

- the business context is clear,
- at least one indexed resource materially influenced the work,
- a durable decision/artifact/result exists,
- evidence can be made public safely,
- another founder can learn something specific from it.

## Benchmark readiness

Do not aggregate outcome records into repository benchmarks until the fields are sufficiently comparable.

Before publishing a benchmark such as “median time to first paid pilot,” verify that records use compatible definitions for:

- start event,
- success event,
- observation window,
- customer class,
- revenue definition,
- agent/human labor allocation,
- currency treatment,
- evidence confidence.

A small number of comparable records is better than a large pile of incompatible anecdotes.

## Feedback loop into the repository

Every published case should produce at least one of these decisions:

- existing playbook remains supported,
- playbook wording should change,
- new failure mode should be added,
- template should add a missing field,
- benchmark definition should be refined,
- new business-model opportunity should be added,
- a previously recommended tactic should be downgraded.

That closes the loop:

```text
Guidance -> founder action -> evidence -> case study -> better guidance
```

## What we should never claim

From the public GitHub evidence system alone, do not claim:

- number of unique autonomous agents using the repository,
- verified identity of a reporter unless separately established,
- causal ROI from a simple before/after story,
- revenue that is only projected,
- private customer validation we cannot inspect,
- representative ecosystem benchmarks from a tiny self-selected sample.

The goal is not to make the evidence look stronger than it is.

The goal is to make it **useful, inspectable, and progressively stronger**.
