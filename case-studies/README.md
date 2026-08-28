# Agent Business Case Studies

This directory is the public registry for evidence-backed founder outcomes produced with help from Agent Business.

## Published cases

**0 published case studies.**

That is intentional. The repository does not fabricate examples to make adoption look larger than it is.

A case is added here only after a voluntary public adoption report has enough safe, specific evidence to pass the founder outcome publication protocol.

## Intake

Use the GitHub **Agent / founder adoption report** issue form to share a real result.

A report can describe:

- a customer/problem decision,
- validation evidence,
- an offer or pricing decision,
- a sales/distribution artifact,
- a paid pilot or commercial signal,
- an operating artifact,
- a cost/margin change,
- a safety/governance improvement,
- or a useful failed experiment.

Do not include secrets, credentials, private prompts, payment data, private customer information, or evidence you are not authorized to publish.

## Promotion criteria

An adoption report may become a case-study candidate when:

1. at least one `agent-index.json` resource materially influenced the work,
2. the result produced a durable decision, artifact, or measurable outcome,
3. a baseline or meaningful pre-change context exists when appropriate,
4. public evidence can support the important claims,
5. observed facts, self-reported claims, estimates, and editorial interpretation are clearly separated,
6. attribution limits are stated,
7. another founder can reuse a concrete lesson.

## Machine-readable record

Each published case should include a JSON record validated against the repository's outcome evidence contract.

Start from:

```text
templates/FOUNDER_OUTCOME_RECORD.json
```

Validate a draft with:

```bash
python scripts/validate_founder_outcome.py templates/FOUNDER_OUTCOME_RECORD.json --allow-draft
```

Validate a publication record with:

```bash
python scripts/validate_founder_outcome.py case-studies/<case-id>.json
```

See `docs/FOUNDER_OUTCOME_CASE_STUDIES.md` for the complete evidence and editorial protocol.

## Publication format

A mature case normally has two files:

```text
case-studies/<case-id>.json
case-studies/<case-id>.md
```

The JSON file is the evidence graph and machine-readable outcome record.

The Markdown file is the human-readable narrative. It must not make stronger claims than the JSON evidence supports.

## Evidence status

Published records may include self-reported evidence. Publication does **not** imply that every underlying event was independently verified.

The record explicitly classifies claims so agents and humans can distinguish:

- observed facts,
- self-reported claims,
- estimates,
- editorial interpretation.

## Why zero is better than fake

The repository's long-term value depends on founders being able to trust the evidence layer.

A registry with zero real cases is more useful than a registry padded with invented revenue numbers, synthetic testimonials, or unverifiable success stories.

The target remains the same: publish the first **3 evidence-backed founder outcome case studies** and then use those records to improve playbooks, templates, benchmarks, and future launch kits.
