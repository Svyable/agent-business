# Agent Customer Implementation, Go-Live, and Adoption

A won deal is not a production deployment. This operating system covers the risky middle: preserving what was sold, configuring integrations and data access, proving the workflow in production-representative evals, staging exposure, obtaining customer acceptance and real production authority, surviving hypercare, and handing a truthful operating baseline to customer success.

Use `templates/CUSTOMER_IMPLEMENTATION_RECORD.json` as the portable record and validate it with `python scripts/validate_customer_implementation.py <record.json>`.

## Lifecycle

`sold -> implementation_planning -> configuring -> validating -> rollout_ready -> live -> hypercare -> handed_to_customer_success`, with `rolled_back` available from any production-exposed phase.

Status is descriptive. It never creates authority. Production authority must exist in the operating environment and be referenced as current evidence before go-live.

## Freeze the commercial handoff

Start from the won opportunity. Copy the customer-accepted scope and measurable success criteria without silently improving, expanding, or reinterpreting them. If implementation uncovers a new requirement, treat it as a change request or new commercial decision rather than mutating the historical promise.

A post-planning record requires current handoff evidence. This makes scope drift detectable and creates a deterministic bridge from `revenue-ops` into implementation.

## Separate environments and promotions

Declare sandbox/test/staging/production explicitly. A demo, local run, or sandbox eval cannot justify production readiness. Production promotion needs its own current evidence and approval state.

Do not place credentials, tokens, connection strings, private prompts, or raw customer records in the portable file. Record only references, classifications, owners, states, and evidence safe for public disclosure.

## Make integrations failure-aware

For each consequential integration—API, MCP server, webhook, identity provider, CRM, billing system, or data source—record configuration state, rate-limit behavior, failure behavior, and validation evidence. Before an integration can be marked `validated` or `production`, both rate limits and failure behavior must be defined and current test evidence must exist.

Useful failure behavior includes idempotency, retry ceilings, quarantine handling, degraded modes, timeout behavior, owner/escalation, and what the agent must not do when the dependency is ambiguous.

## Resolve data readiness before production exposure

Production-capable states require evidence that source authority, minimum necessary fields, retention, residency, deletion, and test-data handling are resolved. Customer-data training/use may not remain `unknown`.

This is a record of decisions, not a place to store the underlying private data or credentials.

## Require production-grade evals

Before `rollout_ready`, the implementation should have a representative test set, regression suite, safety/policy cases, human-review policy, acceptance thresholds, known limitations, and monitoring alignment. `production_grade_passed` must be backed by current eval evidence.

A successful sandbox demo is not a production-grade eval. Representative workloads should include known edge cases, expected tool failures, permission denials, stale data, malformed inputs, and escalation paths.

## Stage rollout and make rollback real

Define a rollout strategy, exposure cap, rollback path, kill switch, and objective rollback triggers before consequential production exposure. Exposure can be bounded by users, traffic percentage, account cohort, geography, workflow class, spend, or another measurable unit.

Rollback should restore a known safe operating mode; “we can disable it manually” is not enough unless owner, procedure, and trigger are explicit.

## Treat adoption as production readiness

A technically correct agent can still fail operationally. Before production-capable status, complete operator training, communications, SOP updates, human escalation, and adoption metrics. Record affected roles and how success or failure changes daily work.

Adoption metrics should favor workflow outcomes—utilization of the intended path, handoff quality, manual-review burden, exception volume, and time to first value—not login counts alone.

## Fail closed at go-live

Go-live requires explicit request and approval, current customer-acceptance evidence, current production-authority evidence, approved production promotion, security/privacy readiness, reliability readiness, observability readiness, a support owner, production-grade eval evidence, rollback and kill switch, completed adoption readiness, and zero unresolved critical blockers.

The implementation record does not grant production permission. It can only prove that a separate authority grant was observed and remains current.

## Hypercare and handoff

During hypercare, define incident thresholds, review cadence, customer communications, and exit criteria. Do not hand off to customer success while hypercare remains active.

The customer-success handoff should preserve the activation baseline, actual configured permissions, support/escalation map, known limitations, first-value milestone, and current handoff evidence. This prevents customer success from inheriting an aspirational configuration instead of the real deployed one.

## Economics and observability

Track implementation cost, rework cost, delay cost, contracted implementation revenue, and time to live. Feed stable workflow economics into `workflow-roi` rather than inventing a second ROI model.

Recommended operating metrics include time to first valid eval, time to production, first-value time, implementation variance, defect escape rate, rollback rate, integration failure rate, human-review burden, support load, and adoption/utilization. Keep denominators and observation windows explicit.

## Failure-mode evals

At minimum test scope drift from the won deal; credentials embedded in the portable record; production promotion from sandbox-only evidence; validated integration without rate-limit/failure behavior; hidden or unknown customer-data training use; missing rollback or kill switch; stale customer acceptance; unsupported production authority; missing monitoring; incomplete operator training; unresolved critical blocker; and premature customer-success handoff.

## Minimal operating cadence

At implementation kickoff, freeze scope, success criteria, and owners. During configuration, review integration and data blockers. During validation, run regression and safety suites against production-representative conditions. Before rollout, conduct the deterministic go-live gate. During hypercare, review incidents and adoption at a cadence proportional to risk. At handoff, snapshot actual permissions, limitations, owners, value baseline, and evidence.
