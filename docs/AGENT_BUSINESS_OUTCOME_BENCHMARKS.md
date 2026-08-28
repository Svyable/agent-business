# Agent Business Outcome Benchmarks

Use this operating system to compare agent configurations on business outcomes that founders and buyers actually care about: successful work, cost, latency, human-review burden, policy failures, recovery behavior, and repeatability.

A benchmark is not production authority, a timeless model ranking, or a substitute for customer evidence. It is a versioned experiment over fixed scenarios with explicit provenance and bounded simulated authority.

## 1. What this benchmark answers

For the same business workflow and starting state:

- Did the agent produce the required customer-visible outcome?
- What failure class occurred when it did not?
- How much model/tool spend, wall-clock time, and human review did it consume?
- Did it violate policy, claim success without evidence, loop, time out, leak tenant context, or leave partial side effects?
- Could it recover safely?
- How stable were the results across repeated runs?
- Which configuration is economically preferable for this workload, given transparent component metrics?

Do not collapse these dimensions into one opaque score. A configuration can be more capable yet economically or operationally worse.

## 2. Benchmark lifecycle

`draft -> scenario_ready -> executed -> reviewed -> published | superseded`

- **draft**: scenario and harness details are incomplete; no comparative claim is allowed.
- **scenario_ready**: fixed inputs, success criteria, authority envelope, stop conditions, and provenance are defined.
- **executed**: repeated runs are complete and raw aggregate metrics are captured.
- **reviewed**: evidence, failure classifications, economics, and interpretation have been checked.
- **published**: a portable result may be used for decision support with its version/date attached.
- **superseded**: retained for history after a newer scenario or harness version replaces it.

## 3. Scenario contract

Every scenario needs:

1. a stable `scenario_id` and semantic `scenario_version`;
2. a workflow class and business objective;
3. a deterministic starting state or fixture reference;
4. allowed tools and data classes;
5. a simulated authority envelope;
6. explicit success criteria and evidence required to prove success;
7. stop conditions for loops, time, cost, policy breaches, and unsafe side effects;
8. whether the scenario is public or held-out;
9. a contamination note explaining what the evaluated agent can know in advance.

Public scenario text may be used for development. Held-out answer keys, restricted fixtures, private customer data, credentials, or secret prompts must never be copied into public result records.

## 4. Starter scenario pack

`benchmarks/BUSINESS_SCENARIOS.json` provides five portable scenario definitions:

- `revenue-ops.qualification-handoff.v1` — qualify a sales opportunity from mixed buyer evidence without inventing authority or stage advancement;
- `customer-success.incident-renewal.v1` — respond to a service incident while preserving renewal evidence and bounded communications;
- `finance.invoice-reconciliation.v1` — reconcile a synthetic invoice/payment mismatch without fabricating tax or bank facts;
- `research.market-brief.v1` — produce an evidence-classified market brief with dated sources and uncertainty;
- `multi-agent.vendor-selection.v1` — coordinate research, risk, and economics agents to recommend a vendor while preserving provenance and decision ownership.

These scenarios are fixtures, not claims about any vendor or model.

## 5. Result contract

A result record captures two layers.

### Per-configuration aggregate

For each configuration record:

- agent revision and policy/prompt version refs;
- provider/model labels as observed strings, not endorsement;
- tool and harness versions;
- run count and observation window;
- successful, partial, and failed run counts;
- failure taxonomy counts;
- p50/p95 latency;
- model/tool cost in minor currency units;
- human-review minutes;
- escalations and takeover count;
- policy violations and unsafe side-effect count;
- recovery attempts and successful recoveries;
- throughput where meaningful;
- component scores for capability and operations/economics.

### Interpretation

Interpretation must be separate from measurement. State which result is measured, which field is estimated, and what founder/editorial conclusion is being drawn.

## 6. Failure taxonomy

Use stable failure classes so results remain comparable:

- `hallucinated_completion` — claimed success without required outcome evidence;
- `wrong_tool_success_claim` — tool result does not support the asserted business outcome;
- `policy_violation` — declared policy boundary was crossed;
- `timeout` — time limit exceeded;
- `retry_storm` — retry/loop limit exceeded or economically uncontrolled looping occurred;
- `partial_side_effect` — a consequential action partially executed before failure;
- `stale_data` — decision relied on data outside the allowed freshness window;
- `cross_tenant_leakage` — tenant boundary was violated;
- `recovery_failure` — rollback/recovery was attempted but did not restore the declared safe state;
- `human_takeover` — benchmark completed only after a human assumed execution responsibility;
- `other` — only with a human-readable explanation.

A successful run may still have a policy or economic problem; keep those counters separate.

## 7. Repeated-run methodology

Never publish a comparative superiority claim from one run.

For each compared configuration:

1. run the same scenario version and fixed fixture set;
2. use at least five repetitions before a `published` comparison;
3. record deterministic seeds where the harness/provider supports them;
4. preserve the full run count rather than only successful trials;
5. report success proportion plus latency/cost/review distributions;
6. report the observation period and exact environment versions;
7. rerun after material model, tool, prompt, policy, or harness changes.

The validator enforces a minimum of five runs for published records and refuses statistical-superiority language unless both compared configurations have at least 20 runs. This is a guardrail, not a guarantee of statistical power.

## 8. Component scores

### Capability score

Capability should reflect outcome completion only. The starter record uses:

`100 * (successful_runs + 0.5 * partial_runs) / run_count`

This is intentionally simple and transparent.

### Operational/economic score

Do not derive one universal hidden formula. Record the decision thresholds that matter for the scenario:

- maximum acceptable cost per successful outcome;
- maximum p95 latency;
- maximum human-review minutes per run;
- zero-tolerance safety/policy failures where applicable;
- minimum recovery success rate.

Then expose the measured components and whether each threshold passed. Founders may choose different trade-offs for different verticals.

## 9. Economics handoff

Benchmark economics are operational evidence, not a complete ROI model.

Calculate and retain:

- `cost_per_success_minor = total_cost_minor / successful_runs` when successes are nonzero;
- expected cost after retries from observed total spend divided by successful outcomes;
- review burden per run;
- successful outcomes per hour when meaningful;
- recovery cost and takeover burden where measured.

Feed realistic candidate economics into `workflow-roi`; do not use benchmark score alone as proof of customer ROI or contribution margin.

## 10. Authority and safety

Benchmark authority is simulated and must be explicitly marked `simulation_only: true`.

A benchmark harness may model sending an email, issuing a refund, moving money, modifying CRM state, or calling a production-like tool, but the public record never grants real authority. Real production authority still comes from the principal and operating environment.

Use deterministic fixtures, sandboxes, mocks, or non-consequential test tenants wherever possible. Never place production credentials, private customer data, payment data, secret prompts, or restricted answer keys in portable public benchmark artifacts.

## 11. Reproducibility provenance

Every executed result must identify:

- scenario pack version;
- scenario ID/version;
- harness version;
- agent revision;
- model/provider label;
- prompt/policy refs;
- tool version refs;
- environment/fixture version;
- observation timestamps;
- seed policy;
- evidence references.

A provider silently changing model behavior is one reason to date results. Treat benchmark publications as observations, not timeless rankings.

## 12. Worked comparison

`examples/BUSINESS_BENCHMARK_COMPARISON.json` compares two fictional configurations on the revenue-operations scenario. It demonstrates how a configuration with slightly higher capability can still require more human review and higher cost.

The example is synthetic. It does not rank real providers or models.

## 13. Validation

Start from the conservative template:

```bash
cp templates/BUSINESS_BENCHMARK_RECORD.json my-benchmark.json
python scripts/validate_business_benchmark.py my-benchmark.json
```

The starter is intentionally `draft`. To publish, provide executed results, current evidence, at least five repetitions per configuration, complete provenance, explicit component metrics, and a measured/estimated/interpretation split.

## 14. Founder operating loop

1. Choose a decision-relevant business workflow.
2. Freeze scenario, fixtures, authority, and stop conditions.
3. Run candidate configurations repeatedly under the same scenario version.
4. Preserve failures and recovery attempts, not just successes.
5. Compare capability separately from operational/economic burden.
6. Review safety, provenance, and statistical limits.
7. Feed plausible economics into `workflow-roi` and production readiness into implementation/release systems.
8. Publish only versioned, dated, reproducible observations.
