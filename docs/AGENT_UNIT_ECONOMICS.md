# Agent Unit Economics, Cost Controls & Margin Engineering

Agent businesses should optimize for **cost per successful customer outcome**, not cost per token.

A workflow can look cheap per model call and still lose money after retries, tool calls, browser sessions, paid data, storage, payment fees, human review, support, and failed runs.

## 1. Choose the economic unit

Pick the smallest unit that maps to customer value: a resolved ticket, qualified lead, booked meeting, reconciled invoice, accepted code change, processed claim, completed report, successful purchase, or another measurable outcome.

```text
attempt_cost = model + retrieval + tools + compute + storage + payments + human_review + support_allocation
cost_per_success = total_delivery_cost / successful_outcomes
success_rate = successful_outcomes / attempted_outcomes
```

If a workflow costs $0.40 per attempt but succeeds only half the time, direct cost per success is already $0.80 before support or overhead.

## 2. Build a complete cost ledger

Track costs separately instead of using one blended AI-spend number.

| Cost bucket | Examples |
|---|---|
| Inference | input/output units, images, audio, reasoning |
| Cache/retrieval | cache reads/writes, embeddings, vector search, reranking |
| Data | search, enrichment, proprietary datasets |
| Tools/APIs | CRM, email, maps, SaaS actions |
| Browser/compute | remote browser, VMs, sandboxes, serverless |
| Storage | files, logs, databases, traces |
| Payments | transaction fees, FX, refunds, chargebacks |
| Human review | QA, approvals, exception handling |
| Support | onboarding, account management, tickets |
| Reliability/compliance | observability, backups, identity checks, audits |

Allocate human exception work to the workflows and customers that create it.

## 3. Attribute every production run

At minimum record:

```text
customer_id
workflow_type
run_id
success_or_failure
model_provider
model_name
input_units
output_units
cache_units
tool_calls
paid_api_cost
compute_cost
human_review_minutes
retry_count
revenue_attributed
```

You should be able to answer which workflow, customer, model, and tool combination produces the most gross profit—and which failure mode wastes the most money.

## 4. Gross margin and contribution margin

```text
gross_profit = revenue - direct_delivery_cost
gross_margin = gross_profit / revenue

contribution_profit = revenue - variable_delivery_cost - variable_sales_and_support_cost
contribution_margin = contribution_profit / revenue
```

Direct delivery cost should include inference, tools, paid data, variable compute, payment fees, and required human review.

A customer can have attractive model economics but poor contribution economics if they require constant onboarding or exceptions.

## 5. Set a pricing floor

```text
minimum_price = expected_cost_per_success / (1 - target_gross_margin)
```

If expected cost per success is $8 and target gross margin is 80%, the minimum price is $40.

That is a floor, not necessarily the right price. If the customer receives $500 of value, price around value rather than simply marking up delivery cost.

## 6. Match pricing to cost behavior

### Subscription
Use when value and usage are predictable. Protect margin with included usage, overages, concurrency limits, and plan-specific access to expensive capabilities.

### Usage
Use when delivery cost scales with activity. Price in customer-native units such as workflow, document, minute, record, or successful task—not raw tokens unless customers actually buy tokens.

### Outcome pricing
Use when success is measurable. Include failed attempts in the cost model because the customer may only pay for successful outcomes.

### Setup + recurring
Useful when integrations, onboarding, configuration, or evaluation work is expensive.

### Marketplace take rate

```text
net_revenue = GMV * take_rate
contribution_profit = net_revenue - payment_cost - incentives - support - expected_loss
```

## 7. Route by economic value

Do not send every task to the same model.

| Tier | Task | Rule |
|---|---|---|
| 0 | deterministic logic | use code/rules if a model adds no value |
| 1 | simple extraction/classification | cheapest option meeting quality target |
| 2 | normal reasoning | balanced capability/cost |
| 3 | difficult, valuable work | stronger model when expected value justifies it |
| 4 | critical decision | strongest acceptable option plus approval when required |

Routing should consider expected task value, failure cost, latency, quality target, model cost, and expected retry cost.

The cheapest first attempt is not always cheapest overall: a stronger model may reduce retries and human review enough to lower cost per success.

## 8. Measure retry economics

Track:

```text
retry_rate = retried_runs / total_runs
average_attempts_per_success
cost_of_failed_attempts
cost_of_recovery
```

Set hard retry limits per step and workflow. Use timeouts, escalating strategies, and human escalation thresholds. Never allow an autonomous workflow to retry indefinitely.

## 9. Control context and caching

Long-lived agents often become more expensive because context grows silently. Use retrieval, structured state, summarization, relevance filtering, and hard context budgets.

For caching, measure net savings:

```text
cache_savings = avoided_compute_cost - cache_write_cost - cache_read_cost - invalidation_cost
```

Do not cache simply because a provider offers caching; stale results can increase correction and failure costs.

## 10. Give autonomous agents hard budgets

Every production agent should have deterministic spend limits by workflow, customer, billing period, and tool/provider.

Example policy fields:

```text
max_total_cost_per_workflow
max_model_cost
max_paid_tool_calls
max_browser_minutes
max_retries
approval_threshold
```

Tie spend authority to the delegated-authority model in [Agent Identity, Authority & Reputation](AGENT_IDENTITY_TRUST.md).

A useful value-aware rule is:

```text
max_delivery_cost = expected_revenue_per_success * (1 - target_margin)
```

## 11. Treat human review as a measurable cost

Track review rate, minutes per review, review cost per outcome, error catch rate, and value of prevented errors.

Then decide whether to automate more, improve evals, narrow agent authority, raise prices, or reserve review for high-risk cases.

Removing humans is not automatically an improvement. Removing unnecessary human work while preserving outcomes is.

## 12. Protect free-trial economics

Agent products can be easy to automate against. Measure trial cost per signup, activated user, and converted customer.

Use trial credits, concurrency limits, expensive-tool restrictions, anomaly detection, and reasonable identity checks. Do not let a free acquisition channel become an unbounded compute subsidy.

## 13. Review profitability by customer

Maintain a table like:

| Customer | Revenue | Models | Tools | Human | Support | Contribution profit | Margin |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | | | | | | | |
| B | | | | | | | |

Negative-contribution customers need a decision: reprice, reduce included usage, redesign the workflow, reduce support burden, add approval for expensive actions, or churn intentionally.

Revenue that destroys cash is not good revenue.

## 14. Detect cost anomalies

Alert on:

- cost per run above normal range,
- sudden input/context growth,
- retry spikes,
- tool-call loops,
- unexpected premium-model routing,
- browser/compute duration spikes,
- human escalation spikes,
- one customer consuming disproportionate resources.

Example operating rule:

```text
if run_cost > 3 * rolling_p95_cost:
    pause_new_actions
    preserve_trace
    require_operator_review
```

Connect economic controls to [Agent Security, Evals & Incident Response](AGENT_SECURITY_EVALS.md).

## 15. Evaluate cost and quality together

For every model or workflow change, compare:

| Metric | A | B |
|---|---:|---:|
| Success rate | | |
| Cost per attempt | | |
| Cost per success | | |
| P95 latency | | |
| Retry rate | | |
| Human review rate | | |
| Customer-visible defect rate | | |

A model that is 60% cheaper per call but doubles retries and escalations can be economically worse.

A useful metric is:

```text
quality_adjusted_cost = total_cost / acceptable_successes
```

## 16. Use lower-cost execution modes when latency has low value

Batch, flex, or reserved execution can improve economics depending on provider and workload. Good candidates include embeddings, bulk classification, scheduled reporting, offline evals, indexing, and backfills.

Keep real-time capacity for workflows where latency changes customer value. Economic routing should decide **when** work runs as well as which model runs it.

Provider pricing changes frequently, so keep vendor prices in a dated internal table rather than hard-coding the business model to one price sheet.

## 17. Agent-to-agent transaction economics

For a machine buyer:

```text
all_in_purchase_cost = seller_price + payment_fee + marketplace_fee + verification_cost + expected_failure_loss
```

For a machine seller:

```text
net_transaction_margin = transaction_revenue - delivery_cost - payment_fee - marketplace_fee - expected_refund_loss
```

See [Agent Commerce & Machine Payments](AGENT_COMMERCE.md) for transaction architecture.

## 18. Break-even and payback

```text
CAC_payback_months = CAC / monthly_contribution_profit_per_customer
break_even_customers = monthly_fixed_costs / contribution_profit_per_customer
automation_payback = automation_investment / monthly_cost_savings
```

Do not spend weeks automating a rare edge case to save a trivial monthly amount.

## 19. Margin engineering sequence

When margins are weak:

1. Verify price/value alignment.
2. Fix failures that waste work.
3. Reduce unnecessary retries.
4. Route simple work to cheaper models or deterministic code.
5. Trim excess context.
6. Cache stable repeated work when net savings are positive.
7. Batch non-urgent work.
8. Reduce expensive search/browser/data calls.
9. Target human review to risky cases.
10. Negotiate provider economics after workflow economics are understood.

Do not start by degrading reliability. Reliability is part of the product.

## 20. Founder margin dashboard

Track weekly:

- revenue,
- successful outcomes,
- success rate,
- cost per successful outcome,
- gross margin,
- contribution margin,
- retry rate,
- human review rate,
- P95 workflow cost,
- P95 latency,
- cost by provider/model,
- cost by customer.

Add these to the [Founder Scorecard](../templates/FOUNDER_SCORECARD.md) as they become material.

## 21. Benchmark template

```markdown
# Workflow economics benchmark

Workflow:
Customer segment:
Pricing model:
Revenue per successful outcome:
Attempts:
Successes:
Success rate:
Model cost:
Tool/API cost:
Data cost:
Compute cost:
Human review cost:
Payment cost:
Total variable cost:
Cost per attempt:
Cost per successful outcome:
Gross margin:
Retry rate:
Human review rate:
P95 run cost:
P95 latency:
Main margin leak:
Proposed change:
Expected savings:
Quality risk:
Rollback trigger:
```

## 22. Business opportunities in agent FinOps

The agent economy creates businesses around economic control itself:

- **cost observability:** unify model, tool, browser, data, and human costs at workflow level;
- **economic routing:** select models/providers using quality, latency, risk, and cost-per-success constraints;
- **budget control planes:** enforce spend authority across agents, providers, and tools;
- **margin optimizers:** detect retries, context inflation, costly customer cohorts, and tool loops;
- **agent procurement brokers:** route machine buyers using price, trust, quality, and service constraints;
- **benchmark networks:** aggregate permissioned data on cost per successful outcome by workflow and vertical.

Possible revenue models include SaaS, usage fees, enterprise licenses, transaction fees, and shared savings.

## 23. Launch checklist

- [ ] Define the customer-visible unit of success.
- [ ] Measure cost per attempt and per success.
- [ ] Attribute models, tools, data, compute, payments, and human review.
- [ ] See profitability by customer.
- [ ] Set a defensible pricing floor.
- [ ] Put hard limits on retries and autonomous spend.
- [ ] Route tasks by value and difficulty.
- [ ] Alert on abnormal workflow cost.
- [ ] Prevent free-trial abuse from creating unbounded spend.
- [ ] Benchmark cost and quality together.
- [ ] Keep provider pricing separate from the commercial model.
- [ ] Know the next margin leak to fix.

## Operating rule

**Revenue is not enough. Autonomy must produce value at a known, bounded, and improving cost.**

The strongest agent businesses will continuously decide how much intelligence, tooling, latency, and human oversight each outcome is worth—and enforce those decisions in production.