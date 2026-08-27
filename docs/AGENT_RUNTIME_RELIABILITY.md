# Agent Runtime, Deployment, Capacity & Reliability Engineering

An agent business can have a validated offer, clean contracts, good evals, and perfect billing—and still fail commercially because autonomous demand hits the runtime in ways the founder never designed for.

Agent workloads are unusually hostile to naive production architectures. They can be long-running, bursty, retry-heavy, dependent on stochastic models, fan out across tools and other agents, pause for human review, and create real-world side effects that must not be duplicated. Reliability therefore means more than process uptime. It means delivering the promised outcome within explicit cost, latency, safety, and semantic bounds even when dependencies fail.

The operating principle for this guide is simple:

> **Use the simplest runtime that can meet measured demand and explicit customer promises. Add queues, durable execution, failover, and distributed-systems machinery only when a concrete failure mode or SLO requires them.**

---

## 1. Start from the commercial promise

Do not begin capacity planning with CPU, requests per second, or token throughput. Begin with the outcome the customer believes they bought.

For each capability define:

- the successful outcome,
- maximum acceptable end-to-end latency,
- maximum acceptable failure rate,
- whether partial completion has value,
- whether duplicate execution is harmful,
- whether a human can intervene,
- maximum delivery cost per successful outcome,
- data residency or regional constraints,
- recovery expectations after a dependency failure,
- and which degraded modes are acceptable.

Example:

```yaml
capability: reconcile_invoice_batch
success_definition: "all eligible invoices reconciled and exceptions surfaced"
latency_slo: "95% within 10 minutes"
availability_target: "99.5% successful accepted jobs"
max_cost_per_success: 2.50 USD
duplicate_side_effect_tolerance: none
human_escalation_after: 2 failed recovery attempts
acceptable_degradation:
  - "use secondary model for classification"
  - "delay non-urgent enrichment"
not_acceptable:
  - "skip financial validation"
  - "send duplicate payment instruction"
```

A runtime architecture is good only if it makes these promises measurable and enforceable.

---

## 2. Choose the minimum viable execution model

### Synchronous request/response

Use when:

- work reliably completes inside the client timeout,
- the action is cheap enough to retry safely,
- there is little fan-out,
- no long human wait is involved,
- and losing in-flight work is acceptable or trivially recoverable.

Good examples: classification, short retrieval, lightweight transformation, quote calculation.

Avoid using synchronous execution just because it is easy if the workflow regularly exceeds tens of seconds, invokes several unreliable dependencies, or performs costly side effects.

### Queued asynchronous job

Use when:

- request latency is shorter than execution latency,
- demand arrives in bursts,
- concurrency must be bounded,
- downstream quotas are tight,
- or callers can poll/webhook for completion.

The queue becomes a pressure buffer. It does not automatically make the workflow reliable; you still need idempotency, retry policy, visibility into age/backlog, and dead-letter handling.

### Event-driven workflow

Use when:

- distinct systems own different stages,
- stages should evolve independently,
- work can proceed from durable events,
- or multiple consumers need the same state transition.

Do not create an event bus merely to make the architecture look sophisticated. Event-driven systems increase debugging and ordering complexity.

### Durable workflow / state machine

Use when:

- execution spans minutes, hours, or days,
- humans may approve or supply missing information,
- restarting from the beginning would duplicate expensive work,
- exactly- or effectively-once side effects matter,
- multiple retries/fallbacks must be coordinated,
- or the execution history itself is commercially useful evidence.

A durable workflow should checkpoint enough state to resume from the last known-good boundary rather than repeating the entire trajectory.

### Scheduled/batch execution

Use when:

- work is not interactive,
- freshness has a predictable window,
- batching improves economics,
- or downstream systems prefer controlled bursts.

Batching can dramatically lower model/tool cost, but do not let hourly batching violate a customer promise that implies continuous monitoring.

---

## 3. Separate stateless compute from authoritative workflow state

Treat the worker process as disposable whenever possible.

Persist authoritative state outside free-form agent memory:

- workflow ID,
- current stage,
- accepted input version,
- completed step outputs or references,
- side-effect receipts,
- retry counters,
- deadlines,
- delegated authority/budget,
- pricing/entitlement snapshot if relevant,
- and terminal status.

Agent memory may help reasoning, but it should not be the only place that knows whether a payment was already initiated or an email was already sent.

A crash should be recoverable from durable state without asking a model to infer what probably happened.

---

## 4. Design every side effect for replay

Retries are inevitable. Duplicate side effects do not have to be.

For every tool or external action classify it as:

1. **Naturally idempotent** — repeated execution produces the same state.
2. **Idempotent with a key** — caller supplies a stable operation ID and the service stores/returns the first result.
3. **Compensatable** — duplicate or partial execution can be reversed with a defined compensating action.
4. **Non-repeatable/high-risk** — requires preflight checks, explicit confirmation, or manual recovery.

Generate idempotency keys from stable workflow identity, not a random value created on each retry.

Example:

```text
idempotency_key = hash(workflow_id + step_name + business_object_id + semantic_version)
```

Persist the side-effect receipt before declaring a step complete.

For financial, messaging, fulfillment, credential, and legal-signature actions, test replay behavior explicitly.

---

## 5. Use retry budgets, not infinite optimism

A retry policy should answer five questions:

- Which errors are transient?
- How many attempts are economically justified?
- How long should the delay be?
- What happens when retries are exhausted?
- Which global limit prevents a provider outage from multiplying traffic?

Use exponential backoff with jitter for shared dependencies. Cap both attempts and total retry time.

Track a **retry budget** at multiple levels:

- per step,
- per workflow,
- per tenant,
- per dependency,
- and globally.

Example:

```yaml
retry_policy:
  transient_errors:
    - rate_limit
    - gateway_timeout
    - provider_unavailable
  max_attempts_per_step: 3
  max_attempts_per_workflow: 8
  max_retry_elapsed: 15m
  backoff: exponential_with_jitter
  global_provider_retry_share: 10%
```

If the upstream provider is failing for everyone, unlimited retries turn one outage into two outages: theirs and yours.

Do not retry deterministic validation failures, permission denials, schema incompatibility, exhausted budgets, or confirmed harmful requests.

---

## 6. Build backpressure before autoscaling

Autonomous callers may generate load faster than you should accept it.

Backpressure means deliberately slowing or rejecting new work when downstream capacity is constrained.

Useful controls:

- bounded queues,
- per-tenant concurrency limits,
- global in-flight limits,
- provider-specific token/request budgets,
- admission control by customer tier,
- cost-based admission control,
- deadline-aware scheduling,
- queue-age limits,
- load shedding for low-value optional work.

A system that accepts everything and times out later provides worse service than one that rejects excess demand clearly and early.

Return machine-readable capacity failures where agent callers can react safely:

```json
{
  "status": "capacity_limited",
  "retry_after_seconds": 45,
  "accepted": false,
  "charged": false,
  "alternative_tier": "deferred",
  "reason_code": "downstream_model_quota"
}
```

---

## 7. Budget concurrency across the whole workflow

A single accepted request can create many downstream operations.

Define concurrency for:

- incoming jobs,
- active workflows,
- model calls,
- browser sessions,
- code execution sandboxes,
- database-heavy steps,
- third-party API calls,
- child agents,
- and human-review queues.

Estimate fan-out:

```text
peak_downstream_calls
= accepted_workflows
× average_parallel_branches
× calls_per_branch
× retry_multiplier
```

A service that accepts 100 concurrent jobs may generate 2,000 downstream calls after fan-out and retries. Capacity planning must model amplification.

Prefer explicit semaphores or worker pools over hoping each dependency handles arbitrary concurrency.

---

## 8. Make timeouts hierarchical

A workflow deadline should be divided among its stages.

If the customer expects a result in 60 seconds, do not allow every dependency to wait 60 seconds independently.

Example:

```text
customer deadline: 60s
- admission + setup: 2s
- retrieval: 8s
- primary reasoning: 20s
- tool execution: 15s
- verification: 8s
- packaging/response: 2s
- reserve/fallback: 5s
```

Propagate remaining deadlines to child agents and tools. A child workflow should not start expensive work when only two seconds remain unless it has a realistic fast path.

For long-running workflows use explicit step deadlines plus an overall business deadline.

---

## 9. Checkpoint long-running work at economic boundaries

Checkpoint after work that is expensive, slow, externally visible, or difficult to reproduce.

Good checkpoint boundaries include:

- after a costly research pass,
- after an external data purchase,
- after a human approval,
- after a verified artifact is produced,
- before and after a side effect,
- after a child-agent result is accepted,
- and before a long waiting period.

Do not checkpoint every token or trivial transformation. Excessive state management adds latency, storage cost, and migration complexity.

A useful checkpoint should let the workflow answer:

- what completed,
- what remains,
- which inputs/version produced the result,
- whether the step can be safely replayed,
- and whether the result is still fresh enough to reuse.

---

## 10. Define graceful degradation explicitly

Reliability is not binary. Many agent capabilities can provide a lower-cost or lower-fidelity result safely during dependency problems.

Design degradation tiers before an incident.

Example:

| Tier | Behavior | Customer promise |
|---|---|---|
| Full | primary model + enrichment + verification | normal SLA |
| Reduced | fallback model, skip optional enrichment | slower or lower-detail response |
| Deferred | queue non-urgent work | completion by later deadline |
| Read-only | analyze but block external actions | safe continuity |
| Unavailable | reject before accepting/charging | explicit outage |

Never degrade by silently removing a safety, legal, financial, or accuracy control that the customer relies on.

A cheaper model is not a valid fallback if it violates a semantic invariant. Provider failover must be validated with capability-level evals, not only API compatibility.

---

## 11. Treat model/provider failover as a product change

Switching models can alter:

- tool-call behavior,
- structured-output reliability,
- refusal patterns,
- context limits,
- reasoning quality,
- latency,
- cost,
- hallucination rate,
- and safety behavior.

Maintain a tested fallback matrix:

```yaml
capability: contract_clause_extraction
primary: model_A
fallbacks:
  - model: model_B
    approved_for:
      - extraction
      - classification
    not_approved_for:
      - final_legal_recommendation
  - mode: human_review_queue
```

Before enabling automatic failover, run the same golden tasks and failure scenarios across primary and fallback paths.

Record which provider/model served each successful outcome so reliability and margin analysis can be joined later.

---

## 12. Isolate tenants and noisy neighbors

High-volume autonomous buyers can consume shared capacity quickly.

At minimum track and bound by tenant:

- concurrent workflows,
- queue depth,
- model/tool usage,
- retry consumption,
- spend,
- storage/memory footprint,
- human-review load,
- and error rate.

A single customer should not be able to exhaust the global retry budget, saturate the browser pool, or consume every downstream provider quota.

Use fair scheduling or explicit priority classes when premium SLAs justify it.

If enterprise customers require dedicated capacity, charge for the reserved resource and include the unused-capacity economics in pricing.

---

## 13. Capacity-plan from successful outcomes

Traditional throughput metrics are necessary but insufficient.

Track:

```text
successful_outcomes_per_hour
accepted_workflows_per_hour
in_flight_workflows
workflow_amplification_factor
model_calls_per_success
tool_calls_per_success
retry_calls_per_success
human_minutes_per_success
compute_cost_per_success
p95 and p99 outcome latency
```

Then model peak demand:

```text
required_effective_capacity
= expected_peak_successes
× resource_units_per_success
× safety_factor
```

Use measured percentiles rather than averages for long-tail agent workloads.

Capacity should be bounded by the scarcest dependency, which may be a third-party API quota or human-review team rather than compute.

---

## 14. Put spend limits into autoscaling

Autoscaling can preserve latency while destroying unit economics.

Every automatic scale decision should consider:

- remaining model/provider budget,
- downstream quota,
- customer revenue/entitlement,
- cost per successful outcome,
- current gross margin,
- and whether deferred execution is commercially acceptable.

Examples of safe guards:

- maximum workers per capability,
- maximum hourly model spend,
- maximum spend per tenant,
- maximum retry spend,
- model tier downgrade only when eval-approved,
- pause low-margin free-tier jobs during demand spikes,
- require approval before reserving expensive dedicated capacity.

Alert on both saturation and unexpectedly low utilization. Overprovisioned idle infrastructure is also a margin leak.

---

## 15. Separate liveness, readiness, and capability health

A healthy process can still deliver broken agent outcomes.

Use at least three health layers:

### Liveness

Can the runtime process execute at all?

### Readiness

Can it currently accept work given dependencies, quotas, configuration, and queue state?

### Capability health

Can it still perform the promised task correctly?

Capability health may include:

- a small synthetic task,
- schema validation,
- tool connectivity,
- retrieval freshness,
- model behavior check,
- policy engine check,
- and expected semantic invariant.

Do not run expensive full evals on every health probe. Use cheap canaries continuously and deeper evals periodically or during rollouts.

---

## 16. Define SLOs around customer outcomes

Infrastructure SLOs should support, not replace, commercial SLOs.

Useful agent-business SLOs:

- accepted-job success rate,
- successful outcome within deadline,
- duplicate side-effect rate,
- unverified-output rate,
- queue wait time,
- recovery success rate,
- cost-per-success ceiling compliance,
- human-escalation rate,
- semantic fallback success rate,
- and billing-to-delivery reconciliation rate.

Example:

```yaml
slo:
  indicator: "verified successful workflows completed within 10m"
  target: 99.0%
  window: 30d
```

Use an error budget to decide how aggressively to ship runtime changes. If the service is burning reliability budget quickly, prioritize stabilization over feature velocity.

Burn-rate alerts are more useful than a single threshold because they identify when a monthly reliability budget is being consumed too fast.

---

## 17. Trace one outcome across every dependency

Every accepted workflow should have a stable correlation ID propagated through:

- ingress,
- entitlement check,
- queue,
- orchestration,
- model calls,
- retrieval,
- tool calls,
- child agents,
- side effects,
- verification,
- billing meter,
- and final response.

Capture structured events rather than relying only on prose logs.

Minimum event fields:

```yaml
workflow_id:
tenant_id:
capability:
capability_version:
step:
attempt:
provider:
model:
start_time:
end_time:
status:
error_class:
cost:
input_reference:
output_reference:
side_effect_receipt:
trace_id:
```

Redact or reference sensitive inputs instead of dumping customer data into logs.

The goal is to reconstruct why an individual paid outcome succeeded, degraded, or failed.

---

## 18. Classify failures before recovering

Not all failures should trigger the same action.

Suggested taxonomy:

- **Transient infrastructure:** timeout, connection reset, provider 5xx → bounded retry.
- **Capacity:** quota, concurrency, saturated queue → delay, shed, or alternate capacity.
- **Compatibility:** schema/protocol mismatch → stop and surface actionable contract error.
- **Semantic quality:** output violates invariant → retry with changed strategy, fallback, or human review.
- **Authorization:** permission/mandate insufficient → stop and request approval.
- **Budget:** spend ceiling reached → stop, downgrade only if approved, or request more budget.
- **Safety/compliance:** policy violation → stop and escalate according to policy.
- **Business rule:** invalid customer state → deterministic failure, usually no retry.
- **Unknown:** capture evidence, cap attempts, and escalate rather than looping.

Recovery should be driven by classification, not by a blanket `try again` wrapper.

---

## 19. Use deployment patterns that limit blast radius

### Shadow

Run the new version on copied production inputs without allowing side effects. Compare outcome quality, latency, and cost.

### Canary

Route a small percentage of eligible traffic to the new version. Increase only while outcome SLOs remain healthy.

### Blue/green

Maintain old and new deployment environments so traffic can switch quickly. Useful when rollback must be fast and infrastructure changes are substantial.

### Feature flag

Gate behavioral changes independently of code deployment. Flags should have owners, expiry/removal plans, and safe defaults.

### Tenant allowlist

Roll out to internal/test tenants or opt-in customers before broad autonomous traffic.

A deployment is not successful because pods stayed alive. Compare successful-outcome rate, semantic evals, latency, retries, and margin before expanding.

---

## 20. Make rollback deterministic

For every production change know:

- the previous known-good artifact/configuration,
- how to switch back,
- whether workflow state is backward-compatible,
- how in-flight work will be handled,
- whether schemas/data migrations can be reversed,
- and which customer actions happened under the faulty version.

Agent systems often combine prompts, models, tools, policies, schemas, and code. Treat all of these as versioned deployment inputs.

Record a deploy manifest:

```yaml
release_id: 2026-08-27.3
code_sha: abc123
prompt_bundle: p17
policy_version: pol9
capability_contract: 4.2
primary_model: model_A
fallback_model: model_B
retrieval_index: kb_2026_08_27
```

Without this, reproducing an incident becomes guesswork.

---

## 21. Run reliability evals, not only quality evals

Your test suite should deliberately create runtime failures.

Scenarios:

- primary model times out,
- fallback model returns schema-valid but semantically different output,
- tool API returns 429 for ten minutes,
- queue backlog grows 20×,
- child agent disappears after accepting work,
- duplicate delivery event arrives,
- worker crashes after side effect but before checkpoint,
- database becomes slow,
- one tenant creates extreme fan-out,
- human approval never arrives,
- region loses a dependency,
- billing meter is delayed,
- clock/deadline is nearly exhausted,
- retrieval source is stale,
- credentials expire mid-workflow,
- global model spend limit is reached.

Evaluate whether the system:

- preserves authority and budget,
- avoids duplicate side effects,
- stays within retry limits,
- degrades only along approved paths,
- provides actionable failure information,
- preserves evidence,
- reconciles billing correctly,
- and recovers or terminates deterministically.

---

## 22. Practice fault injection carefully

Start in test environments, then controlled production canaries.

Useful injections:

- latency,
- dropped responses,
- dependency 5xx,
- rate limiting,
- worker termination,
- queue delay,
- malformed response,
- stale cache,
- unavailable region,
- and temporary credential failure.

Never inject destructive side effects into real customer workflows without explicit isolation and rollback safeguards.

The goal is not chaos for its own sake. It is evidence that known recovery paths actually work.

---

## 23. Maintain runbooks for the expensive failure modes

At minimum write concise runbooks for:

### Queue saturation

1. Confirm whether demand is legitimate or retry amplification.
2. Stop nonessential producers/retries.
3. Enforce admission limits.
4. Add capacity only if downstream quotas and economics allow it.
5. Communicate updated completion expectations.
6. Drain oldest/deadline-sensitive work first.

### Provider outage

1. Classify scope and affected capabilities.
2. Disable retries that would amplify load.
3. Activate eval-approved fallback or degraded tier.
4. Block unsafe semantic substitutions.
5. Preserve failed workflow state for resume.
6. Reconcile provider-specific costs and customer impact afterward.

### Latency regression

1. Identify the stage consuming the latency budget.
2. Compare current release/model/tool versions with known-good versions.
3. Shed optional enrichment.
4. Roll back if release-correlated.
5. Re-evaluate timeout allocation after recovery.

### Runaway cost

1. Freeze low-priority autonomous intake if necessary.
2. Find tenant/capability/provider driving spend.
3. Check retries, loops, fan-out, and model routing.
4. Enforce hard spend/concurrency ceilings.
5. Verify no duplicate customer charges occurred.
6. Reopen only with a tested guardrail.

### Partial regional failure

1. Determine which state and dependencies are region-bound.
2. Fail over only capabilities whose data/residency rules allow it.
3. Avoid duplicating in-flight side effects.
4. Reconcile workflow ownership before resuming.

---

## 24. Design regional failover from data constraints backward

Multi-region deployment is not automatically better.

Before adding it, answer:

- Can customer data legally move to the alternate region?
- Is workflow state replicated consistently enough to avoid duplicate ownership?
- Are secrets/credentials available safely?
- Are third-party dependencies region-independent?
- Can the fallback region sustain the workload economically?
- How is split-brain prevented?
- How are in-flight side effects reconciled?

For early-stage businesses, a tested backup/restore process plus transparent outage handling may be more appropriate than active-active complexity.

---

## 25. Treat downstream quotas as first-class capacity

Your effective capacity is constrained by the lowest relevant limit:

```text
effective capacity = min(
  compute capacity,
  model quota,
  tool API quota,
  browser/sandbox pool,
  database capacity,
  human review capacity,
  budget capacity
)
```

Track quota headroom continuously for dependencies that can block paid outcomes.

If a provider quota is the bottleneck, scaling your own worker fleet makes nothing faster and may increase failure/retry cost.

Negotiate higher limits only after measured demand justifies them.

---

## 26. Measure runtime economics per capability

Join reliability telemetry with the unit-economics model.

Per capability and tenant track:

```text
infrastructure_cost_per_success
model_cost_per_success
tool_cost_per_success
retry_cost_per_success
idle_reserved_capacity_cost
human_recovery_cost
failure_refund_or_credit_cost
margin_after_reliability_cost
```

Reliability has an economic optimum. Eliminating the last 0.01% of failures may cost more than customers value; tolerating frequent failures may destroy retention and reputation.

Price premium reliability tiers only when the underlying architecture can actually reserve or prioritize the promised resources.

---

## 27. Reliability tiers can be a product

Examples:

| Tier | Runtime treatment | Monetization |
|---|---|---|
| Best effort | shared queue, standard retry, no reserved capacity | base price |
| Priority | shorter queue target, higher concurrency share | premium usage/subscription |
| Reserved | dedicated or preallocated capacity, stronger SLA | committed annual spend |
| Regulated | region pinning, additional evidence/review controls | enterprise premium |

Do not sell an SLA that is merely a support promise. Map each commercial tier to real scheduling, capacity, redundancy, and escalation behavior.

---

## 28. Agent-to-agent traffic needs stronger admission control

Machine callers can react to errors much faster than humans and can accidentally synchronize into retry storms.

Publish machine-readable operational metadata when useful:

```yaml
capacity:
  max_concurrent_per_buyer: 20
  supports_async: true
  typical_latency_ms: 8500
  retry_after_supported: true
  idempotency_required: true
  max_job_duration: 2h
```

For autonomous buyers:

- require stable buyer identity where abuse matters,
- rate-limit by buyer and capability,
- expose `retry_after`,
- distinguish rejected from accepted work,
- never charge rejected work as completed usage,
- and prefer asynchronous callbacks for long-running tasks.

Protect high-value capacity from anonymous retry floods.

---

## 29. Keep the control plane boring

The runtime control plane should make execution more deterministic, not add another agent that improvises operational policy.

Good deterministic control-plane responsibilities:

- admission,
- queue assignment,
- concurrency limits,
- retry classification,
- workflow state transitions,
- deadlines,
- budget enforcement,
- routing among pre-approved fallbacks,
- health checks,
- release selection,
- and kill switches.

A reasoning agent may recommend a recovery path, but hard limits and authority boundaries should remain deterministic.

---

## 30. Minimal architecture by maturity

### Pre-revenue / manual pilot

Use:

- one deployable service,
- simple database,
- explicit request IDs,
- basic logs,
- hard spend limit,
- manual recovery.

Do not build a workflow engine because you hope demand arrives.

### Early paid usage

Add when needed:

- background queue,
- worker concurrency caps,
- idempotency keys,
- structured traces,
- basic SLOs,
- deployment rollback,
- provider fallback for proven critical paths.

### Repeated long-running workflows

Add:

- durable state/checkpoints,
- typed failure/recovery policy,
- dead-letter handling,
- human callback handling,
- workflow versioning,
- reliability evals.

### High-volume autonomous demand

Add based on measured bottlenecks:

- tenant isolation,
- admission control,
- fair scheduling,
- quota-aware routing,
- automated burn-rate alerts,
- capacity forecasting,
- regional strategies,
- reserved capacity tiers.

Complexity should follow revenue and observed failure modes.

---

## 31. Runtime launch checklist

Before exposing a capability to autonomous traffic:

- [ ] Successful outcome is defined independently of HTTP success.
- [ ] End-to-end latency and cost budgets are explicit.
- [ ] Execution model matches observed workflow duration and failure modes.
- [ ] Authoritative workflow state survives process restarts.
- [ ] Side effects have idempotency or compensation strategy.
- [ ] Retryable and non-retryable failures are classified.
- [ ] Retry attempts and global retry load are bounded.
- [ ] Concurrency is capped across scarce dependencies.
- [ ] Backpressure/admission behavior is machine-readable.
- [ ] Timeouts/deadlines propagate through child work.
- [ ] Long-running work checkpoints after expensive/irreversible stages.
- [ ] Fallback models/providers have semantic eval coverage.
- [ ] Degraded modes are explicitly approved.
- [ ] Per-tenant noisy-neighbor controls exist where needed.
- [ ] Autoscaling has spend and quota ceilings.
- [ ] Liveness, readiness, and capability health are distinct.
- [ ] Outcome-level SLOs and error budgets are defined.
- [ ] Trace IDs connect workflow, tools, verification, and billing.
- [ ] Deploy manifests version code, prompts, policy, models, and contracts.
- [ ] Rollback handles in-flight workflows safely.
- [ ] Fault scenarios are tested before production incidents.
- [ ] Queue saturation, provider outage, latency, and runaway-cost runbooks exist.
- [ ] Reliability costs feed back into pricing and margin analysis.

---

## 32. Reliability scorecard

Review weekly for each revenue-critical capability:

| Metric | Target | Actual | Action |
|---|---:|---:|---|
| accepted jobs successful | | | |
| successful within promised deadline | | | |
| duplicate side effects | 0 | | |
| p95 outcome latency | | | |
| queue p95 wait | | | |
| retries per success | | | |
| fallback activation rate | | | |
| fallback semantic success | | | |
| cost per success | | | |
| human recovery rate | | | |
| SLO error budget remaining | | | |
| top dependency quota headroom | | | |

A trend is more important than a one-off number. Investigate when retry rate, queue age, cost, or fallback use rises before customer-visible failure rate catches up.

---

## 33. Reliability business opportunities

As autonomous agents become customers of other agents, runtime reliability itself becomes a market.

Potential businesses:

### Durable execution for agents

Offer agent-native workflow persistence, replay, checkpoints, callback waits, idempotency, and traceability without requiring founders to build custom state machines.

### Capacity brokerage

Route agent workloads among model/tool providers based on quota, latency, price, residency, and semantic compatibility.

### Agent reliability certification

Continuously test capabilities against published failure scenarios and issue machine-readable reliability attestations for registries and buyers.

### Failure replay and debugging

Reconstruct stochastic multi-agent incidents from versioned prompts, models, tool calls, state, and side-effect evidence.

### Reliability-aware marketplace routing

Match buyers to providers based not only on advertised capability and price, but measured completion rate, deadline adherence, degradation behavior, and dispute history.

### Autonomous FinOps/runtime control

Enforce budgets, concurrency, routing, and margin targets in real time across agent workflows.

### Enterprise agent control plane

Provide policy-driven admission, deployment, regional routing, kill switches, workflow evidence, and SLO management across many internal/external agents.

The durable opportunity is not “more infrastructure.” It is making autonomous commercial promises reliably enforceable.

---

## 34. A practical reliability design review

Before approving a runtime design, answer these in order:

1. What exactly has the customer paid us to complete?
2. Which failures can prevent that outcome?
3. Which failures are most likely or most expensive?
4. Can the workflow safely restart from the beginning?
5. Which side effects must never duplicate?
6. Where is authoritative progress stored?
7. Which dependency is the true capacity bottleneck?
8. What is the maximum acceptable retry amplification?
9. What should happen when that dependency is unavailable?
10. Which degraded outcomes remain commercially acceptable?
11. What is the total cost ceiling per successful outcome?
12. Which telemetry lets us reconstruct a single failure?
13. Can the current release be rolled back without corrupting in-flight work?
14. Have we actually tested the failure path?

If those answers are concrete, the architecture is probably ready for the next level of traffic. If they are vague, adding more distributed-systems components will usually make the ambiguity harder to debug.

---

## Final principle

Agent reliability is the discipline of turning stochastic, failure-prone execution into a bounded commercial service.

The winning agent business is not the one with the most elaborate runtime. It is the one that can state what it promises, measure whether it delivered, survive expected failures without duplicate harm, keep cost inside the business model, and recover from the last known-good state with evidence.