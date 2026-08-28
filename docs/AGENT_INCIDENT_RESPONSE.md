# Agent Incident Response, Containment, and Postmortems

Production agent incidents are not ordinary application errors. A tool-using agent can combine software failure, policy violation, stale or adversarial data, autonomous retries, customer-visible side effects, delegated authority, and economic loss in one event. Incident response therefore needs to answer not only **what broke**, but **what the agent did, under whose authority, what evidence proves it, what must be contained, and what can safely resume**.

This guide complements runtime reliability, security evals, release management, business continuity, economic integrity, and customer success. Reliability runbooks help recover known failure modes; this operating system records and governs a specific incident from detection through verified closure.

## 1. Lifecycle

Use an explicit state machine:

`detected -> triaged -> contained -> investigating -> remediating -> recovery_verification -> monitoring -> closed`

A closed incident may move to `reopened` when new evidence invalidates the closure decision.

Status does not grant authority. An incident commander still needs real authority to disable production actions, revoke credentials, roll back releases, contact customers, issue credits, move money, or change policy.

## 2. Severity is evidence-backed

Classify severity from observable impact rather than anxiety or model confidence. Consider:

- customer impact and number of affected tenants;
- data exposure, integrity loss, or cross-tenant access;
- unauthorized tool/action use;
- financial, ordering, messaging, fulfillment, or legal side effects;
- service unavailability or material degradation;
- blast radius and recurrence likelihood;
- ability to contain safely.

A suggested portable scale is `SEV0` through `SEV4`, where lower numbers are more severe. Define local thresholds separately. The portable record should preserve the evidence used for a classification or downgrade instead of pretending one universal threshold fits every business.

## 3. Detect and preserve before cleaning up

High-value evidence includes:

- trace and workflow IDs;
- agent/release/model/tool/policy versions;
- tool-call and side-effect receipts;
- authorization and policy decisions;
- queue/job state and retry counters;
- billing/metering events;
- alerts and detection events;
- immutable log or snapshot references;
- customer-impact references.

Portable public records should store references, hashes, timestamps, and classifications—not raw private payloads, credentials, secret prompts, exploit material, or customer data.

If destructive cleanup would erase evidence, preserve the evidence first when doing so is safe and authorized.

## 4. Containment matrix

Choose the narrowest control that stops further harm:

| Containment | Typical use | Authority concern |
|---|---|---|
| Pause new intake | retry storm, unknown failure | admission-control authority |
| Disable one tool/action class | unsafe side effect | tool/policy authority |
| Enter read-only mode | uncertain external writes | runtime/policy authority |
| Isolate one tenant | tenant-specific compromise | tenant/runtime authority |
| Freeze a release | regression or model/tool change | release authority |
| Disable provider/integration | compromised dependency | dependency authority |
| Revoke delegated authority | unauthorized action path | identity/authority owner |
| Kill switch | uncontrolled consequential behavior | emergency authority |

Containment must not silently disable authentication, logging, safety checks, evidence retention, or other controls merely to restore throughput.

## 5. Separate facts from hypotheses

Maintain three fields during investigation:

- **observed facts**: directly supported by evidence;
- **causal hypotheses**: plausible explanations still being tested;
- **unknowns**: material questions not yet resolved.

Do not promote a hypothesis to root cause because it sounds coherent. A postmortem can close operationally while retaining unresolved causal uncertainty, but not when that uncertainty is critical to security, data integrity, authority, or economic reconciliation.

## 6. Reconcile consequential side effects

For every incident involving external actions, build a side-effect ledger:

- operation ID / idempotency key;
- intended action;
- observed provider/system receipt;
- state: `confirmed_success`, `confirmed_failure`, `duplicate`, `compensated`, or `uncertain`;
- customer/account reference where safe;
- financial exposure or credit estimate;
- reconciliation owner;
- resolution evidence.

Never assume an operation failed because the agent timed out. Payments, orders, messages, file writes, account changes, or API mutations may have succeeded after the local caller lost the response.

Normal closure fails closed while material economic or consequential side effects remain `uncertain`.

## 7. Customer impact and notification

Record:

- whether customer impact occurred;
- affected tenant/customer count or bounded estimate;
- affected capability and time window;
- what customers observed;
- notification decision and owner;
- legal/compliance escalation reference when required;
- communication evidence when communication occurred.

The repository does not encode jurisdiction-specific breach-notification deadlines. Resolve those through applicable policy and qualified counsel instead of inventing them in an agent workflow.

## 8. Recovery verification

Do not equate a deployed fix with recovery. Before resuming normal production, verify with current evidence that:

- the triggering condition is no longer active;
- identity and authorization controls are healthy;
- affected policy/security controls are healthy;
- relevant data integrity is restored or bounded;
- duplicate/replay risk is reconciled;
- required dependencies and observability are healthy;
- rollback or containment remains available if monitoring fails;
- customer-impact handling is owned;
- production authority is still valid and was not inferred from incident status.

Use a monitored recovery window before closure for consequential incidents.

## 9. Postmortem structure

A useful postmortem records:

1. concise incident summary;
2. observed timeline;
3. customer/business impact;
4. confirmed facts;
5. causal hypotheses and confidence;
6. root cause only when actually evidenced;
7. contributing conditions;
8. detection gaps;
9. containment/remediation decisions and authority used;
10. economic side-effect reconciliation;
11. what worked and what failed;
12. corrective actions.

Avoid blame-oriented narrative. The operational purpose is to make recurrence less likely and detection/containment faster.

## 10. Corrective actions need verification

Each corrective action needs:

- owner;
- due date;
- action class (`prevent`, `detect`, `contain`, `recover`, `govern`);
- status;
- verification evidence;
- recurrence/failure-mode test when applicable.

`done` is not enough. Close an action only when the intended control change is verified.

Examples:

- add a cross-tenant retrieval isolation test;
- move a dangerous tool behind a narrower authority envelope;
- add a retry-storm detector;
- require idempotency receipts before workflow completion;
- add a release canary gate for a failure class;
- add evidence retention for a previously invisible tool path.

## 11. Core incident metrics

Track at least:

- mean/median time to detect (MTTD);
- time to triage;
- time to containment;
- time to verified recovery;
- affected successful outcomes or customers;
- known economic loss, refunds, and credits;
- duplicate or uncertain side effects;
- recurrence rate by failure class;
- detection source and false-negative lessons;
- overdue corrective actions.

Optimize for earlier detection and bounded impact, not cosmetically short incident duration.

## 12. Machine-readable record

Use `templates/INCIDENT_RESPONSE_RECORD.json` as the conservative starter and validate with:

```bash
python scripts/validate_incident_response.py templates/INCIDENT_RESPONSE_RECORD.json
```

The validator intentionally fails closed on unsafe portable records, unsupported closure, missing authority evidence for consequential containment, unreconciled side effects, missing customer-impact assessment, stale recovery verification, and corrective actions closed without evidence.

## 13. Failure-mode exercises

Practice incidents such as:

- agent claims success despite a failed tool receipt;
- a compromised tool begins returning cross-tenant data;
- an autonomous retry loop sends duplicate messages;
- a release change widens effective authority unexpectedly;
- a payment API times out after settlement;
- a provider credential is exposed in agent telemetry;
- a retrieval source is poisoned or stale;
- monitoring loses the trace span covering the consequential action;
- remediation fixes the symptom but the recurrence test still fails;
- a customer-impacting incident is closed before notification ownership is resolved.

The target is deterministic containment, evidence preservation, safe recovery, and verified learning—not merely producing a polished postmortem.