# Agent Capability Benchmarking, Certification & Assurance

Autonomous buyers cannot safely purchase a capability because a seller says it is "accurate," "reliable," or "enterprise ready." They need evidence that is scoped, fresh, reproducible, and tied to the exact workload they intend to delegate.

This playbook shows agent founders how to turn capability claims into buyer-verifiable proof.

The core rule is simple:

> **Never publish a capability claim without publishing what was tested, under what conditions, against what baseline, with what uncertainty, and for how long the evidence should remain trusted.**

A useful assurance system should answer six questions:

1. What exactly can this agent do?
2. On which population of tasks does the claim apply?
3. How was performance measured?
4. How uncertain is the estimate?
5. What changed since the evidence was produced?
6. Can a buyer independently verify the claim before paying or delegating authority?

---

## 1. Separate marketing claims from assurance claims

Marketing language can be broad. Assurance claims cannot.

Bad claim:

```text
Our agent resolves support tickets with 95% accuracy.
```

Better claim:

```text
On 1,240 English-language Tier-1 SaaS support tickets sampled from the last
90 days, version 3.4 resolved 91.8% without human correction, with a 95%
confidence interval of 90.2%-93.3%, median latency of 18.4 seconds, and median
delivery cost of $0.071 per resolved ticket. The benchmark excludes billing
disputes and account-security incidents. Evidence expires after 30 days or
on any material model, prompt, tool, policy, or retrieval change.
```

The second claim is useful because a buyer can decide whether the evidence applies to its own workload.

---

## 2. Publish a machine-readable capability claim

Every paid capability should expose a canonical claim object.

Example:

```json
{
  "capability_id": "support.resolve_tier1.v3",
  "claim_version": "2026-08-27.1",
  "task": "resolve_tier1_support_ticket",
  "population": {
    "language": ["en"],
    "customer_type": ["b2b_saas"],
    "excluded_categories": ["billing_dispute", "security_incident"]
  },
  "constraints": {
    "max_context_tokens": 120000,
    "required_integrations": ["knowledge_base", "crm"],
    "human_review": "exceptions_only"
  },
  "metrics": {
    "successful_outcome_rate": 0.918,
    "human_correction_rate": 0.061,
    "p95_latency_seconds": 41.2,
    "median_cost_usd": 0.071,
    "safety_violation_rate": 0.0008
  },
  "uncertainty": {
    "confidence_level": 0.95,
    "successful_outcome_rate_interval": [0.902, 0.933],
    "sample_size": 1240
  },
  "benchmark": {
    "suite_id": "tier1-support-prodlike-2026q3",
    "dataset_visibility": "sequestered",
    "run_id": "run_8b213",
    "evaluator_version": "2.1.0"
  },
  "provenance": {
    "agent_version": "3.4.0",
    "model_family": "provider/model-version",
    "toolset_digest": "sha256:...",
    "policy_digest": "sha256:...",
    "knowledge_snapshot": "kb_2026_08_26"
  },
  "validity": {
    "tested_at": "2026-08-27T16:00:00Z",
    "expires_at": "2026-09-26T16:00:00Z",
    "recertify_on_material_change": true
  }
}
```

A buyer should be able to reject a claim automatically when its scope, evidence age, or uncertainty does not meet procurement policy.

---

## 3. Define the population before choosing the metric

A benchmark score is meaningless if the evaluated population does not resemble production.

Define:

- customer segment,
- language and geography,
- workflow category,
- complexity distribution,
- input length,
- tool availability,
- data freshness,
- risk tier,
- expected ambiguity,
- long-tail and adversarial cases,
- human-review policy,
- execution environment.

Avoid the "benchmark average" trap. A system may look strong overall while failing on the exact segment that produces most revenue or risk.

Stratify results when materially different workloads exist.

Example:

| Segment | Sample | Success | Human correction | P95 latency | Median cost |
|---|---:|---:|---:|---:|---:|
| Simple FAQ | 500 | 97.2% | 1.8% | 12s | $0.03 |
| Workflow update | 420 | 91.4% | 6.2% | 31s | $0.08 |
| Ambiguous request | 240 | 78.8% | 18.3% | 54s | $0.14 |
| Long-tail | 80 | 66.3% | 31.3% | 71s | $0.19 |

Do not hide the last two rows because they lower the average. They are exactly where a buyer learns whether the capability is safe to delegate.

---

## 4. Measure successful outcomes, not model outputs

For agent businesses, the primary unit of measurement should normally be the completed customer outcome.

Useful outcome metrics include:

- task success rate,
- verified resolution rate,
- accepted deliverable rate,
- human-correction rate,
- rework rate,
- transaction completion rate,
- recovery rate after failure,
- policy-compliant completion rate,
- customer-confirmed value,
- successful outcome per dollar.

Supporting metrics include:

- latency,
- cost,
- tool-call count,
- retry count,
- escalation rate,
- error rate,
- refusal precision/recall,
- unsupported-action rate,
- data-leakage rate,
- authority-boundary violation rate.

Do not optimize a supporting metric if it worsens the business outcome.

For example, a cheaper model route is not an improvement if it raises rework enough to increase total cost per successful outcome.

---

## 5. Always include uncertainty

A point estimate without uncertainty invites false confidence.

At minimum, publish:

- sample size,
- confidence level,
- confidence interval or credible interval,
- sampling method,
- number of repeated runs when stochasticity matters,
- missing or excluded cases,
- evaluator disagreement when judgment is subjective.

Small samples should produce visibly weaker claims.

Do not convert "10/10 passed" into "100% reliable."

A better statement is:

```text
10 of 10 test cases passed. Sample size is too small to support a precise
reliability estimate; this result should be treated as preliminary evidence.
```

When outcomes vary by task, customer, or environment, model that variation instead of pretending observations are perfectly interchangeable.

---

## 6. Distinguish benchmark accuracy from generalized performance

A system can perform well on a fixed benchmark without proving equivalent performance on future production tasks.

Track two concepts separately:

### Benchmark performance

How did the system perform on the exact test set?

### Generalized performance

What performance should a buyer expect on new tasks drawn from the intended population?

This distinction matters when:

- benchmark items are unusually easy or hard,
- many items come from the same source,
- repeated observations share structure,
- benchmark composition differs from customer traffic,
- a model or prompt may have seen benchmark content before.

Treat generalized performance as an inference problem, not a simple arithmetic average.

---

## 7. Use public and private benchmarks differently

### Public benchmarks

Best for:

- broad comparability,
- onboarding new buyers,
- documenting methodology,
- reproducing non-sensitive results.

Risks:

- memorization,
- prompt tuning to known items,
- selective reporting,
- benchmark-specific hacks.

### Private or sequestered benchmarks

Best for:

- certification,
- procurement gates,
- high-stakes capabilities,
- contamination resistance,
- anti-gaming controls.

Risks:

- lower transparency,
- evaluator trust requirements,
- operational cost.

A mature assurance program often uses both: public methodology plus private test items.

---

## 8. Control benchmark contamination

Treat the test set as production-sensitive infrastructure.

Controls should include:

- separate benchmark storage from training and product telemetry,
- restrict test-item access,
- rotate or replenish hidden items,
- track hashes of benchmark artifacts,
- block benchmark examples from retrieval corpora,
- prohibit manual prompt tuning against certification sets,
- maintain canary items to detect leakage,
- inspect suspicious step-function performance gains,
- keep development, validation, and certification sets separate.

If an agent can search the internet or an internal knowledge base during a test, define whether finding the answer is part of the capability or contamination.

---

## 9. Benchmark realistic workflows, not isolated trivia

Agent businesses make money from workflows.

Benchmark full trajectories where possible:

```text
Input -> planning -> tool use -> state changes -> verification -> final outcome
```

Include:

- unavailable tools,
- stale data,
- partial API failures,
- ambiguous requests,
- conflicting instructions,
- insufficient authority,
- changing state during execution,
- duplicate events,
- retries,
- customer corrections,
- downstream side effects.

A capability that succeeds only when every dependency behaves perfectly is not production-ready.

---

## 10. Evaluate safety and authority alongside quality

A high-quality answer can still be a failed agent outcome if it exceeds delegated authority.

Measure:

- unauthorized actions,
- secret exposure,
- cross-tenant access,
- prohibited purchases,
- unapproved external communication,
- unsafe tool selection,
- policy-bypass success,
- prompt-injection susceptibility,
- failure to escalate when required.

Safety metrics should be treated as gates for some capabilities, not merely blended into an overall score.

Example:

```text
Quality >= 92%
AND unauthorized-action rate = 0 in certification suite
AND high-severity prompt-injection success = 0
AND p95 latency <= 60s
```

Do not let excellent average quality compensate for unacceptable tail risk.

---

## 11. Evaluate cost-quality tradeoffs

Autonomous buyers care about economics, not leaderboard status.

For each configuration, report a frontier:

| Route | Success | P95 latency | Cost / attempt | Cost / success |
|---|---:|---:|---:|---:|
| Fast | 84% | 8s | $0.02 | $0.024 |
| Balanced | 92% | 24s | $0.06 | $0.065 |
| Premium | 96% | 62s | $0.21 | $0.219 |

The best route depends on the buyer's value of success, latency tolerance, and risk.

Expose enough evidence for the buyer to make that decision automatically.

---

## 12. Compare against useful baselines

A benchmark should answer "better than what?"

Useful baselines include:

- current human workflow,
- previous agent version,
- simplest deterministic automation,
- lower-cost model route,
- incumbent vendor,
- manual outsource provider,
- buyer's internal SLA.

Avoid misleading competitor rankings when environments differ.

If you cannot reproduce a competitor under equivalent conditions, state that limitation explicitly.

Prefer:

```text
Version 4 reduced median cost per successful outcome by 28% versus our own
version 3 on the same sequestered suite.
```

Over:

```text
#1 support agent in the world.
```

---

## 13. Make evaluation reproducible

Every benchmark run should produce a run manifest.

```yaml
run_id: run_2026_08_27_001
suite: tier1-support-prodlike-2026q3
suite_digest: sha256:...
agent_version: 3.4.0
prompt_digest: sha256:...
policy_digest: sha256:...
toolset_digest: sha256:...
knowledge_snapshot: kb_2026_08_26
model_route: provider/model-version
runtime_version: 1.8.2
started_at: 2026-08-27T16:00:00Z
completed_at: 2026-08-27T16:41:09Z
seed_policy: recorded
network_policy: restricted
human_review_policy: none
```

Preserve enough evidence to answer:

- what ran,
- on what,
- with which dependencies,
- under which policies,
- what happened,
- how the score was computed.

---

## 14. Issue signed benchmark receipts

For agent-to-agent commerce, benchmark results should be portable evidence.

A benchmark receipt can include:

```json
{
  "issuer": "did:web:assurance.example",
  "subject": "agent:vendor/capability/support.resolve_tier1.v3",
  "suite": "tier1-support-prodlike-2026q3",
  "result_digest": "sha256:...",
  "claim_digest": "sha256:...",
  "tested_at": "2026-08-27T16:00:00Z",
  "expires_at": "2026-09-26T16:00:00Z",
  "signature": "..."
}
```

The receipt should not require exposing confidential test items.

A buyer can verify the signature, evidence age, issuer, scope, and revocation status before accepting the claim.

---

## 15. Define certification tiers carefully

Certification should communicate scope, not prestige.

Example:

### Observed

- seller-run benchmark,
- methodology published,
- evidence digest available.

### Verified

- independent reproduction,
- hidden or sequestered test set,
- provenance checked.

### Continuously assured

- production telemetry monitored,
- recertification triggers automated,
- claim expires on material drift,
- revocation feed available.

Never imply that certification means "safe for all uses."

Every certificate needs:

- capability scope,
- excluded uses,
- tested environment,
- metric thresholds,
- issue date,
- expiry date,
- evidence version,
- revocation mechanism.

---

## 16. Recertify after material changes

Agent systems drift because their dependencies drift.

Trigger recertification when any of these change materially:

- model or model version,
- system prompt,
- workflow graph,
- tool schema,
- external API behavior,
- retrieval source,
- policy engine,
- memory behavior,
- runtime environment,
- safety filter,
- pricing or routing policy,
- human-review policy.

Use dependency digests to detect change automatically.

Do not assume a benchmark from last quarter still applies because the product name is unchanged.

---

## 17. Add expiration to every claim

Evidence should decay with time.

Expiration can be based on:

- elapsed time,
- number of production executions,
- dependency-change events,
- measured drift,
- incident occurrence,
- customer-segment shift.

Example policy:

```text
Claim expires at the earliest of:
- 30 days,
- 100,000 paid executions,
- a material dependency change,
- a high-severity incident,
- statistically significant production drift.
```

Stale proof should fail closed for high-risk procurement.

---

## 18. Monitor production against the certified population

Certification is not a substitute for live assurance.

Compare production with benchmark assumptions:

- input distribution,
- task mix,
- success rate,
- latency,
- cost,
- escalation rate,
- policy violations,
- dependency versions.

Flag **scope drift** when production moves outside the tested population.

Example:

```text
Certified population: English Tier-1 tickets
Current traffic: 22% Spanish, 18% billing disputes
Status: evidence applicability degraded
Action: route out-of-scope tasks to fallback + launch new benchmark stratum
```

---

## 19. Detect benchmark gaming

Common failure modes:

### Cherry-picking

Only favorable tasks or runs are reported.

Control: pre-register suite composition and reporting rules.

### Selective stopping

Testing stops once a desired score appears.

Control: predefine sample size and stopping criteria.

### Test-set tuning

Prompts or policies are optimized against certification items.

Control: sequestered tests and access logging.

### Metric substitution

A convenient proxy replaces the buyer outcome.

Control: tie certification to verified customer outcomes where possible.

### Hidden exclusions

Hard cases disappear from the denominator.

Control: publish exclusions and missing-data counts.

### Judge exploitation

The agent learns to satisfy an automated evaluator rather than the intended outcome.

Control: rotate evaluators, use adversarial verification, and audit disagreement with humans or deterministic evidence.

---

## 20. Treat LLM judges as measurement instruments

An LLM judge is not ground truth.

For judge-based evaluation:

- pin the judge version when possible,
- document the rubric,
- blind the judge to vendor identity,
- randomize answer order,
- measure judge consistency,
- compare against expert labels,
- monitor drift after judge updates,
- preserve raw evidence for re-scoring.

If the judge is changed, do not silently compare the new score with historical scores as though the measurement instrument were identical.

---

## 21. Build buyer-specific acceptance tests

Generic certification gets an agent into consideration. Buyer-specific acceptance gets it into production.

A buyer should be able to submit:

```json
{
  "required_capability": "support.resolve_tier1",
  "acceptance": {
    "success_rate_min": 0.94,
    "p95_latency_seconds_max": 45,
    "cost_per_success_usd_max": 0.12,
    "unauthorized_action_rate_max": 0,
    "evidence_age_days_max": 30
  },
  "sample": "buyer_private_suite_v7"
}
```

The seller returns a proof bundle rather than a sales deck.

This is a natural interface between benchmarking, procurement, and agent marketplaces.

---

## 22. Make proof machine-readable for marketplaces

Marketplaces should rank evidence, not adjectives.

Useful marketplace fields:

- capability scope,
- verified success rate,
- uncertainty,
- cost per successful outcome,
- latency distribution,
- safety gates,
- evidence age,
- certification issuer,
- production volume,
- recent incident status,
- buyer acceptance-test history.

Ranking should weight evidence quality and applicability, not just raw score.

A 97% result from 30 cherry-picked public examples may deserve less confidence than 93% across 20,000 recent sequestered and production-like tasks.

---

## 23. Do not collapse evidence into one opaque score

A single score is convenient but often destroys decision-relevant information.

Prefer a vector:

```text
success      93.2%
safety       pass
p95 latency  28s
cost/success $0.084
human review 4.1%
evidence age 8d
sample       4,320
```

If a composite score is used, publish the weights and preserve the underlying metrics.

Autonomous buyers should be able to apply their own utility function.

---

## 24. Connect assurance to pricing

Evidence can support higher pricing when it reduces buyer risk.

Possible packaging:

### Standard

- seller-run public benchmark,
- normal SLA.

### Verified

- independent benchmark receipt,
- stronger SLA,
- buyer acceptance test.

### Assured

- continuous monitoring,
- recertification triggers,
- claim revocation feed,
- audit evidence,
- stronger service credits.

Do not price "certification" as a decorative badge. Price the real operational cost and risk reduction.

---

## 25. Assurance economics

Track the cost of proof.

```text
assurance_cost_per_period =
  benchmark_execution
+ hidden_test_generation
+ evaluator_cost
+ human_review
+ independent_verification
+ evidence_storage
+ monitoring
+ recertification
```

Then measure:

```text
assurance_roi =
  incremental_gross_profit_from_higher_conversion_or_price
+ avoided_loss_from_detected_drift
+ avoided_procurement_friction
- assurance_cost
```

Do not run expensive certification suites more often than the risk and commercial value justify.

---

## 26. Practical benchmark design checklist

Before running a benchmark:

- [ ] define the capability and excluded uses,
- [ ] define the target population,
- [ ] choose outcome metrics,
- [ ] define safety gates,
- [ ] choose baselines,
- [ ] pre-register sample size,
- [ ] separate development and certification sets,
- [ ] record dependency versions,
- [ ] define missing-data policy,
- [ ] define stopping rules,
- [ ] define confidence reporting,
- [ ] define evidence retention,
- [ ] define claim expiration,
- [ ] define recertification triggers.

After the run:

- [ ] preserve raw outcomes,
- [ ] compute uncertainty,
- [ ] report all pre-registered metrics,
- [ ] disclose exclusions,
- [ ] compare with baselines,
- [ ] issue evidence digest,
- [ ] sign receipt if applicable,
- [ ] publish claim scope,
- [ ] register expiry/revocation,
- [ ] start production drift monitoring.

---

## 27. Suggested assurance dashboard

Track at least:

### Claim health

- active claims,
- expiring claims,
- revoked claims,
- claims awaiting recertification.

### Evidence quality

- sample size,
- evidence age,
- percentage using sequestered tests,
- percentage independently verified,
- judge/human disagreement.

### Production drift

- success delta from certification,
- cost delta,
- latency delta,
- task-distribution shift,
- dependency-change count,
- out-of-scope traffic percentage.

### Commercial impact

- procurement pass rate,
- acceptance-test pass rate,
- conversion with verified evidence,
- price premium for assured tier,
- churn by assurance tier,
- gross profit net of assurance cost.

---

## 28. Eval the assurance system itself

Test failure scenarios such as:

1. a model provider changes behavior without changing the model alias,
2. public benchmark items leak into retrieval,
3. success improves while safety violations increase,
4. a tiny sample produces an apparently perfect score,
5. one customer segment degrades while the aggregate stays flat,
6. the evaluator model changes its preferences,
7. a supplier selectively omits failed runs,
8. production traffic shifts outside the certified population,
9. cost per success doubles while raw success remains constant,
10. a signed certificate remains technically valid after a dependency change,
11. an adversarial agent tries to forge a benchmark receipt,
12. a marketplace ranks stale evidence above fresh evidence,
13. a buyer submits a private acceptance suite containing sensitive data,
14. repeated certification attempts create test-set overfitting,
15. an incident should revoke a claim but the revocation feed fails.

A robust system should fail loudly and conservatively.

---

## 29. Business opportunities

The assurance layer itself can become a business.

### Independent agent testing labs

Run sequestered, reproducible evaluations for buyers and sellers.

Revenue:

- per certification,
- recurring assurance subscription,
- enterprise testing retainers.

### Continuous assurance API

Watch dependency changes, production drift, claim validity, and recertification triggers.

Revenue:

- per monitored capability,
- per production execution,
- enterprise platform fee.

### Benchmark network

Maintain industry-specific hidden test pools and representative workload distributions.

Revenue:

- benchmark access,
- marketplace licensing,
- procurement integrations.

### Acceptance-test exchange

Let buyers publish private or permissioned acceptance suites and suppliers return verifiable results.

Revenue:

- transaction fee,
- buyer subscription,
- supplier verification fee.

### Evidence and certificate registry

Store signed claims, issuer metadata, expiry, revocation, and provenance.

Revenue:

- registry API,
- verification calls,
- enterprise private registry.

### Benchmark observability

Detect evaluator drift, contamination, cherry-picking, and suspicious score movement.

Revenue:

- monitoring subscription,
- audit services,
- marketplace risk tooling.

---

## 30. A minimal 7-day implementation plan

### Day 1: define one precise capability

Write the population, exclusions, outcome, constraints, and buyer decision it supports.

### Day 2: build a representative test sample

Stratify by the real traffic mix and reserve hidden items.

### Day 3: define metrics and gates

Include outcome, cost, latency, safety, and human-review measures.

### Day 4: make runs reproducible

Record prompts, policies, tool versions, model routes, knowledge snapshots, and environment.

### Day 5: quantify uncertainty

Publish sample size and confidence intervals. Compare with at least one useful baseline.

### Day 6: publish a machine-readable claim

Include scope, evidence digest, tested version, expiration, and recertification triggers.

### Day 7: connect production drift to revocation

Detect when the claim no longer applies and stop buyers from relying on stale proof.

---

## 31. Assurance operating principle

The goal is not to prove that an agent is universally good.

The goal is to make a narrow economic promise falsifiable.

A trustworthy agent business can say:

```text
This capability was tested on this kind of work,
under these constraints,
with these measured outcomes,
with this uncertainty,
using these dependencies,
and this evidence remains valid until this date or this system changes.
```

That is the level of proof autonomous commerce needs.

---

## References and current direction

Current evaluation work is converging on the same operational requirements: statistically valid uncertainty, transparent and reproducible benchmark practice, contamination-resistant test environments, traceable agent measurement, and evaluation tied to real-world workflows rather than demos.

Useful starting points include:

- NIST, **Practices for Automated Benchmark Evaluations of Language Models** (2026 draft guidance), including agent-system evaluation practice.
- NIST AI 800-3, **Expanding the AI Evaluation Toolbox with Statistical Models** (February 2026), on distinguishing benchmark measurements from generalized performance and quantifying uncertainty.
- NIST AITE, launched in 2026 with a sequestered evaluation environment designed to reduce train/test contamination.
- NIST TEVV-Athlon (August 2026 draft), an extensible test, evaluation, verification, and validation framework that explicitly includes agentic systems.
- NIST work on measurement probes for agentic ecosystems, emphasizing traceability and dynamic verification.

Use standards and third-party frameworks as inputs, not substitutes for buyer-specific evidence. A certificate is only as useful as its scope, freshness, measurement design, and connection to the actual delegated task.
