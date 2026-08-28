# Agent Data Residency, Sovereignty, and Cross-Region Processing

Agent businesses need to answer more than **where is the database?** A production agent can move customer information through model inference, retrieval, memory, queues, telemetry, identity/governance systems, backups, support tooling, and disaster-recovery paths. Each layer can have a different geography.

Use this playbook to turn residency promises into an evidence-backed operating contract. It is an engineering and evidence framework, not legal advice.

## Core rule

**Never infer end-to-end residency from a resource name, account geography, storage-region setting, or provider marketing page.** Prove every material data path independently.

Residency status also does not grant authority to process sensitive data or transfer it across borders. Authority, purpose, minimization, and legal basis remain separate controls.

## Lifecycle

`inventory -> requirements_mapped -> architecture_selected -> configured -> tested -> active -> changed -> suspended -> retired`

A material provider, endpoint, telemetry, subprocessor, backup, support, or failover change moves the record back to `changed` until reviewed and re-tested.

## Map the whole data plane

For each material path record:

- data class and tenant/customer scope;
- origin and destination component;
- storage region;
- inference/processing region;
- routing mode: regional, multi-region, global, or unknown;
- replication and failover regions;
- telemetry/log destination;
- control-plane or identity/governance destination;
- backup/DR location;
- human support/admin geography when material;
- provider/subprocessor and endpoint;
- requirement that applies; and
- current technical and contractual evidence.

At minimum inspect prompts and responses, files, retrieval/vector indexes, long-term memory, queues, tool/MCP payloads, billing events, audit evidence, incident tooling, analytics, support data, backups, and recovery replicas.

## Separate claims that are often conflated

| Claim | What it means | What does **not** prove it |
|---|---|---|
| At-rest residency | durable stored bytes stay in allowed geography | model endpoint location |
| Processing residency | inference/transform processing stays in allowed geography | database region |
| Routing residency | transit and dynamic routing stay within allowed boundary | hostname containing a region |
| Telemetry residency | traces/logs/analytics stay in allowed geography | application data residency |
| Control-plane residency | inventory/governance/identity metadata stays in allowed geography | workload region |
| Backup/DR residency | replicas and restoration targets stay allowed | primary-region configuration |
| Support sovereignty | administrative access meets personnel/location restrictions | data-center region |

## Endpoint and provider selection

Treat routing semantics as part of the contract.

- `regional`: one explicitly scoped region; verify service-specific guarantees.
- `multi_region`: bounded geography containing multiple regions; document the allowed set.
- `global`: dynamic routing with no region guarantee unless the provider explicitly states otherwise. Never use for a tenant requiring region pinning.
- `unknown`: fail closed for constrained workloads.

A provider/model switch is a residency change until proven otherwise. The commercial brand can remain the same while the underlying processing geography changes.

## Resilience without silent residency violations

Business continuity and residency must agree. For every failover target, prove that its storage, processing, telemetry, control-plane, backup, and support paths still satisfy the tenant requirement.

A recovery plan that restores availability by routing constrained data through a prohibited geography is not a valid recovery plan. If no compliant failover exists, define the degraded or suspended mode explicitly.

## Sovereignty beyond geography

Some customers require controls beyond region pinning. Record only those that actually apply, such as:

- customer-managed or locally controlled key custody;
- administrative personnel-location restrictions;
- local operator or support requirements;
- isolated identity, billing, or metadata boundaries;
- disconnected or air-gapped operation;
- restricted cross-border support escalation.

Do not label a workload “sovereign” from geography alone.

## Verification plan

Use multiple evidence classes when material:

1. **Configuration evidence** — endpoint, resource, storage, logging, replication, backup and failover configuration.
2. **Runtime evidence** — provider region headers/receipts, audit logs, routing observations or synthetic probes when available.
3. **Storage/export inspection** — destination buckets, vector stores, backups, log sinks and recovery replicas.
4. **Provider/service documentation** — current service-specific residency semantics, not generic cloud marketing.
5. **Contractual evidence** — customer commitment, DPA/order form, subprocessor terms or approved exception.

Evidence freshness matters because region support and provider routing change.

## Activation gate

`active` requires all of the following:

- every material data path has a known routing mode and processing/storage geography;
- each constrained path is inside its allowed geography;
- no constrained path uses a global endpoint;
- telemetry, control-plane, backup, support, and failover paths are reviewed rather than assumed;
- provider/subprocessor locations are resolved;
- current evidence supports technical configuration and the applicable requirement;
- failover has no unresolved disallowed region;
- no material location uncertainty remains; and
- activation authority is separately evidenced.

Unknown material geography fails closed to `changed` or `suspended`.

## Change triggers

Re-review when any of these change:

- model or model provider;
- endpoint or routing mode;
- region or multi-region set;
- vector store, memory, queue, analytics, log or backup service;
- identity/governance integration;
- subprocessor;
- support path;
- DR/failover target;
- customer residency requirement; or
- provider residency documentation/terms.

## Metrics

Track at least:

- residency-policy violations;
- unknown-region events;
- constrained requests sent to global endpoints;
- cross-region failovers;
- provider/subprocessor changes;
- telemetry or backup placement drift;
- affected tenants; and
- time to detect and remediate drift.

## Failure modes to test

- region pinning asserted only from marketing copy;
- global endpoint under a regional guarantee;
- hidden telemetry/control-plane export;
- provider switch without re-review;
- DR failover into disallowed geography;
- backup outside the allowed region;
- unknown subprocessor location;
- tenant A residency policy leaking onto tenant B;
- support/admin path ignored;
- resource-name or UI-region inference treated as evidence; and
- `active` while a material location is unknown.

## Portable record

Start with `templates/DATA_RESIDENCY_RECORD.json`, validate with:

```bash
python scripts/validate_data_residency.py templates/DATA_RESIDENCY_RECORD.json
```

The public record must not contain credentials, private keys, raw prompts, private customer data, encryption keys, or unpublished legal advice. Use references to private evidence where necessary.
