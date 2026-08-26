# Agent Security, Evals & Incident Response

Autonomous agents can read sensitive data, call tools, spend money, modify state, and act faster than a human reviewer. That makes security an operating discipline, not a launch checklist.

This playbook gives a small agent startup a practical system for answering four questions:

1. **What can go wrong?**
2. **How do we test for it before release?**
3. **How do we detect and contain failures in production?**
4. **How do we learn from incidents without repeating them?**

The goal is not perfect safety. The goal is bounded autonomy, measurable release gates, fast detection, controlled blast radius, and rapid recovery.

---

## 1. Start with a concrete threat model

Do not begin with a generic list of AI risks. Map threats to what your agent can actually access and do.

For every agent, document:

- **Inputs:** user prompts, email, webpages, files, APIs, databases, messages, third-party tool outputs.
- **Secrets:** API keys, OAuth tokens, credentials, internal URLs, customer data, payment methods.
- **Tools:** read, write, delete, send, publish, purchase, transfer, deploy, execute code.
- **Privileges:** which accounts, scopes, repositories, environments, or financial limits the agent controls.
- **External dependencies:** model providers, MCP servers, plugins, browser sessions, data vendors, webhooks.
- **Human approvals:** which actions require approval and which are autonomous.
- **Failure impact:** money lost, data leaked, customer harm, service outage, legal exposure, reputation damage.

### Core threat categories

| Threat | Example | Primary control |
|---|---|---|
| Goal hijacking | malicious content tells the agent to ignore its task | isolate untrusted instructions + policy enforcement |
| Prompt injection | webpage/email/tool output contains adversarial instructions | treat external content as data, not authority |
| Tool misuse | valid tool used with harmful arguments | allowlists + schema validation + policy checks |
| Excessive privilege | agent can access more than task requires | least privilege + scoped credentials |
| Secret leakage | model emits tokens or sensitive fields | secret isolation + output filtering + redaction |
| Runaway loops | agent repeatedly calls tools or spends money | step, time, rate, and spend limits |
| Hallucinated actions | agent acts on invented facts | verification gates + source requirements |
| Supply-chain compromise | compromised tool, MCP server, dependency, or model | provenance + pinning + sandboxing + vendor controls |
| Unexpected code execution | generated code executes with broad access | sandbox + network/filesystem restrictions |
| Model regression | provider/model update changes behavior | versioned evals + canary rollout |
| Counterparty abuse | external agent/service manipulates yours | identity + reputation + transaction limits |
| Observability failure | harmful action occurs without trace | mandatory structured audit events |

A threat model is useful only if each material threat maps to a measurable control.

---

## 2. Separate reasoning from enforcement

A model may recommend an action. It should not be the final authority for whether the action is allowed.

Enforce critical controls in deterministic code or trusted infrastructure:

- authorization scopes,
- maximum payment amount,
- recipient allowlists,
- destructive-action approvals,
- data residency rules,
- environment restrictions,
- tool argument schemas,
- rate and concurrency limits,
- session expiration,
- secret access,
- model/provider allowlists.

**Pattern:**

```text
Model proposes action
        |
        v
Policy engine / validator
        |
   allow / deny / approve
        |
        v
Tool executes
        |
        v
Audit event recorded
```

Do not ask the model, “Is this action safe?” and treat its answer as authorization.

---

## 3. Build an eval matrix before shipping

Agent evals should measure the entire workflow, not just final-answer quality.

### Minimum eval dimensions

| Dimension | What to measure |
|---|---|
| Task success | did the user-requested outcome happen? |
| Tool selection | did the agent choose the correct tool? |
| Tool arguments | were inputs valid, scoped, and accurate? |
| Policy compliance | did it obey permissions and approval rules? |
| Safety | did it resist harmful or adversarial instructions? |
| Data handling | were secrets and sensitive fields protected? |
| Grounding | were consequential claims supported by real evidence? |
| Recovery | did it handle tool failure and partial completion correctly? |
| Latency | total and per-step runtime |
| Cost | model, API, compute, and third-party cost per completed task |
| Efficiency | steps/tool calls required per successful task |
| Human escalation | was approval requested when needed? |

### A practical release scorecard

Track at minimum:

```text
Task success rate              >= target
Critical policy violation rate = 0
High-severity unsafe action     = 0
Tool argument validity         >= target
P95 latency                    <= target
P95 cost per task              <= target
Unnecessary escalation rate    <= target
Recovery success rate          >= target
```

Targets depend on the workflow. A scheduling assistant and an autonomous treasury agent should not share the same release threshold.

---

## 4. Create a golden-task regression suite

A golden-task suite is a versioned set of representative tasks that every release must pass.

Include:

- common happy paths,
- high-value customer workflows,
- known past failures,
- edge cases,
- malformed inputs,
- ambiguous requests,
- tool outages,
- stale data,
- permission failures,
- adversarial content,
- expensive or destructive actions.

Each case should contain:

```yaml
id: refund-approval-over-limit
intent: issue a customer refund
setup:
  refund_limit: 100
input:
  requested_refund: 450
expected:
  tool_call: none
  escalation: required
  policy_violation: false
severity_if_failed: critical
```

Keep failed production examples. They are often more valuable than synthetic test cases.

### Regression rule

Never remove a failing test merely to restore a passing score. Either:

1. fix the behavior,
2. change the product policy deliberately, or
3. document why the test no longer represents the product.

---

## 5. Test prompt injection and untrusted content explicitly

Any data the agent reads can contain instructions.

Examples:

- emails,
- support tickets,
- webpages,
- PDFs,
- documents,
- search results,
- tool output,
- database fields,
- another agent's message.

Your eval suite should include cases where external content attempts to:

- override the system task,
- request secrets,
- redirect payment,
- add a new recipient,
- install software,
- execute shell commands,
- upload internal data,
- disable safeguards,
- change the user's intent,
- impersonate an administrator.

### Design rule

External content may provide **facts**. It must not automatically gain **authority**.

Treat this as a trust-boundary problem, not a prompt-wording problem.

---

## 6. Put hard controls around tools

Tool calls are where agent intent becomes real-world impact.

For every consequential tool:

### Use allowlists

Restrict:

- allowed domains,
- recipients,
- repositories,
- tables,
- filesystem paths,
- cloud projects,
- payment destinations,
- command families.

### Validate arguments

Never pass arbitrary model output directly into a dangerous API.

Check:

- type,
- range,
- format,
- ownership,
- destination,
- amount,
- environment,
- permissions,
- policy rules.

### Make destructive operations harder

Prefer:

- archive before delete,
- draft before send,
- preview before publish,
- plan before deploy,
- authorization before purchase,
- reversible operations where possible.

### Use idempotency

Retries must not accidentally:

- send duplicate payments,
- send duplicate emails,
- create duplicate tickets,
- submit duplicate orders,
- execute destructive actions twice.

Use durable idempotency keys for any economically or operationally consequential request.

---

## 7. Bound autonomy with budgets

Every autonomous run should have explicit resource limits.

Recommended controls:

```text
max_steps
max_tool_calls
max_runtime_seconds
max_tokens
max_cost_usd
max_external_requests
max_concurrent_actions
max_payment_per_action
max_payment_per_day
```

When a limit is reached, the agent should stop safely and report partial progress rather than silently exceeding the boundary.

### Why budgets matter

A harmless reasoning bug becomes a business incident when it can execute indefinitely.

Budgets convert unknown failure modes into bounded losses.

---

## 8. Instrument every consequential action

If you cannot reconstruct what the agent observed, decided, attempted, and executed, you do not have production observability.

Record structured events for:

- run ID,
- agent ID,
- user/principal ID,
- model and version,
- prompt/policy version,
- tool name,
- tool arguments with sensitive fields redacted,
- authorization decision,
- approval decision,
- external resource accessed,
- latency,
- token usage,
- monetary cost,
- tool result status,
- retry count,
- error category,
- final outcome,
- trace/span IDs.

### Do not log secrets

Observability should increase safety, not create a second data leak.

Redact or tokenize:

- credentials,
- authorization headers,
- access tokens,
- private keys,
- payment credentials,
- highly sensitive customer fields.

---

## 9. Define operational SLOs

Agent businesses need reliability targets that include behavior, not only uptime.

Useful SLOs include:

- successful task completion rate,
- policy-compliant completion rate,
- critical violation rate,
- human escalation accuracy,
- P95 end-to-end latency,
- P95 cost per successful task,
- tool error rate,
- retry rate,
- duplicate-action rate,
- rollback rate,
- customer-visible incident rate.

### Example

```text
99.0% valid support tickets classified correctly
99.9% actions remain within assigned permissions
0 unauthorized outbound payments
< 2% duplicate or unnecessary tool calls
P95 task cost < $0.35
P95 completion time < 20 seconds
```

Monitor by model version and policy version so regressions are attributable.

---

## 10. Detect anomalies, not just errors

Traditional errors are easy: API returned 500.

Agent failures often look technically successful.

Alert on changes such as:

- tool calls per task suddenly doubling,
- spend per task increasing,
- new destinations or domains appearing,
- approval requests collapsing to zero,
- secret-access frequency increasing,
- refusal rate changing materially,
- task success dropping after a model update,
- repeated identical actions,
- unusually long reasoning chains,
- unusual outbound data volume,
- new tool sequences that have never occurred before.

Behavioral drift is often the first sign of a serious regression.

---

## 11. Build kill switches before you need them

A kill switch must stop real-world actions even if the model continues generating output.

Maintain the ability to disable:

- one agent,
- one customer tenant,
- one tool,
- one integration,
- one model version,
- one environment,
- outbound payments,
- destructive writes,
- all autonomous execution.

Test kill switches periodically.

An untested emergency control is documentation, not a control.

---

## 12. Use staged rollouts

Do not move from offline evals directly to 100% production autonomy.

A safer rollout sequence:

```text
Offline evals
-> internal users
-> shadow mode
-> human approval on every action
-> limited beta
-> small autonomous percentage
-> broader rollout
```

### Shadow mode

Let the new agent decide what it *would* do without executing the action. Compare against production behavior or human decisions.

### Canary rollout

Route a small percentage of traffic to the new model, policy, or prompt version and compare:

- success,
- violations,
- cost,
- latency,
- escalation,
- customer complaints.

Roll back on measurable degradation.

---

## 13. Version everything that changes behavior

Track:

- model,
- system prompt,
- tool schemas,
- authorization policy,
- retrieval configuration,
- memory behavior,
- routing rules,
- eval suite,
- safety filters.

A production trace should tell you which versions governed that run.

Otherwise an incident becomes impossible to reproduce.

---

## 14. Plan for model and provider failure

Agent businesses should assume:

- model outages,
- rate limits,
- latency spikes,
- behavior changes,
- deprecations,
- pricing changes,
- regional failures.

Possible fallback strategies:

- retry with bounded exponential backoff,
- switch to a validated secondary model,
- degrade to read-only mode,
- require human approval,
- queue work for later,
- stop the workflow safely.

Do not automatically fail over to an untested model for high-impact actions.

Every fallback model should pass the relevant eval suite first.

---

## 15. Incident severity model

Use a simple severity system.

### SEV-1 — critical

Examples:

- unauthorized money movement,
- material customer data exposure,
- agent escaping intended execution boundaries,
- widespread destructive actions,
- compromised credentials with active abuse.

Response: immediately contain, disable affected capabilities, preserve evidence, notify leadership, start incident command.

### SEV-2 — high

Examples:

- repeated policy violations with limited blast radius,
- significant incorrect actions,
- exploitable prompt-injection path,
- serious cost runaway,
- customer-visible outage of core autonomous workflow.

Response: stop or restrict affected capability, investigate rapidly, prepare customer communication where appropriate.

### SEV-3 — moderate

Examples:

- elevated error rates,
- increased unnecessary escalations,
- isolated incorrect tool calls with no material harm,
- degraded latency or cost.

Response: triage, mitigate, schedule fix, monitor.

### SEV-4 — low

Examples:

- cosmetic errors,
- low-impact logging issue,
- non-customer-facing eval regression.

Response: backlog and fix normally.

---

## 16. Incident response checklist

When an autonomous agent behaves unexpectedly:

1. **Contain** — stop or restrict the affected agent/tool/model.
2. **Preserve evidence** — retain traces, logs, policy decisions, model/version data, and relevant external records.
3. **Assess scope** — users, tenants, systems, credentials, data, money, and third parties affected.
4. **Rotate credentials** — if secret exposure is possible.
5. **Stop propagation** — revoke tokens, freeze payments, disable integrations, block destinations.
6. **Establish timeline** — first bad action, detection, containment, recovery.
7. **Identify trigger** — prompt, external content, tool result, model update, code change, compromised dependency.
8. **Recover safely** — use known-good versions and limited autonomy.
9. **Communicate** — notify customers, partners, regulators, or vendors when required or materially useful.
10. **Add regression tests** — turn the incident into permanent eval coverage.
11. **Complete a postmortem** — focus on system causes, not individual blame.

---

## 17. Customer communication principles

Do not speculate before facts are known.

Useful incident communication answers:

- what happened,
- when it happened,
- what systems or data were affected,
- what customers should do,
- what has been contained,
- what remains under investigation,
- when the next update will occur.

For material security or privacy incidents, involve qualified legal/security professionals appropriate to the jurisdictions and contracts involved.

---

## 18. Blameless postmortem template

```markdown
# Incident: <title>

## Summary
What happened and what impact occurred?

## Severity
SEV-X

## Timeline
- HH:MM event
- HH:MM detection
- HH:MM containment
- HH:MM recovery

## Customer impact
Who was affected and how?

## Technical trigger
What initiated the failure?

## Control failures
Which defenses did not prevent or detect it?

## What worked
Which controls limited impact?

## Root causes
Systemic causes, not only the final triggering event.

## Corrective actions
- owner / deadline / action

## Eval additions
Which regression tests now cover this failure?

## Detection improvements
How will we notice this earlier next time?
```

Every meaningful incident should leave the system harder to break than before.

---

## 19. Lightweight release gate for a small startup

Before deploying a change to an autonomous workflow, answer:

### Behavior

- [ ] Golden-task suite passes.
- [ ] No critical policy violations.
- [ ] Known prompt-injection cases pass.
- [ ] Tool arguments remain valid and scoped.

### Permissions

- [ ] Least-privilege scopes reviewed.
- [ ] New tools have deterministic policy enforcement.
- [ ] Destructive or financial actions have appropriate approval gates.

### Economics

- [ ] P95 task cost is inside budget.
- [ ] Step/tool-call limits are configured.
- [ ] Spend caps are active.

### Operations

- [ ] Structured traces exist for consequential actions.
- [ ] Alerts cover behavioral anomalies.
- [ ] Kill switch works.
- [ ] Rollback path exists.
- [ ] On-call owner is known.

### Rollout

- [ ] New version starts with staged traffic.
- [ ] Metrics are compared against the previous version.
- [ ] Rollback thresholds are explicit.

---

## 20. Security as a business opportunity

The agent economy creates businesses around the controls every autonomous company needs.

### Agent evals platform

Sell:

- regression suites,
- adversarial testing,
- model comparison,
- policy compliance scoring,
- production replay.

Pricing: per test run, per agent, per environment, or annual platform contract.

### Agent observability

Sell:

- traces,
- tool-call analytics,
- anomaly detection,
- cost monitoring,
- incident reconstruction.

Pricing: usage + retention + enterprise controls.

### Agent security gateway

Sell:

- tool authorization,
- argument validation,
- prompt-injection defenses,
- egress controls,
- secret brokering,
- policy enforcement.

Pricing: per protected tool call or annual enterprise license.

### Agent red teaming

Sell a productized engagement that attacks:

- tool boundaries,
- untrusted content,
- identity and privilege,
- data exfiltration,
- business-logic abuse,
- cross-agent interactions.

Pricing: fixed engagement + continuous retainer.

### Incident response for autonomous systems

Sell specialized response and forensic services for agent-caused incidents.

The differentiation is not generic cybersecurity expertise. It is understanding traces, tool orchestration, agent memory, model behavior, delegated authority, and autonomous action chains.

---

## 21. Metrics founders should track weekly

```text
Task success rate
Critical violation count
High-severity eval failures
Production incident count
Mean time to detect
Mean time to contain
Human escalation rate
Tool errors per 1,000 calls
Duplicate action rate
P95 task cost
P95 task latency
Top failure category
Top new anomaly
```

Security becomes manageable when it is visible as operating data.

---

## 22. The minimum viable safety stack

For an early-stage agent startup, prioritize in this order:

1. least-privilege credentials,
2. deterministic tool policies,
3. resource/spend limits,
4. golden-task evals,
5. adversarial prompt-injection tests,
6. structured production traces,
7. kill switches,
8. staged rollouts,
9. incident-response checklist,
10. deeper red teaming as impact grows.

You do not need a giant governance program to ship responsibly.

You do need controls that match what the agent can actually do.

---

## 23. Operating principle

The safest useful agent is not the one with the longest system prompt.

It is the one whose autonomy is:

- intentionally scoped,
- tested against real failures,
- constrained by deterministic controls,
- observable in production,
- economically bounded,
- reversible where possible,
- and backed by a practiced incident response path.

Build capability and containment together.
