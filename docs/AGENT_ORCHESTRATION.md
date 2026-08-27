# Agent Orchestration, Delegation & Multi-Agent Workflows

A multi-agent system is not automatically a better business system. Every additional agent adds coordination cost, latency, failure modes, authority edges, and debugging surface.

Use multiple agents only when specialization, concurrency, independent verification, market-style selection, or organizational separation creates more value than the coordination overhead.

> **Operating principle:** prefer the simplest architecture that reliably delivers the customer outcome.

## 1. Start with the business outcome, not the agent graph

Before adding agents, write down:

- the customer outcome,
- the acceptance criteria,
- the maximum acceptable latency,
- the maximum delivery cost,
- which actions are reversible,
- which actions require approval,
- and what evidence proves the outcome was delivered correctly.

Then ask whether one agent plus deterministic workflow code can satisfy those constraints.

### Single-agent default

Use one agent when:

- one context window can hold the important state,
- one policy boundary is sufficient,
- tasks are mostly sequential,
- specialization does not materially improve quality,
- a deterministic tool workflow can enforce the hard constraints,
- and failures are easier to localize in one trajectory.

### Multi-agent justification test

Add another agent only when at least one of these is true:

1. **Specialization:** a dedicated agent materially improves a distinct class of work.
2. **Parallelism:** independent work can safely run concurrently and latency matters.
3. **Separation of duties:** one agent should not both propose and approve a consequential action.
4. **Independent verification:** a second agent catches enough expensive errors to justify its cost.
5. **Capability routing:** tasks need to be assigned dynamically across heterogeneous providers or specialists.
6. **Fault isolation:** a failed specialist can degrade gracefully without taking down the whole workflow.
7. **Organizational boundary:** different agents operate for different principals, teams, vendors, or counterparties.
8. **Market selection:** competing agents can bid or be ranked for work based on price, quality, latency, or reputation.

If none applies, keep the architecture simpler.

## 2. Model orchestration as a control plane

Treat orchestration as infrastructure that coordinates probabilistic workers.

The control plane should own:

- task identity,
- durable workflow state,
- dependency tracking,
- routing policy,
- authority and budget ceilings,
- deadlines and timeouts,
- retries and fallback chains,
- approval gates,
- acceptance criteria,
- audit events,
- and terminal outcome state.

Do not rely on free-form agent conversation to remember critical workflow state.

A useful split is:

```text
Control plane
  ├── task graph
  ├── state machine
  ├── permissions
  ├── budgets
  ├── routing
  ├── retries / timeouts
  └── audit log
       ↓
Agent workers
  ├── planner
  ├── researcher
  ├── operator
  ├── verifier
  └── specialist services
```

The model may recommend what should happen next. The control plane decides what is actually allowed to happen next.

## 3. Use explicit delegation contracts

Every delegated task should have a machine-readable envelope. Avoid vague instructions such as “handle this account” or “finish the job.”

### Minimal task envelope

```json
{
  "task_id": "task_01J...",
  "parent_task_id": "task_01H...",
  "requester": "agent://principal/sales-ops",
  "assignee_capability": "invoice.followup",
  "objective": "Obtain payment status for invoice INV-4821",
  "inputs": ["invoice://INV-4821", "customer://C-19"],
  "allowed_actions": ["crm.read", "email.draft"],
  "forbidden_actions": ["email.send", "refund.create"],
  "max_spend_usd": 0.20,
  "deadline": "2026-08-27T18:00:00Z",
  "acceptance": [
    "status is supported by cited evidence",
    "draft contains no unverified payment claim"
  ],
  "return_schema": "invoice_followup.v1"
}
```

The envelope should separate:

- **objective** — what outcome is requested,
- **authority** — what the child is allowed to do,
- **budget** — what resources it may consume,
- **deadline** — when work is no longer useful,
- **acceptance** — how success will be judged,
- **evidence** — what provenance must accompany the answer.

## 4. Never expand authority through delegation

A child agent cannot receive more authority than its parent has.

If a parent has:

- $100 purchasing authority,
- access to customers A and B,
- and permission to draft but not send contracts,

then no descendant should be able to exceed those limits merely because the parent asked it to.

Use the intersection rule:

```text
child_authority = parent_authority
                  ∩ delegation_policy
                  ∩ child_role_policy
                  ∩ task_specific_policy
```

The same rule should apply to:

- spend,
- data access,
- geographic restrictions,
- tool scopes,
- contractual authority,
- regulated actions,
- and time windows.

### Budget propagation

Reserve child budgets from the parent budget before work begins.

Example:

```text
Parent remaining budget: $12.00
Research child reservation: $3.00
Verification child reservation: $2.00
Unreserved parent budget: $7.00
```

Return unused reservation when the task closes. Do not let independent descendants each assume the full parent budget.

## 5. Choose the right orchestration pattern

### Pattern A: deterministic pipeline

```text
intake → research → draft → verify → deliver
```

Best for repeatable business processes with known stages.

Use when:

- order matters,
- each stage has a clear schema,
- and reliability matters more than flexibility.

### Pattern B: planner / executor

```text
planner → task graph → executors → verifier
```

Best when work must be decomposed dynamically.

Risk: the planner can create unnecessary work or impossible dependencies. Bound plan depth, fan-out, and cost.

### Pattern C: supervisor / specialists

```text
               specialist A
request → supervisor → specialist B → synthesis
               specialist C
```

Best when capabilities are distinct and routing can be explicit.

Prefer capability-based routing over hard-coded agent names.

### Pattern D: parallel map / reduce

```text
              ┌→ worker 1 ─┐
request ──────┼→ worker 2 ─┼→ reducer
              └→ worker 3 ─┘
```

Best when independent subtasks can run concurrently.

Use bounded fan-out. The cost of 50 “cheap” workers can exceed one good worker.

### Pattern E: proposer / verifier

```text
proposer → candidate result → verifier → accept / reject / escalate
```

Best for expensive mistakes or high-value outputs.

The verifier should have explicit acceptance tests, not merely “review this.”

### Pattern F: competitive market

```text
job → eligible agents → bids / offers → selector → winner → verification
```

Best when multiple interchangeable agents can compete on:

- price,
- latency,
- quality history,
- availability,
- jurisdiction,
- or specialization.

This is the foundation of an agent labor market.

### Pattern G: peer swarm

Use carefully. Peer-to-peer collaboration without clear ownership can produce loops, duplicated work, deadlocks, inconsistent state, and unclear responsibility.

If a swarm is genuinely useful, still define:

- a task owner,
- termination conditions,
- conflict resolution,
- shared-state rules,
- and spend / concurrency limits.

## 6. Route by capability, not identity

Instead of:

```text
send task to agent-17
```

prefer:

```text
find eligible providers for capability=invoice.followup
filter by permissions, SLA, cost, trust, and availability
rank
assign
```

A routing score can be simple:

```text
score = quality_weight * success_rate
      + latency_weight * latency_score
      + price_weight * price_score
      + trust_weight * reputation_score
      + availability_weight * availability_score
```

Keep hard constraints outside the score. An agent that is unauthorized should be ineligible, not merely ranked lower.

### Fallback chains

For critical capabilities, define fallbacks before incidents happen:

```text
preferred provider
  ↓ unavailable / policy failure
secondary provider
  ↓ unavailable
reduced-capability workflow
  ↓ cannot satisfy acceptance criteria
human escalation
```

Test fallback paths periodically.

## 7. Make handoffs small and attributable

Long agent-to-agent transcripts are expensive and difficult to reason about.

A handoff should contain only what the next agent needs:

- task objective,
- structured inputs,
- relevant evidence,
- explicit constraints,
- unresolved questions,
- and a reference to durable state.

Avoid blindly forwarding an entire parent context.

### Handoff record

```json
{
  "from": "researcher",
  "to": "writer",
  "task_id": "task_123",
  "facts": [
    {"claim": "...", "source": "source://abc", "confidence": 0.92}
  ],
  "open_questions": ["..."],
  "constraints": ["Do not state estimated figures as actuals"],
  "trace_id": "trace_456"
}
```

Preserve provenance across every handoff so a later agent cannot turn a weak observation into an authoritative fact.

## 8. Define acceptance before execution

Agents should not invent their own definition of “done” after the work is complete.

Use measurable acceptance criteria such as:

- schema validates,
- every factual claim has a source,
- price is within approved bounds,
- no prohibited tool was invoked,
- output passes deterministic business rules,
- required human approval exists,
- latency is below SLA,
- and the customer-facing action is idempotent.

A verifier should return a structured decision:

```json
{
  "decision": "reject",
  "failed_rules": ["missing_source:claim_3"],
  "retryable": true,
  "recommended_route": "researcher"
}
```

## 9. Engineer for partial failure

Multi-agent systems fail like distributed systems plus probabilistic software.

Common failure modes include:

- one agent times out,
- duplicate task delivery,
- partial tool success,
- conflicting writes,
- stale state,
- cyclic delegation,
- one agent returning malformed output,
- one child exceeding expected cost,
- a provider disappearing mid-workflow,
- and a “successful” subtask that violates downstream assumptions.

### Idempotency

Every consequential action should have an idempotency key derived from the business operation, not the retry attempt.

```text
invoice-followup:INV-4821:2026-08-27
```

### Retry policy

Retry only errors that are plausibly transient.

Use:

- maximum attempts,
- exponential backoff,
- jitter,
- per-attempt timeout,
- total workflow deadline,
- and a cost ceiling.

Do not retry policy denials, deterministic validation failures, or irreversible actions blindly.

### Dead-letter workflow

Tasks that exhaust retries should move to an explicit review queue with:

- original objective,
- attempts,
- errors,
- tool side effects,
- spend consumed,
- and recommended recovery action.

### Compensation

If a workflow has multiple side effects, define how to compensate for partial completion.

Example:

```text
reserve inventory → charge card → book shipment
```

If shipment booking fails after charging, the recovery plan must be known before the workflow runs.

## 10. Control concurrency and shared state

Two agents acting at the same time can create races that no prompt can reliably prevent.

Use ordinary distributed-systems controls:

- optimistic version checks,
- database transactions,
- leases,
- queues,
- mutexes where appropriate,
- deduplication,
- compare-and-set updates,
- and single-writer ownership for critical records.

Do not ask agents to “coordinate among yourselves” over a shared bank balance, inventory count, or contract state.

## 11. Build human escalation into the graph

Human review is a workflow state, not an exception.

Escalate when:

- authority is insufficient,
- confidence is below threshold,
- expected loss exceeds tolerance,
- a task enters a regulated or contractual boundary,
- agents disagree on a consequential decision,
- spend exceeds a threshold,
- retry limits are exhausted,
- or acceptance criteria cannot be satisfied.

The reviewer should receive a compact packet:

- requested decision,
- evidence,
- agent recommendation,
- alternatives,
- expected impact,
- irreversible consequences,
- and an audit link.

## 12. Observe the whole workflow

Use one trace ID across parent and child tasks.

At minimum, record:

- task creation and completion,
- delegation edges,
- model and tool calls,
- routing decisions,
- policy decisions,
- retries and fallbacks,
- approvals,
- spend,
- latency,
- acceptance failures,
- and final customer outcome.

### Core orchestration metrics

Track:

| Metric | Why it matters |
|---|---|
| End-to-end success rate | business outcome reliability |
| Success rate by agent/capability | routing quality |
| Cost per successful workflow | profitability |
| p50/p95 completion latency | SLA and customer experience |
| Delegation depth | complexity creep |
| Fan-out per task | spend and coordination load |
| Retry rate | hidden reliability problems |
| Fallback activation rate | provider/control-plane health |
| Verification rejection rate | upstream quality |
| Human escalation rate | autonomy ceiling |
| Duplicate/compensated actions | distributed-state correctness |

A local agent success rate can look excellent while end-to-end workflow success collapses. Optimize the customer-visible outcome.

## 13. Evaluate coordination, not only individual agents

A strong specialist can still participate in a weak system.

Add multi-agent evals for:

- correct task decomposition,
- correct capability routing,
- authority preservation,
- budget preservation,
- information fidelity across handoffs,
- conflict resolution,
- partial-failure recovery,
- graceful degradation,
- verifier precision/recall,
- termination behavior,
- and end-to-end outcome quality.

### Failure localization

When a workflow fails, identify the earliest step after which successful recovery was no longer possible.

Do not assume the last agent that touched the task caused the failure. Root causes may be:

- a bad initial plan,
- missing context,
- incorrect routing,
- an earlier factual corruption,
- a tool side effect,
- or an invalid acceptance contract.

## 14. Measure whether orchestration is worth it

Compare the multi-agent workflow with the simplest credible baseline.

Example:

| Metric | Single agent | Multi-agent |
|---|---:|---:|
| Successful outcomes | 84% | 94% |
| Median latency | 22s | 41s |
| Cost / attempt | $0.18 | $0.43 |
| Cost / success | $0.21 | $0.46 |
| Human escalation | 12% | 4% |

The multi-agent version may be worthwhile if the extra 10 percentage points of success are economically valuable. If the outcome is low-value, it may not be.

A useful decision rule:

```text
incremental_value_of_quality
+ incremental_value_of_latency_improvement
+ incremental_value_of_reduced_human_work
>
incremental_agent_cost
+ coordination_cost
+ reliability_cost
+ operational_complexity_cost
```

## 15. Agent-to-agent service-level agreements

When agents buy work from other agents, define machine-readable service terms.

Useful fields include:

```json
{
  "capability": "research.company_profile",
  "version": "2.1",
  "max_latency_ms": 15000,
  "price_usd": 0.08,
  "availability_target": 0.995,
  "evidence_required": true,
  "data_retention": "none",
  "jurisdiction": ["US"],
  "refund_policy": "failed_acceptance_test",
  "support": "machine_ticket"
}
```

The orchestration layer can use these terms for routing and contract enforcement.

## 16. Business opportunities in orchestration

The explosion of agents creates businesses around coordination itself.

### Orchestration control plane

Sell durable workflow execution, task state, approvals, retries, traces, and policy-aware routing.

Possible pricing:

- per workflow,
- per active task,
- per successful outcome,
- or enterprise platform fee.

### Agent router / exchange

Match work to external agents based on capability, price, reputation, latency, and policy.

Revenue options:

- take rate on completed work,
- routing subscription,
- preferred-provider tools,
- or enterprise procurement contracts.

### Independent verification network

Agents pay independent verifiers to check high-value outputs or transactions.

Pricing can be tied to:

- verification request,
- transaction value,
- or assurance tier.

### Multi-agent observability

Offer trace correlation, delegation graphs, failure localization, spend attribution, and workflow replay.

### Agent SLA broker

Standardize performance terms, measure providers, manage failover, and settle disputes between agent buyers and sellers.

### Agent labor marketplace

Create a market where autonomous buyers can procure bounded tasks from specialized agents under explicit price, authority, evidence, and acceptance contracts.

The moat is not a directory. It is trusted transaction history, routing quality, verification, and settlement.

## 17. Production checklist

Before shipping a multi-agent workflow:

- [ ] A single-agent baseline was measured first.
- [ ] Every additional agent has a documented reason to exist.
- [ ] The workflow has one durable task/state authority.
- [ ] Delegated authority cannot exceed parent authority.
- [ ] Parent budgets are reserved before child work begins.
- [ ] Every task has explicit acceptance criteria.
- [ ] Capability routing uses hard eligibility constraints before ranking.
- [ ] Critical capabilities have tested fallback chains.
- [ ] Handoffs preserve provenance and minimize unnecessary context.
- [ ] Consequential actions are idempotent.
- [ ] Retry policy distinguishes transient from deterministic failures.
- [ ] Partial side effects have compensation/recovery procedures.
- [ ] Shared state uses deterministic concurrency controls.
- [ ] Human escalation is a first-class workflow state.
- [ ] One trace ID follows the full delegation tree.
- [ ] Cost, latency, retries, escalation, and outcome quality are measured end to end.
- [ ] Coordination evals test failures across agent boundaries.
- [ ] The multi-agent system beats the simpler baseline on customer economics.

## 18. Founder benchmark

For each production workflow, maintain a small benchmark record:

```text
Workflow:
Customer outcome:
Architecture: single / pipeline / planner-executor / supervisor / market / other
Agents involved:
Maximum delegation depth:
Maximum fan-out:
Success rate:
Cost per attempt:
Cost per successful outcome:
p50 / p95 latency:
Retry rate:
Fallback rate:
Verification rejection rate:
Human escalation rate:
Top three failure modes:
Last fault-injection test:
Simplest baseline performance:
Why multi-agent remains justified:
```

If the team cannot explain why the multi-agent version still beats its baseline, simplify it.

---

## Further reading

This playbook is intentionally protocol- and vendor-neutral. Useful current references include:

- AWS Well-Architected Agentic AI Lens guidance on multi-agent orchestration, capability routing, fallback chains, resilient control planes, durable messaging, and graceful degradation.
- Microsoft Research AgentRx work on localizing critical failure steps in long, stochastic and multi-agent execution trajectories.
- Current research on long-horizon delegated workflows, where small fidelity errors can accumulate across repeated handoffs.

Treat those as evidence for engineering principles, not as requirements to adopt a specific vendor stack.
