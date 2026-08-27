# Agent Dependency, Vendor & Supply-Chain Operations

Autonomous businesses are only as reliable as the external systems behind their paid outcomes.

A production agent may depend on models, APIs, MCP servers, data providers, cloud infrastructure, payment rails, other agents, package ecosystems, identity providers, observability systems, and human review vendors. Any one of them can fail, change behavior, alter pricing, revoke access, introduce unsafe outputs, or become compromised.

The operating goal is not to eliminate dependencies. It is to make every important dependency **known, bounded, observable, substitutable, and economically justified**.

> Core principle: never let an upstream change silently become a customer-facing failure.

## 1. Start with the paid outcome

Do not inventory dependencies by vendor name alone. Begin with the outcome customers pay for.

For each paid capability, record:

- customer-visible outcome,
- acceptance criteria,
- deadline or latency promise,
- security/privacy constraints,
- geographic or regulatory constraints,
- maximum delivery cost,
- critical external dependencies,
- fallback path,
- degraded mode,
- customer communication trigger.

Example:

```yaml
capability: invoice_reconciliation
customer_outcome: reconciled ledger with exceptions
slo:
  success_rate: 99.5%
  p95_completion_minutes: 15
constraints:
  region: US
  pii: true
  max_cost_per_success: 2.40
critical_dependencies:
  - model: reasoning_provider_primary
  - api: accounting_connector
  - data: fx_reference_feed
fallbacks:
  - reasoning_provider_secondary
  - manual_exception_queue
degraded_mode: reconcile_non_fx_items_only
```

This ties supply-chain risk to revenue instead of maintaining a disconnected vendor spreadsheet.

## 2. Build a dependency graph

Maintain a machine-readable graph that answers:

1. What does this business depend on?
2. Which customer outcomes depend on each component?
3. What happens if that component disappears right now?

Track at least:

- models and model gateways,
- tool/API providers,
- MCP servers,
- A2A services and delegated agents,
- cloud/runtime services,
- package/runtime dependencies,
- identity/authentication providers,
- storage/vector/search systems,
- data sources,
- payment and settlement rails,
- notification channels,
- observability systems,
- human-review vendors.

Recommended fields:

```yaml
id: accounting-api-prod
kind: external_api
provider: example_vendor
capabilities:
  - fetch_transactions
  - create_adjustment
criticality: tier_1
owner: finance-platform
regions:
  - us-east
contract_version: 2026-07
api_version: v4
commercial_model: per_request
data_classes:
  - customer_financial_data
permissions:
  - read_transactions
  - write_adjustments
fallbacks:
  - accounting-api-secondary
change_monitors:
  - status_page
  - docs_diff
  - price_diff
  - terms_diff
last_qualified_at: 2026-08-01
```

The graph should support reverse lookup: `dependency -> affected capabilities -> affected customers -> revenue at risk`.

## 3. Classify criticality

Use a small number of dependency tiers.

### Tier 0 — safety/control-plane

Failure may create unauthorized actions, uncontrolled spend, data exposure, or inability to stop the system.

Examples:

- identity provider,
- permission service,
- secrets manager,
- policy engine,
- payment authorization control,
- kill-switch infrastructure.

Requirements:

- deterministic fail-closed behavior,
- strong redundancy where practical,
- tested recovery procedures,
- short detection windows,
- explicit ownership.

### Tier 1 — revenue-critical

Failure directly prevents delivery of an important paid outcome.

Requirements:

- measured SLO,
- fallback or degraded mode,
- capacity assumptions,
- incident escalation,
- customer-impact mapping.

### Tier 2 — quality-critical

Failure degrades quality or efficiency but does not fully block delivery.

Requirements:

- observable degradation,
- bounded customer impact,
- acceptable temporary substitute.

### Tier 3 — convenience

Failure is operationally annoying but not material to customer outcomes.

Do not spend Tier-0 engineering effort on Tier-3 dependencies.

## 4. Measure blast radius

For every critical dependency, calculate the likely blast radius.

Useful dimensions:

- percentage of paid workflows affected,
- percentage of revenue affected,
- number of tenants affected,
- data classes exposed,
- regions affected,
- irreversible actions exposed,
- fallback capacity available,
- estimated recovery time.

A simple dependency risk score:

```text
risk exposure = probability of material failure
              × customer impact
              × duration
              × irreversibility multiplier
```

Track concentration separately:

```text
provider concentration = revenue dependent on provider / total revenue
```

A provider with excellent uptime can still be dangerous if 95% of revenue depends on it and replacement takes three months.

## 5. Qualify vendors before production use

A dependency is not production-ready because its demo worked.

Evaluate five dimensions.

### Capability

- Does it satisfy the required semantic outcome?
- Is behavior stable across representative inputs?
- Are outputs structured enough to validate?
- Are edge cases documented?

### Reliability

- Published availability and rate limits,
- capacity behavior under bursts,
- timeout and retry semantics,
- regional behavior,
- incident history,
- support escalation.

### Security

- authentication and authorization model,
- least-privilege support,
- secret handling,
- signing/integrity controls,
- vulnerability disclosure process,
- auditability,
- data isolation.

### Legal/data

- data-use terms,
- retention,
- training on customer data,
- subprocessors,
- residency,
- deletion support,
- IP/licensing rights.

### Economics

- pricing unit,
- minimum commitments,
- burst pricing,
- egress/hidden costs,
- price-change terms,
- expected cost per successful outcome.

Qualification should produce an explicit decision: `approved`, `approved_with_limits`, `evaluation_only`, or `blocked`.

## 6. Treat MCP servers and agent tools as live dependencies

Agent supply chains differ from classic package supply chains because tools and agent capabilities may be discovered or modified at runtime.

For externally supplied tools:

- pin or record publisher identity,
- record exact tool schema/version,
- verify provenance when possible,
- review requested permissions,
- reject unexpected capability expansion,
- sandbox high-risk execution,
- treat tool descriptions and outputs as untrusted input,
- retain invocation evidence,
- continuously re-evaluate trust.

Do not let a new tool description grant itself more authority.

A tool may be functionally compatible while becoming security-incompatible.

## 7. Detect dependency drift

A supplier can remain online while becoming materially different.

Monitor for changes in:

- model behavior,
- latency,
- refusal policy,
- tool schema,
- API version,
- authentication requirements,
- rate limits,
- pricing,
- terms of service,
- data retention,
- training policy,
- supported regions,
- safety controls,
- package or artifact hashes,
- ownership/publisher identity.

Classify change events:

```text
informational -> review later
compatible     -> validate in normal release process
material       -> run regression suite before production
breaking       -> block rollout or invoke migration plan
security       -> quarantine immediately
```

A status page cannot detect semantic drift. Use synthetic transactions and outcome evals.

## 8. Version dependency evidence

Every important execution should be explainable after the fact.

Record:

- provider,
- model/tool/API identifier,
- version or release,
- schema version,
- configuration hash,
- routing decision,
- fallback decision,
- price version,
- execution region,
- relevant policy version.

This lets you answer:

> Which upstream dependency produced this customer-visible result?

Without that evidence, debugging, claims, audits, and vendor disputes become guesswork.

## 9. Design fallbacks around semantics

Do not write fallback logic as:

```text
if ProviderA fails -> use ProviderB
```

Instead define the required contract:

```yaml
required_capability: classify_claim
semantic_requirements:
  precision_floor: 0.96
  structured_output_schema: claim-v3
  pii_processing: allowed
  region: US
commercial_constraints:
  max_cost_per_success: 0.40
operational_constraints:
  p95_latency_ms: 2500
```

Then choose any provider that satisfies the contract.

Provider substitution must preserve:

- permissions,
- data policy,
- output semantics,
- safety requirements,
- latency budget,
- cost ceiling,
- contractual commitments.

A technically available fallback can still be commercially or legally invalid.

## 10. Use graceful degradation

Not every failure requires total shutdown.

Possible degraded modes:

- read-only instead of write actions,
- lower concurrency,
- cheaper/slower model tier,
- partial workflow completion,
- stale-but-bounded cached data,
- human-review queue,
- deferred non-critical work,
- reduced feature set.

Every degraded mode should have:

- entry condition,
- customer-visible effect,
- maximum duration,
- exit condition,
- owner,
- data/safety restrictions.

Never degrade silently across a promise the customer paid for.

## 11. Bound retries and failover storms

An upstream outage can become your outage amplifier.

Common failure pattern:

```text
provider slows
-> every request retries
-> fallback receives sudden traffic spike
-> fallback rate-limits
-> queues grow
-> spend rises
-> entire service collapses
```

Controls:

- bounded retries,
- exponential backoff with jitter,
- circuit breakers,
- retry budgets,
- concurrency caps,
- fallback capacity reservations,
- admission control,
- customer-tier prioritization.

Measure failover capacity before you need it.

## 12. Set supplier SLOs

For critical dependencies, define internal supplier SLOs even if the vendor does not.

Examples:

- availability,
- valid response rate,
- semantic success rate,
- p95 latency,
- freshness,
- error-budget burn,
- data-integrity failures,
- price variance,
- change-notification lead time.

Customer SLOs should be stricter than blind faith in vendor SLAs.

A vendor can meet a 99.9% uptime SLA while failing your specific workflows repeatedly.

## 13. Monitor data dependencies as products

Data sources fail differently from APIs.

Track:

- freshness,
- completeness,
- duplicate rate,
- schema drift,
- correction frequency,
- lineage,
- licensing,
- redistribution rights,
- deletion obligations,
- geographical scope.

Use freshness budgets:

```yaml
source: merchant-risk-feed
max_age_minutes: 20
stale_behavior: block_high_risk_actions
fallback: manual_review
```

Never let stale external knowledge masquerade as current authoritative state.

## 14. Manage model-provider drift

Model upgrades are dependency changes even when the API name stays the same.

Regression-test:

- task success,
- structured-output validity,
- tool selection,
- refusal behavior,
- hallucination rate,
- safety behavior,
- token use,
- latency,
- cost per successful outcome.

For high-value workflows, pin versions where possible and require staged promotion.

Do not auto-adopt a “better” model without proving it is better for your business workflow.

## 15. Control concentration risk

Diversification has value only when alternatives are genuinely independent and usable.

Track:

```text
revenue concentration by provider
workflow concentration by provider
spend concentration by provider
regional concentration
data-source concentration
control-plane concentration
```

Watch for fake diversification:

- two providers running on the same underlying cloud,
- two APIs backed by the same model,
- two data vendors sourcing the same upstream dataset,
- multiple tools owned by one company,
- multiple gateways sharing one authentication dependency.

Document common-mode failure explicitly.

## 16. Decide when redundancy is worth paying for

Redundancy should be an economic decision.

Estimate:

```text
annual expected outage loss
= probability-weighted downtime
× revenue/customer impact
```

Compare with:

```text
annual redundancy cost
= standby fees
+ duplicated engineering
+ reserved capacity
+ testing
+ operational complexity
```

Pay for redundancy when expected avoided loss, strategic leverage, or contractual necessity exceeds the cost.

Do not build multi-provider complexity for workflows with trivial downside.

## 17. Keep vendor leverage

Operational substitutability improves commercial leverage.

Useful practices:

- avoid proprietary coupling unless it creates real customer value,
- maintain export paths,
- preserve canonical internal schemas,
- isolate vendor-specific adapters,
- periodically test alternative suppliers,
- know switching time and migration cost,
- negotiate change-notification windows.

A dependency you cannot replace has bargaining power over your margin.

## 18. Define change windows and canaries

For material dependency changes:

1. detect the upstream change,
2. reproduce it in a controlled environment,
3. run semantic regression evals,
4. test economic impact,
5. canary a small traffic slice,
6. compare against the previous dependency state,
7. expand only when guardrails hold,
8. retain rollback capability.

Track outcome-level metrics, not only HTTP errors.

## 19. Propagate incidents by dependency graph

When an upstream dependency fails, incident tooling should immediately answer:

- which workflows are affected,
- which customers are affected,
- which regions are affected,
- what fallback exists,
- whether fallback capacity is sufficient,
- whether irreversible actions should stop,
- whether customers must be notified.

A dependency incident should create structured events that downstream systems can consume.

Example:

```json
{
  "dependency": "primary-reasoning-provider",
  "severity": "major",
  "affected_capabilities": ["claims-review", "contract-analysis"],
  "fallback_status": "capacity_limited",
  "customer_impact": "elevated_latency",
  "action": "throttle_low_priority_work"
}
```

## 20. Prepare emergency replacement runbooks

For Tier-0 and Tier-1 dependencies, maintain a tested replacement plan.

Include:

- trigger for emergency substitution,
- approved alternatives,
- credentials and permissions process,
- schema adapter,
- data migration requirements,
- regression suite,
- traffic migration steps,
- rollback,
- customer communication,
- commercial owner,
- post-incident reconciliation.

Test the runbook before the emergency.

A fallback that has not processed realistic production traffic is a hypothesis.

## 21. Control supplier permissions

External dependencies should receive only the minimum access needed.

Prefer:

- per-provider credentials,
- scoped tokens,
- short-lived credentials,
- tenant-aware authorization,
- read-only defaults,
- separate staging credentials,
- no shared administrator tokens,
- explicit approval for irreversible writes.

If a vendor is compromised, your permission model determines the blast radius.

## 22. Quarantine suspicious dependencies

Quarantine when you observe:

- publisher identity mismatch,
- unexpected tool/schema expansion,
- integrity/signature failure,
- unexplained outbound traffic,
- permission escalation,
- anomalous data access,
- sudden semantic changes,
- compromised credentials,
- security advisory affecting your usage.

Quarantine means:

1. stop new high-risk invocations,
2. preserve evidence,
3. rotate affected credentials,
4. switch to safe mode/fallback,
5. assess past executions,
6. notify affected owners/customers when required.

Do not keep a suspicious dependency live because switching is inconvenient.

## 23. Track dependency economics

Attribute costs at the workflow and supplier level.

Metrics:

- cost per request,
- cost per successful outcome,
- retry cost,
- fallback premium,
- standby capacity cost,
- provider-specific gross margin,
- price-change exposure,
- migration cost,
- outage cost.

Useful question:

> If this supplier raises prices 40% tomorrow, which customers become unprofitable?

The answer should be queryable, not guessed.

## 24. Run supply-chain evals

At minimum test these scenarios:

### Provider outage

- primary returns errors,
- primary times out,
- primary partially degrades.

Expected: bounded retries, correct failover, no storm.

### Rate-limit shock

Expected: admission control and graceful degradation preserve priority workloads.

### Silent model drift

Expected: semantic regression metrics detect quality change before broad rollout.

### Tool poisoning

A third-party tool returns adversarial instructions or altered metadata.

Expected: outputs remain untrusted; authority does not expand.

### Tool schema expansion

Expected: unexpected new write capability is blocked pending review.

### Stale data

Expected: freshness policy triggers safe behavior.

### Pricing shock

Expected: spend controls, margin alerts, and routing policy respond.

### Credential compromise

Expected: affected dependency can be disabled and credentials rotated quickly.

### Fallback incompatibility

Expected: contract validation blocks unsafe substitution.

### Common-mode failure

Primary and fallback fail together.

Expected: degraded mode or customer-visible stop, not uncontrolled retries.

## 25. Dashboard the supply chain

A useful operator view includes:

- critical dependencies by tier,
- dependency health,
- customer revenue at risk,
- provider concentration,
- fallback readiness,
- last successful failover test,
- semantic drift alerts,
- pricing changes,
- security advisories,
- data freshness,
- error-budget burn,
- unresolved vendor-risk exceptions.

Do not optimize for number of monitored vendors. Optimize for reduction of unbounded customer risk.

## 26. Supplier review cadence

Suggested cadence:

### Continuous

- availability,
- latency,
- semantic health,
- integrity anomalies,
- freshness,
- spend.

### Weekly

- incident review,
- error-budget burn,
- new advisories,
- price anomalies.

### Monthly

- concentration,
- fallback readiness,
- contract exceptions,
- dependency graph accuracy.

### Quarterly

- requalification of critical suppliers,
- emergency replacement exercise,
- commercial renegotiation,
- permission review,
- data/terms review.

## 27. Supplier scorecard

Use a simple scorecard:

| Dimension | Measure |
|---|---|
| Outcome quality | successful outcomes / attempts |
| Reliability | SLO attainment and error-budget burn |
| Security | unresolved critical findings and permission scope |
| Change discipline | breaking changes and notification quality |
| Data governance | retention, deletion, provenance, residency |
| Economics | cost per successful outcome and price volatility |
| Support | incident response and escalation quality |
| Portability | tested switching time and migration complexity |

Do not collapse everything into one opaque score. Keep the underlying dimensions visible.

## 28. Customer communication triggers

Define communication rules before incidents.

Notify when:

- contractual SLO is likely to be missed,
- customer data may be affected,
- material behavior changes,
- regulated workflow constraints change,
- prolonged degraded mode is active,
- an irreversible action may be wrong,
- the customer must take action.

Avoid both silence and noisy status spam.

## 29. Business opportunities

The explosion of agent businesses creates new supply-chain infrastructure categories.

### Agent dependency observability

Map runtime dependencies to paid outcomes and show blast radius in real time.

### Semantic failover gateways

Route between providers based on capability contracts, policy, quality, and economics rather than brand-specific APIs.

### Agent supplier certification

Continuously evaluate MCP servers, agents, data sources, and tools for integrity, permissions, reliability, and behavioral drift.

### Machine-readable vendor risk

Expose structured trust, data, security, region, pricing, and operational metadata consumable by autonomous procurement agents.

### Dependency change intelligence

Monitor documentation, schemas, pricing, terms, status, and model behavior and convert change into actionable alerts.

### Agent SBOM / capability bill of materials

Maintain a live bill of external capabilities used in each agent workflow, including runtime-discovered tools and agents.

### Supply-chain attack detection

Detect publisher impersonation, capability injection, tool poisoning, suspicious permission growth, and compromised agent dependencies.

### Multi-provider economic routing

Optimize cost per successful outcome while respecting semantics, policy, residency, capacity, and reliability constraints.

### Vendor-risk automation

Automate qualification evidence, reassessments, contract exceptions, and replacement readiness for agent-heavy companies.

## 30. Minimum viable dependency operations

A small agent startup does not need enterprise vendor-management bureaucracy.

It does need:

- a dependency list,
- criticality tiers,
- one owner per critical dependency,
- health monitoring,
- cost tracking,
- version/provenance evidence,
- one safe fallback or degraded mode for revenue-critical dependencies,
- tested credential revocation,
- a basic replacement runbook.

That is enough to prevent many catastrophic surprises.

## 31. Launch checklist

Before a critical external dependency handles production customer work:

- [ ] Paid outcomes depending on it are identified.
- [ ] Criticality tier is assigned.
- [ ] Provider, version, schema, permissions, and data classes are recorded.
- [ ] Qualification has been completed.
- [ ] Security and data-use constraints are acceptable.
- [ ] Cost per successful outcome is measured.
- [ ] Health and semantic drift are monitored.
- [ ] Pricing and contract changes are monitored.
- [ ] Retry behavior is bounded.
- [ ] Fallback or degraded mode is defined.
- [ ] Fallback semantics and capacity are tested.
- [ ] Credential revocation is tested.
- [ ] Blast radius is queryable.
- [ ] Incident communication triggers are defined.
- [ ] Emergency replacement runbook exists.

## 32. Operating principle

Treat every external capability as a supplier to a customer promise.

The winning agent businesses will not be those with zero dependencies. They will be those that can adopt the best models, tools, data, and agent services quickly **without surrendering control of reliability, security, margin, or customer trust**.

Build the supply chain so dependencies can change without the business becoming unknowable.