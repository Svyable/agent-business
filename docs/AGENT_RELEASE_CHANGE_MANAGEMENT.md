# Agent Release, Change Management, Rollout, and Deprecation

Launching an agent once is not the same as operating it safely over time. Models change, tools change, prompts change, data contracts evolve, customer expectations shift, and production behavior drifts. This operating system makes those changes reconstructable and bounded.

Use `templates/AGENT_RELEASE_RECORD.json` as the portable record and validate it with:

```bash
python scripts/validate_agent_release.py <record.json>
```

The record is evidence about a release. It does **not** grant production authority.

## Lifecycle

`proposed -> built -> evaluated -> approved -> canary -> rolling_out -> stable`

A release may instead become `rolled_back`. A stable or superseded revision can later move through `deprecated -> retired`.

Do not skip states because a change looks small. A model, provider, tool, prompt, or policy version change is behavioral until evidence shows its effect is acceptably bounded.

## 1. Create an immutable revision identity

Every candidate needs a `revision_id` and, except for a first-ever release, a `parent_revision_id`. Treat the revision as an immutable snapshot of the behavior you evaluated. If a versioned component changes after evaluation, create a new revision and evaluate again.

A useful release record distinguishes the candidate revision from the currently trusted production baseline. “Same semantic version” or “minor model upgrade” is not evidence of behavioral compatibility.

Record affected components without embedding private prompts, credentials, raw customer data, or secret environment values.

## 2. Classify the change before evaluating it

Use one or more explicit classes:

- `patch`: operational change intended not to alter customer-visible behavior;
- `behavioral`: model, tool, prompt, policy, routing, or reasoning behavior can change;
- `commercial`: pricing, packaging, metering, entitlement, SLA, or billing semantics change;
- `security`: security control, threat surface, trust boundary, or incident behavior changes;
- `data`: collection, retention, residency, deletion, training/use, memory, or source behavior changes;
- `authority`: tool, data, spending, communication, transaction, or other delegated power changes;
- `breaking`: machine contract, stored state, integration, or downstream compatibility breaks.

Classification should be conservative. A dependency version bump is behavioral unless you can prove that it cannot affect behavior.

## 3. Compare against the actual production baseline

Advanced release states require a distinct production baseline revision with current evidence. Compare the candidate to that baseline, not to an old test snapshot.

The minimum evaluation delta should cover:

- representative regression suite;
- safety and policy cases;
- tool selection and tool-call behavior;
- latency change;
- cost-per-success change;
- human-review burden change;
- known limitations and critical regressions.

An unresolved critical regression fails closed. A release should not advance because its aggregate score improved while one consequential safety or authority behavior degraded.

## 4. Treat production dependencies as part of the release

For each changed model, provider, tool, runtime, library, or data source, record old version, new version, compatibility check, and evidence. Do not treat provider release notes alone as proof of compatibility with your workflow.

Dependency changes should be tested against the same production-representative cases as first-party changes. A provider swap can alter latency, tool calling, refusal behavior, output structure, cost, data handling, or failure modes even when the API surface is unchanged.

## 5. Never widen authority silently

A release record may describe authority, but it cannot create authority.

If a revision widens tool permissions, data access, spend limits, outbound communication rights, transaction rights, or any other consequential capability, classify the release as `authority`, obtain separate approval from the real principal/operating environment, and attach current evidence of that reapproval.

A code merge, deployment status, successful eval, or stable canary does not imply authority approval.

## 6. Make compatibility explicit

Before production exposure, check:

- machine contracts and API schemas;
- stored memory/state and migrations;
- external integrations;
- downstream consumers.

If the change is breaking, mark it breaking, define a migration path, and preserve compatibility evidence. Do not infer compatibility from semantic version labels alone.

For stateful agents, pay special attention to irreversible migrations. A rollback of code is not a rollback if the new revision mutated state into a form the prior revision cannot safely read.

## 7. Use staged production exposure

A canary is an experiment with explicit exposure and stop rules, not a hopeful partial rollout.

Before exposure define:

- canary percentage or bounded cohort;
- hold period;
- promotion criteria;
- stop conditions;
- rollback target revision;
- production metrics used to judge the release.

During `canary`, actual production traffic must stay at or below the configured canary percentage. `stable` means the candidate has reached 100% intended production traffic—not merely that no complaints were reported.

Evidence should come from explicit production observations. Absence of support tickets is not enough.

## 8. Monitor behavior and economics together

At production exposure, monitor at least:

- error rate;
- quality/safety outcomes;
- latency;
- cost per successful outcome;
- escalation/human-review rate;
- customer-impact incidents.

Also track rollback rate, adoption, and change failure rate over time. The goal is not only technical stability; a release that doubles cost or review burden for the same customer outcome can still be a regression.

Use `workflow-roi` for deeper outcome economics and `run` for runtime reliability. The release record should point to current measurements rather than inventing a second observability system.

## 9. Make rollback executable before rollout

Production exposure requires:

- a defined rollback procedure;
- a tested rollback path;
- an accountable owner;
- a known rollback target;
- explicit treatment of state/data migration reversibility.

If irreversible changes exist, record them and design a forward-recovery path. Do not mark state migration reversible when irreversible changes are known.

A rollback trigger should be objective enough to act on under pressure: critical safety failure, defined quality regression, error-rate threshold, customer-impact incident, cost spike, or authority-policy violation.

## 10. Communicate material customer impact before exposure

Behavior, data, pricing, metering, availability, compatibility, and security changes may require customer communication. Commercial, data, and breaking changes should be presumed material until reviewed.

For material changes, complete required customer communication before production exposure or deprecation. Preserve evidence of the notice, not private customer correspondence itself.

A release must never silently change what a customer is billed for, what data is used, or what interface they depend on.

## 11. Deprecate and retire deliberately

Deprecation is an operating phase, not a cleanup label. Define:

- whether notice is required and whether it was completed;
- support window;
- migration path;
- sunset criteria;
- migration evidence.

Do not retire a revision while required migration remains incomplete. Retain enough audit history to reconstruct what ran, when, what replaced it, and why the sunset was considered safe.

For vulnerable or unsafe old revisions, reduce exposure promptly while still preserving a bounded migration and incident path.

## Failure-mode evals

At minimum test these cases:

1. model/provider/tool version changes classified only as patch;
2. prompt/policy changes without behavioral classification;
3. advanced release without a current production baseline;
4. stale or missing eval evidence;
5. unresolved critical regression;
6. canary bypass or canary traffic above the declared cap;
7. production exposure without production metrics;
8. authority widening without separate reapproval;
9. irreversible state migration represented as reversible;
10. breaking change without migration path;
11. material customer impact without completed communication;
12. silent pricing/metering change;
13. production exposure without tested rollback;
14. stable status below full intended traffic;
15. retirement before migration completion;
16. credentials, private prompts, or private customer data embedded in the public record.

## Minimal operating cadence

Before build, classify the change and assign a revision ID. Before approval, compare against the current production baseline and close critical regressions. Before canary, confirm compatibility, rollback, observability, customer communication, and authority. During canary, review explicit production metrics across the declared hold period. During rollout, promote only when criteria remain satisfied. After stabilization, preserve the evidence that justified promotion. During deprecation, track migration until retirement criteria are actually met.

## Related Agent Business resources

Use this layer with:

- `docs/AGENT_CUSTOMER_IMPLEMENTATION.md` for first production go-live;
- `docs/AGENT_RUNTIME_RELIABILITY.md` for ongoing runtime SLOs, incidents, and recovery;
- `docs/AGENT_API_CONTRACTS_INTEROPERABILITY.md` for interface evolution and compatibility;
- `docs/AGENT_DEPENDENCY_SUPPLY_CHAIN.md` for third-party dependency risk;
- `docs/AGENT_SECURITY_EVALS.md` for security and safety evaluation;
- `docs/AGENT_AUTHORITY_DELEGATION.md` for real principal authority;
- `docs/AGENT_CUSTOMER_SUCCESS_RETENTION.md` for customer-impact and lifecycle handoff;
- `docs/AGENT_WORKFLOW_ROI.md` for cost-versus-value deltas.
