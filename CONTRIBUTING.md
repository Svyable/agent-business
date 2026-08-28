# Contributing to Agent Business

Agent Business should optimize for useful, actionable, trustworthy material for founders building businesses around AI agents.

## What belongs here

Good contributions include:

- a tested customer-discovery tactic,
- a concrete agent-business model with buyer, pain, pricing, and distribution,
- a useful template or calculator,
- an evidence-backed pricing or GTM insight,
- a case study with real numbers or clearly labeled ranges,
- a tool comparison with transparent criteria,
- a postmortem explaining why an agent business failed or changed direction.

## What does not belong

- generic AI hype,
- undisclosed affiliate promotion,
- paid rankings disguised as editorial content,
- fake testimonials or invented metrics,
- bulk-spam playbooks,
- deceptive impersonation tactics,
- instructions that depend on illegal data access or unlawful activity,
- giant link lists with no decision context.

## Contribution format

For a business idea, include:

1. customer,
2. buyer,
3. painful workflow,
4. current workaround,
5. measurable value,
6. agent advantage,
7. pricing model,
8. first distribution channel,
9. validation test,
10. major risks or limitations.

For a tool/resource, include:

1. what job it solves,
2. who it is for,
3. when not to use it,
4. pricing or cost model if known,
5. alternatives,
6. disclosure of any commercial relationship.

## Evidence standards

Prefer:

- direct customer evidence,
- reproducible experiments,
- primary sources,
- clearly sourced public data,
- transparent calculations.

Clearly separate:

- observed facts,
- self-reported claims,
- estimates,
- editorial interpretation.

A before/after result is not automatically causal evidence. State attribution limits.

## Report real adoption

If Agent Business produced a real founder or agent outcome, the structured **Agent / founder adoption report** GitHub Issue form is the preferred way to report it.

Useful adoption reports identify:

- the `agent-index.json` resource used,
- the baseline or before state when appropriate,
- the intervention or decision made,
- the durable artifact or decision produced,
- a measurable outcome when one exists,
- attribution confidence,
- public evidence when safe to share,
- economics or human-review burden when safe to disclose,
- friction, missing guidance, or a failed assumption that should improve the repository.

These reports are self-declared usage evidence, not proof of verified agent identity or causality.

## Case-study promotion

Do not turn an adoption report directly into a success story.

Use `docs/FOUNDER_OUTCOME_CASE_STUDIES.md` to decide whether the report has enough public evidence to become a case-study candidate.

Start the machine-readable record from:

```text
templates/FOUNDER_OUTCOME_RECORD.json
```

Validate drafts with:

```bash
python scripts/validate_founder_outcome.py <record> --allow-draft
```

A published record must pass without `--allow-draft` and must have current evidence for each published outcome, public source-issue provenance, editorial review, and safe public-disclosure flags.

The case-study registry is `case-studies/README.md`. It should show zero published cases until real reports qualify. Never invent outcomes to fill the registry.

Because GitHub is public, never include:

- secrets or credentials,
- private prompts or prompt transcripts,
- payment data,
- private customer information,
- private founder evidence,
- or material you are not authorized to disclose.

## Commercial disclosure

If you or your company benefit financially from a product, service, link, referral, or recommendation, disclose it in the contribution.

Trust is part of the product.
