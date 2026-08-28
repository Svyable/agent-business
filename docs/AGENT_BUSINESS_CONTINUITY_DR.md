# Agent Business Continuity, Disaster Recovery, and State Recovery

Production agent businesses are stateful systems, not just model endpoints. Agent definitions, policy and release configuration, retrieval indexes, memory, queues, metering state, external tool dependencies, identity controls, and customer-facing workflows can fail independently or together. Recovery therefore needs an operating contract that states what must survive, what may be reconstructed, how much loss is acceptable, who may invoke recovery, and what evidence proves recovery actually works.

Use this guide with `AGENT_RUNTIME_RELIABILITY.md`, `AGENT_RELEASE_CHANGE_MANAGEMENT.md`, `AGENT_DEPENDENCY_SUPPLY_CHAIN.md`, `AGENT_DATA_MEMORY_PROVENANCE.md`, `AGENT_MULTI_TENANT_OPERATIONS.md`, `AGENT_BILLING_REVENUE_ASSURANCE.md`, and `AGENT_CUSTOMER_SUCCESS_RETENTION.md`.

## Non-negotiable invariants

**Backup existence is not proof of recoverability.** Strong recovery claims require successful restore or reconstruction drills against explicit recovery objectives.

**Recovery status never grants production authority.** Restored state must not widen permissions, revive expired credentials, replay irreversible economic actions blindly, or bypass identity/policy controls.

**Return to normal traffic fails closed when identity, policy, authority, data integrity, or reconciliation is unresolved.**

## 1. Set recovery objectives by service criticality

Classify each customer-visible capability before choosing technology.

| Tier | Typical impact | RTO | RPO | Degraded-mode expectation |
| --- | --- | --- | --- | --- |
| Critical | revenue, regulated, safety, or contractual workflow stops | shortest justified target | minimal justified loss | preplanned human/manual or alternate-provider path |
| Important | material customer workflow delayed | bounded hours | bounded recent loss | queued or reduced-feature service |
| Standard | inconvenience but low immediate loss | longer target | wider acceptable loss | status page / delayed processing |

Record four separate concepts:

- **RTO:** target time to restore an acceptable service mode.
- **RPO:** maximum acceptable age of recoverable state.
- **Maximum tolerable downtime:** business limit beyond which the impact becomes unacceptable.
- **Degraded-mode objective:** what useful service remains while full recovery is incomplete.

Do not copy provider marketing numbers into these fields. A provider restore SLA is only one dependency in end-to-end recovery.

## 2. Inventory state by recoverability

For every stateful component, assign exactly one recovery class:

- `reconstructable`: recreated from immutable/versioned source plus deterministic procedure;
- `backed_up`: restored from an independently controlled backup;
- `replicated`: continuously or asynchronously copied to a recovery target;
- `externally_owned`: authoritative state lives with another system/provider;
- `ephemeral`: intentionally disposable and safe to lose;
- `intentionally_not_restored`: excluded for privacy, policy, or safety reasons.

At minimum inventory:

1. agent definitions and release/config versions;
2. prompts, policies, guardrails, and tool bindings by version reference;
3. model/provider and tool/API dependencies;
4. retrieval source metadata and index build recipes;
5. durable memory, threads, checkpoints, and workflow state;
6. queues, retries, scheduled jobs, and callbacks;
7. tenant configuration and entitlements;
8. metering, billing, credits, and reconciliation checkpoints;
9. audit/evidence references;
10. identity, policy, and credential references without secrets.

A release rollback restores behavior. It does not restore lost state, broken dependencies, or missing infrastructure.

## 3. Design backup and reconstruction policy

For `backed_up` state, document backup frequency, retention, encryption/control-plane boundary, restore owner, and last successful restore evidence. For `reconstructable` state, document immutable source, dependency versions, reconstruction procedure, and validation criteria.

Portable records must never contain raw backups, customer content, credentials, recovery keys, private prompts, or secrets. Record opaque evidence references and public-safe metadata only.

Test the path that matters: restore into an isolated environment, validate schema/version compatibility, verify access boundaries, and compare recovered state with the declared RPO.

## 4. Plan regional and provider failover

Choose deliberately among:

- **Cold recovery:** rebuild only after an incident. Lowest idle cost, longest RTO.
- **Warm standby:** pre-provision network/control-plane foundations and reconstruct workload resources during failover.
- **Active-passive:** maintain a ready secondary with controlled data replication.
- **Active-active:** serve multiple failure domains concurrently; highest complexity and strongest requirements for consistency, idempotency, and routing.

Document dependency order. A typical safe recovery sequence is:

1. identity and authorization;
2. policy/guardrail configuration;
3. core data stores and integrity checks;
4. secrets/credential references and revocation status;
5. model/tool connectivity and compatibility;
6. retrieval/index state;
7. agent definitions and release configuration;
8. queues/jobs with replay controls;
9. billing/metering reconciliation;
10. customer traffic.

Do not restore downstream automation while an upstream control boundary remains uncertain.

## 5. Reconstruct agent state safely

Recovery must account for agent-specific failure semantics:

- **Immutable source:** redeploy the exact approved release/config rather than reconstructing from memory.
- **Model/tool compatibility:** verify referenced versions still exist and have compatible behavior/permissions.
- **Retrieval rebuild:** rebuild indexes from authoritative sources, then validate document counts, tenant filters, freshness, and representative retrieval tests.
- **Memory/thread recovery:** preserve provenance and consent; treat partial or stale memory as uncertain rather than silently authoritative.
- **Queue recovery:** distinguish safe retries from irreversible actions. Require idempotency keys or reconciliation before replay.
- **Economic actions:** payments, purchases, refunds, credits, messages, or other consequential actions must be reconciled against external systems before retry.
- **Billing continuity:** recover metering checkpoints without double counting or dropping chargeable/creditable events.

## 6. Define graceful degradation

Continuity is broader than DR. Predefine what happens when one component is unavailable:

- agent unavailable -> human queue, static workflow, or alternate service;
- model/provider unavailable -> approved fallback model or reduced-feature mode;
- tool/API unavailable -> queue, read-only mode, or manual action;
- retrieval unavailable -> no-answer/escalation rather than ungrounded generation;
- memory unavailable -> stateless mode only where safe and disclosed;
- region unavailable -> failover according to the declared strategy;
- billing/metering uncertain -> preserve service evidence and delay irreversible settlement where appropriate.

The degraded path should have its own authority and SLOs. An emergency is not blanket permission to bypass safeguards.

## 7. Recovery authority

Separate permissions for:

- declaring continuity incident state;
- invoking failover;
- restoring or reconstructing state;
- replaying queued work;
- switching model/tool/provider/region;
- returning traffic to normal;
- invoking failback;
- declaring recovery complete.

Material authority requires current evidence. Recovery automation may execute a pre-approved runbook but must not infer new authority from incident severity.

## 8. Recovery observability and evidence

Track at least:

- backup age and replication lag;
- restore/reconstruction success rate;
- observed recovery time versus RTO;
- observed recovered point versus RPO;
- queue age and replay/duplicate rate;
- data-integrity discrepancies;
- retrieval/index validation failures;
- degraded-mode duration;
- failover/failback duration;
- customer impact and SLA/credit handoff;
- drill recency and pass/fail state.

A strong drill record includes scenario, recovery target, start/end timestamps, recovered-state cutoff, failed dependencies, integrity/reconciliation findings, customer-impact simulation, stop conditions, and evidence references.

## 9. Failback is a separate change

Do not treat failback as the inverse button of failover. Before returning to the primary environment:

1. confirm primary health and capacity;
2. converge or explicitly reconcile replicated state;
3. stop or drain conflicting writes where required;
4. verify credentials, policies, release/config, and tenant entitlements;
5. reconcile queues and economic actions;
6. verify retrieval and memory integrity;
7. test a limited cohort;
8. observe explicit promotion metrics;
9. only then restore normal routing.

If state cannot be merged safely, select an authoritative side and document the loss/reconciliation decision.

## 10. Customer and commercial handoff

For material incidents, preserve enough evidence for customer success, billing, and contracting systems to determine:

- affected customers and capabilities;
- incident/degraded-mode duration;
- known data loss or duplicated work;
- SLA applicability and service-credit review;
- customer communication status;
- recovery limitations and follow-up actions.

Do not invent credits or contractual promises inside the DR record; hand off evidence to the relevant commercial authority.

## Portable record and validator

Start with `templates/BUSINESS_CONTINUITY_RECORD.json`, governed by `schemas/business-continuity-record.schema.json`, then run:

```bash
python scripts/validate_business_continuity.py templates/BUSINESS_CONTINUITY_RECORD.json
```

The starter is intentionally `needs_review`, grants no recovery authority, and makes no recovery-readiness claim.

## Minimum failure-mode drill suite

Before declaring a critical capability recovery-ready, exercise at least:

- backup exists but restore fails;
- stale or wrong release/config reconstructed;
- required model/tool version unavailable;
- corrupted or incomplete retrieval index;
- partial memory/thread recovery;
- identity/control-plane or credential-reference outage;
- regional failover with insufficient standby capacity;
- duplicated callback or queue replay;
- replayed payment/economic action;
- return to traffic before policy/authority validation;
- failback before replication/reconciliation converges;
- provider fallback that changes behavior or data handling.

Recovery readiness is a demonstrated property of the whole workflow, not a checkbox on a storage service.