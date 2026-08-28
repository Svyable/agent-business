# Agent Multi-Tenant Isolation, Quotas, and Per-Customer Operations

Agent businesses that serve many customers on shared infrastructure need a tenant operating contract, not just a `tenant_id` field. The identity that selects a customer boundary must survive every consequential hop: edge, orchestrator, model session, retrieval, memory, tools, queues, billing, observability, and release configuration.

Use this guide with `AGENT_CREDENTIAL_IDENTITY.md`, `AGENT_RUNTIME_RELIABILITY.md`, `AGENT_DATA_MEMORY_PROVENANCE.md`, `AGENT_BILLING_REVENUE_ASSURANCE.md`, `AGENT_RELEASE_CHANGE_MANAGEMENT.md`, and `AGENT_CUSTOMER_IMPLEMENTATION.md`.

## Non-negotiable invariant

**Tenant status does not grant authority, and prompt text is never authoritative tenant identity.** Resolve tenant context from an authenticated principal/session, bind it to execution context, and re-check it at every data or tool boundary.

A shared runtime may share compute. It must not accidentally share authorization, retrieval scope, memory namespace, cache keys, credentials, entitlements, billing attribution, or release configuration.

## Deployment modes

| Mode | Best when | Advantages | Costs / risks |
| --- | --- | --- | --- |
| Dedicated | regulated, high-value, custom-model, strict SLO tenants | strongest blast-radius, quota, data, and performance isolation | highest infrastructure and operations cost |
| Pooled | many similar tenants with modest load | utilization and cost efficiency | requires explicit tenant-aware controls at every shared layer |
| Hybrid | heterogeneous tiers or regulated subsets | spend isolation where it matters while retaining pooling elsewhere | more routing/configuration complexity |

Do not infer isolation quality from deployment mode alone. A dedicated model endpoint with a shared retrieval index can still leak data; a pooled runtime can be safe only when every relevant boundary is tenant-aware and tested.

## Tenant context propagation contract

Carry an immutable, authenticated tenant-context object internally. It should contain an opaque tenant reference, principal/session reference, service tier, region/residency decision, and applicable entitlement/policy version. Do not place sensitive customer identifiers in portable public records.

At minimum, enforce the context at:

1. edge authentication and request admission;
2. orchestration and sub-agent delegation;
3. model/session state and stored response handles;
4. retrieval security trimming and vector/document filters;
5. long- and short-term memory namespaces;
6. caches and reusable tool/model outputs;
7. tools, MCP servers, APIs, and credential selection;
8. queues, background jobs, retries, and callbacks;
9. metering, spend accounting, invoices, and credits;
10. traces, logs, metrics, alerts, and release/config selection.

If a downstream system cannot carry tenant context safely, treat that integration as a boundary requiring a broker, dedicated resource, or manual review—not as permission to drop context.

## Isolation patterns

Use the strongest practical boundary for the data class and risk:

- **Store-per-tenant:** strongest separation and simplest deletion story; higher operational overhead.
- **Namespace or partition:** practical for pooled systems when tenant filters are mandatory and centrally enforced.
- **Row/document security:** useful only when every query path, retrieval index, admin path, and background job respects it.
- **Security-trimmed retrieval:** apply authorized tenant/document scope before ranking or generation; never ask the model to filter leaked candidates after retrieval.
- **Memory scoping:** namespace memories by tenant and principal/workflow where needed; never rely on prompt prefixes.
- **Cache scoping:** tenant and entitlement/policy version belong in cache keys whenever cached content could differ by customer.

## Quotas and noisy-neighbor control

Edge rate limits are insufficient because expensive work can continue downstream after admission. Define per-tenant limits at consequential resource layers:

- requests and tokens at the AI/API gateway;
- active sessions and concurrency at runtime;
- model inference and context-cache consumption;
- retrieval/memory reads and writes;
- tool calls and external API concurrency;
- queue depth, background-job concurrency, and retry budgets;
- human-review capacity where it is scarce;
- daily/monthly spend or outcome-cost budgets.

Specify burst allowance, steady-state rate, concurrency, queue policy, backpressure, and what happens when a limit is reached. Premium tiers may receive reserved capacity or dedicated resources, but the behavior must match the commercial entitlement.

Run synthetic noisy-neighbor tests. A useful benchmark places one tenant at declared burst capacity while another sends a steady baseline. Record cross-tenant latency/error impact, starvation, quota enforcement, attribution correctness, and whether any access boundary was crossed. Pass/fail thresholds belong in the tenant record.

## Entitlements and tenant-specific releases

Keep model, tool, feature, data, and autonomy entitlements tenant-scoped. Shared infrastructure must not make a capability available merely because another tenant has purchased or approved it.

Release/configuration resolution should include tenant context. Canary cohorts, model versions, policy versions, feature flags, and tool sets need deterministic tenant targeting. Use `AGENT_RELEASE_CHANGE_MANAGEMENT.md` when a change can affect production behavior; a tenant-specific override is still a release/configuration decision.

## Cost attribution

Attribute direct costs before allocating shared overhead. Track, where material:

- inference and context-cache cost;
- tool/API consumption;
- storage, retrieval, and memory;
- retries and failed work;
- background jobs;
- human review/support;
- dedicated infrastructure;
- a documented shared-overhead allocation method.

Connect per-tenant cost to successful outcomes, not activity alone. This lets pricing and customer-success records distinguish a profitable tenant from one whose hidden retries, human review, or noisy workload destroy contribution margin.

## Per-tenant observability

At minimum, expose tenant-scoped metrics for latency, errors, throttles, queue delay, inference/token use, tool use, spend, cost per successful outcome, cross-tenant access denials, isolation-test results, release/config version, and SLO state. Do not place raw customer prompts or private data into public portable records.

Alert on missing tenant context as a security event. Aggregate dashboards are useful, but they must not be the only way to diagnose one tenant's degradation or cost anomaly.

## Onboarding and offboarding

Onboarding is complete only after tenant identity, isolation boundaries, quotas, entitlements, observability, billing attribution, and isolation tests are configured.

Offboarding must account for:

- disabling admission and revoking tenant-scoped credentials/tokens;
- disabling tools, callbacks, jobs, and scheduled work;
- exporting data when contractually required;
- deleting or retaining data/memory according to policy and evidence;
- clearing tenant-scoped caches and temporary artifacts where applicable;
- closing usage/metering and billing;
- retaining only the audit evidence the business is authorized or required to retain.

A closed CRM/customer-success record is not proof that technical access or data has been removed.

## Portable record and validator

Start with `templates/TENANT_OPERATIONS_RECORD.json`, governed by `schemas/tenant-operations-record.schema.json`, then run:

```bash
python scripts/validate_tenant_operations.py templates/TENANT_OPERATIONS_RECORD.json
```

The safe starter is intentionally `needs_review`, has no operational authority, and makes no verified isolation claim. Populate evidence before declaring a tenant operational or offboarded.

## Evidence that supports stronger claims

Good evidence includes current automated isolation-test output, policy/config snapshots without secrets, identity/authorization test results, quota test output, billing-reconciliation records, release/config evidence, deletion/revocation receipts, and externally verifiable platform documentation. Architecture intent or a diagram alone is not proof that isolation works.

## Failure-mode eval suite

Before production, test at least: missing tenant context; forged prompt/header tenant switch; cross-tenant retrieval; memory namespace collision; cache-key leakage; unauthorized tool routing; downstream quota bypass; burst/noisy-neighbor starvation; wrong-tenant usage attribution; tenant-specific release leakage; background job running after offboarding; and data/memory retention beyond the declared offboarding policy.
