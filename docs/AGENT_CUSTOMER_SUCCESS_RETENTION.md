# Agent Onboarding, Support, Retention & Customer Success

A customer relationship does not become durable because an agent is impressive. It becomes durable when the customer reaches value quickly, can understand what the system is doing, receives fair support when things fail, and can prove that the product is worth renewing.

This playbook turns the post-sale lifecycle into an operating system for both human customers and autonomous buyers.

## 1. Define activation before onboarding

Activation is the first point at which the customer receives the promised business value, not the moment they create an account.

Define one activation event per business model:

| Business model | Good activation event |
|---|---|
| Productized agent service | first accepted deliverable produced |
| Vertical agent SaaS | first workflow completed successfully in production |
| Monitoring/data subscription | first actionable alert verified as useful |
| Outcome-fee service | first verified lead, recovery, resolution, or other payable outcome |
| Agent API | first successful paid invocation inside the buyer's real workflow |
| Marketplace | first transaction completed and accepted by both sides |
| Infrastructure | first downstream agent workflow meets target reliability/cost |

Avoid proxy activation such as account creation, tutorial completion, dashboard views, or API-key generation unless they directly represent customer value.

### Time to first value

Track:

```text
TTFV = activation_timestamp - contract_or_payment_timestamp
```

Segment TTFV by customer type, plan, acquisition channel, implementation complexity, and integration path. Median TTFV is useful, but the 90th percentile often reveals hidden onboarding friction.

A strong default target is: shorten TTFV before adding more onboarding content.

## 2. Create an onboarding contract

Every new customer should begin with an explicit onboarding contract that records:

- business outcome being purchased,
- success metric and measurement source,
- systems or datasets required,
- credentials and permission scopes,
- actions the agent may take autonomously,
- actions requiring approval,
- prohibited actions,
- expected traffic or workload,
- go-live target,
- rollback or disable path,
- customer owner,
- provider owner,
- support tier,
- billing start condition,
- acceptance criteria.

For autonomous customers, expose the same information in machine-readable form whenever possible.

Example:

```json
{
  "service": "invoice-collection-agent",
  "objective": "increase collections on invoices 15-60 days overdue",
  "activation": "first verified payment attributable to an agent action",
  "permissions": ["read_invoices", "send_email", "create_followup_task"],
  "approval_required": ["offer_discount", "change_payment_terms"],
  "forbidden": ["modify_bank_details"],
  "support_tier": "business",
  "go_live": "2026-09-01",
  "acceptance": {
    "min_success_rate": 0.95,
    "max_duplicate_actions": 0,
    "max_p95_latency_ms": 8000
  }
}
```

## 3. Separate implementation from adoption

Implementation asks: is the system technically connected?

Adoption asks: is the customer repeatedly receiving value?

Track them separately.

### Implementation checkpoints

1. required systems connected,
2. credentials validated,
3. permissions verified,
4. test data accepted,
5. sandbox workflow succeeds,
6. failure and rollback paths tested,
7. production scope approved,
8. first production execution verified.

### Adoption checkpoints

1. first successful outcome,
2. second successful outcome without provider intervention,
3. recurring usage reaches expected cadence,
4. customer can explain the value received,
5. customer has integrated the workflow into normal operations,
6. customer owner is willing to renew if performance remains stable.

A customer can be fully implemented and still be at severe churn risk.

## 4. Use acceptance criteria at go-live

Do not let go-live mean "we turned it on."

Define measurable acceptance criteria such as:

- task success rate,
- false-positive or false-action threshold,
- latency target,
- allowed cost per outcome,
- escalation rate,
- human-review rate,
- safety or policy violations,
- required audit evidence,
- maximum error budget during pilot.

If a criterion cannot be measured, it cannot reliably anchor an enterprise renewal later.

## 5. Build customer health from evidence

A useful health score should combine real outcome and risk signals, not vanity engagement.

Example inputs:

- activation completed,
- successful outcome rate,
- usage versus expected usage,
- reliability against SLA/SLO,
- unresolved support severity,
- billing or payment problems,
- customer ROI,
- human-review burden,
- stakeholder engagement,
- unresolved implementation blockers,
- expansion signals,
- negative feedback,
- contractual renewal proximity.

Example weighted score:

```text
Health =
  30% outcome attainment
+ 20% reliability
+ 15% expected usage
+ 15% ROI
+ 10% support condition
+ 10% commercial condition
```

Weights should differ by business model. A usage API may weight reliability heavily. An outcome-fee service should weight verified results more heavily.

### Do not hide the score

Operators should be able to explain why a customer is classified as healthy or at risk. A black-box churn score that cannot produce evidence is not an operating system.

## 6. Detect churn before cancellation

Useful leading indicators include:

- activation not completed by target date,
- TTFV far above cohort baseline,
- drop in successful outcomes,
- repeated retries or failures,
- increasing human-review burden,
- decreasing invocation frequency,
- consumption far below committed plan,
- support cases reopening,
- unresolved billing disputes,
- key champion stops engaging,
- customer disables important permissions,
- customer repeatedly rejects agent output,
- worsening unit economics for the customer,
- upcoming renewal with weak ROI evidence.

Create intervention thresholds rather than relying on intuition.

Example:

```text
IF no_activation_after_7_days
THEN implementation_review

IF successful_outcomes_7d < 70% of cohort_baseline
THEN reliability_investigation

IF usage_30d < 40% of contracted_expectation
THEN right_size_or_reactivate

IF renewal_due < 45_days AND ROI_report_missing
THEN generate_outcome_review
```

## 7. Make support operationally bounded

Support promises must be explicit enough that both customers and agents can route incidents correctly.

### Severity model

| Severity | Example | Initial response target | Behavior |
|---|---|---:|---|
| SEV-1 | widespread unsafe actions, major outage, material data risk | minutes | halt affected autonomy, incident command, frequent updates |
| SEV-2 | major degradation or important workflow blocked | under 1 hour for premium tiers | mitigation, escalation, active updates |
| SEV-3 | partial defect with workaround | business-hours target | queue by impact and recurrence |
| SEV-4 | question, request, cosmetic issue | best effort | normal support queue |

Never promise a resolution time you cannot control. Distinguish response targets from resolution targets.

### Support contract fields

Expose:

- support channel,
- support hours,
- severity taxonomy,
- target response times,
- escalation path,
- status endpoint,
- incident identifier format,
- evidence required from customer,
- maintenance policy,
- service-credit policy where applicable.

## 8. Support autonomous customers with machine-readable interfaces

An agent customer should not need a human to interpret every failure.

Return structured errors that distinguish:

- retryable provider failure,
- caller error,
- missing permission,
- expired entitlement,
- budget exceeded,
- rate limit,
- degraded capability,
- unavailable dependency,
- policy rejection,
- human approval required.

Example:

```json
{
  "status": "degraded",
  "error_code": "DEPENDENCY_UNAVAILABLE",
  "retryable": true,
  "retry_after_seconds": 30,
  "request_id": "req_123",
  "incident_id": "inc_456",
  "charged": false,
  "fallback_capability": "summary-basic"
}
```

Machine support should also expose status, planned maintenance, entitlement state, support tickets, and dispute state where commercially appropriate.

## 9. Preserve context on escalation

When an autonomous interaction escalates to a person, transfer:

- customer identity,
- request objective,
- conversation or workflow summary,
- actions already attempted,
- tools invoked,
- errors encountered,
- relevant evidence,
- approval state,
- remaining budget/deadline,
- recommended next action.

Do not force the customer to restate everything.

## 10. Handle incidents with customer-visible evidence

Incident communication should answer:

1. what customer-facing capability is affected,
2. when impact began,
3. what the customer should do now,
4. whether data, billing, or safety may be affected,
5. mitigation status,
6. next update time,
7. final resolution and prevention steps.

Do not leak secrets, internal credentials, private prompts, sensitive chain-of-thought, or unrelated tenant data in the name of transparency.

Useful post-incident artifacts include:

- affected request IDs,
- relevant timestamps,
- delivery receipts,
- usage and billing records,
- audit logs,
- SLA measurements,
- remediation actions,
- service-credit calculation.

## 11. Define refunds, credits, and make-goods before failure

Choose rules while incentives are calm.

Examples:

- refund a duplicate or invalid charge,
- do not charge for executions that failed before billable delivery,
- issue service credits when contracted availability targets are missed,
- re-run a failed deliverable when retry is safe,
- escalate disputed outcome-fee events for evidence review,
- compensate only for commitments actually made in the contract.

Avoid ad hoc concessions that vary by how loudly a customer complains.

## 12. Prove ROI continuously

Renewal should not depend on reconstructing twelve months of value from memory.

Maintain a customer-visible outcome ledger.

Examples:

- revenue generated,
- dollars recovered,
- hours saved,
- tickets resolved,
- claims processed,
- qualified meetings booked,
- response time reduced,
- fraud or risk events prevented,
- workflows completed,
- infrastructure spend avoided.

Simple ROI:

```text
ROI = (verified_value - total_customer_cost) / total_customer_cost
```

Also show assumptions and confidence. Do not present modeled value as verified value.

## 13. Run outcome reviews, not feature reviews

A useful customer review answers:

- what outcomes were promised,
- what outcomes were delivered,
- what failed,
- what changed in the customer's business,
- what should be removed,
- what should be expanded,
- whether price still matches value,
- which risks need mitigation before renewal.

Feature usage belongs only when it explains an outcome.

## 14. Build ethical retention

Retention should come from recurring measurable value, trust, and workflow fit.

Do not rely on:

- hidden cancellation paths,
- hostage data,
- artificial migration barriers,
- opaque auto-renewal,
- misleading ROI claims,
- unnecessary proprietary formats,
- punitive export fees,
- blocking access to customer-owned data.

Make cancellation and data export operationally clear. Strong products win on value, not friction.

## 15. Treat right-sizing as customer success

If a customer is consistently using far less than they pay for, proactively recommend the appropriate plan.

This may reduce short-term MRR but can improve long-term trust and gross revenue retention.

Likewise, expansion should be triggered by measured need:

- sustained capacity saturation,
- additional teams requesting access,
- repeated manual work adjacent to the current workflow,
- ROI materially above target,
- customer hitting plan limits,
- stronger compliance/support requirements,
- new autonomous buyers invoking the capability.

## 16. Renewal operating calendar

Example annual-contract cadence:

### 120-90 days before renewal

- verify commercial owner,
- review outcome attainment,
- identify unresolved reliability/support problems,
- confirm upcoming roadmap dependencies,
- calculate ROI.

### 90-60 days

- present outcome review,
- resolve plan mismatch,
- propose expansion only when justified,
- surface contract or compliance changes.

### 60-30 days

- finalize price and scope,
- confirm entitlements,
- resolve open disputes,
- complete procurement/security requests.

### 30-0 days

- execute renewal,
- verify billing migration,
- publish new term/entitlement state,
- confirm termination behavior if not renewed.

## 17. Define agent-to-agent renewal semantics

Autonomous buyers need deterministic lifecycle behavior.

A machine-readable commercial contract should make clear:

- renewal date,
- auto-renewal policy,
- notice period,
- pricing version,
- upcoming price change,
- entitlement changes,
- spend cap,
- termination effective time,
- grace period,
- data export window,
- deletion policy,
- outstanding invoice/dispute state.

Never silently increase an autonomous agent's spend authority because a subscription renewed.

## 18. Measure retention correctly

### Gross revenue retention

```text
GRR = (starting_recurring_revenue - churn - contraction) / starting_recurring_revenue
```

GRR excludes expansion.

### Net revenue retention

```text
NRR = (starting_recurring_revenue - churn - contraction + expansion) / starting_recurring_revenue
```

### Logo retention

```text
Logo retention = retained_customers / starting_customers
```

### Activation rate

```text
Activation rate = activated_new_customers / eligible_new_customers
```

### Support burden

```text
Support burden = support_cost / customer_revenue
```

### Save rate

```text
Save rate = at_risk_customers_retained / customers_entering_save_motion
```

Do not celebrate save rate without checking whether the customer subsequently receives value.

## 19. Cohort everything

Retention averages hide important differences.

Build cohorts by:

- acquisition month,
- customer segment,
- plan,
- business model,
- vertical,
- acquisition channel,
- implementation type,
- agent/model version,
- onboarding path,
- initial TTFV band.

Compare activation, support burden, outcome success, gross margin, GRR, NRR, and churn reason by cohort.

## 20. Create a churn taxonomy that feeds the backlog

Every churn event should have one primary reason and supporting evidence.

Suggested categories:

- never activated,
- insufficient value,
- reliability failure,
- support failure,
- missing capability,
- price/value mismatch,
- implementation burden,
- integration failure,
- security/compliance blocker,
- internal customer change,
- competitive replacement,
- budget loss,
- product sunset,
- provider-initiated termination.

For each category track preventability and owner.

A churn review should result in one of:

- product backlog item,
- reliability fix,
- onboarding change,
- pricing change,
- ICP refinement,
- sales qualification change,
- documentation change,
- no action because the customer was outside the target market.

## 21. Customer-success playbooks by business model

### Productized agent service

Focus on scope clarity, turnaround, acceptance criteria, human-review burden, and recurring outcome cadence.

### Vertical agent SaaS

Focus on implementation, workflow adoption, integration reliability, active outcome volume, stakeholder coverage, and expansion to adjacent workflows.

### Agent API

Focus on time to first successful production call, error semantics, uptime, latency, cost predictability, compatibility, and usage-to-value conversion.

### Marketplace

Track both sides. Buyer retention without healthy supply—or supply retention without buyer demand—is not durable.

### Infrastructure

Track downstream workflow success, failure attribution, cost impact, integration stability, and whether customers can safely scale usage.

## 22. Build feedback loops from support into product

Support data is operational telemetry.

At minimum classify:

- feature request,
- usability issue,
- reliability defect,
- policy rejection,
- integration failure,
- billing problem,
- misunderstanding,
- missing documentation,
- unsafe or unauthorized behavior,
- customer-specific configuration.

Track recurrence and affected revenue. A repeated low-severity issue may deserve higher priority than a dramatic one-off defect.

## 23. Evaluate customer-success automation

Before letting an agent autonomously intervene with customers, test whether it can:

- identify the correct account,
- use current contract and entitlement state,
- distinguish modeled from verified ROI,
- classify severity correctly,
- avoid promising unauthorized refunds,
- avoid changing price or terms without approval,
- preserve privacy boundaries,
- escalate regulated/high-risk issues,
- respect communication preferences,
- detect when the customer needs a human.

Create regression cases from real support failures.

## 24. Business opportunities in agent-native customer success

As autonomous services grow, new infrastructure categories become valuable:

- machine-readable onboarding and implementation APIs,
- agent health and adoption scoring,
- SLA evidence and service-credit automation,
- autonomous support triage,
- cross-agent incident coordination,
- machine-readable renewal and entitlement negotiation,
- customer outcome ledgers,
- churn-risk agents grounded in operational evidence,
- agent account-management infrastructure,
- support/reliability benchmarking across agent vendors.

A strong wedge is a narrow, auditable workflow where existing CRM or support systems assume a human operator.

## 25. Founder operating checklist

Before declaring customer success operational, verify:

- [ ] activation is defined as customer value,
- [ ] TTFV is measured,
- [ ] onboarding inputs and permissions are explicit,
- [ ] go-live acceptance criteria are measurable,
- [ ] implementation and adoption are tracked separately,
- [ ] health scores are explainable,
- [ ] churn indicators trigger interventions,
- [ ] severity and support targets are documented,
- [ ] autonomous buyers receive structured errors/status,
- [ ] human escalations preserve context,
- [ ] refunds and service credits follow policy,
- [ ] customer-visible outcome evidence accumulates continuously,
- [ ] renewal work starts before procurement deadlines,
- [ ] cancellation and export are straightforward,
- [ ] expansion is tied to measured need,
- [ ] GRR, NRR, activation, TTFV, support burden, and churn reasons are cohort-tracked,
- [ ] churn findings feed product/reliability/ICP backlogs,
- [ ] customer-success automation is evaluated before it receives commercial authority.

## 26. Minimum dashboard

A small agent business should be able to operate with this weekly view:

| Metric | Why it matters |
|---|---|
| New customers | cohort denominator |
| Activation rate | whether sales convert into value |
| Median / p90 TTFV | onboarding friction |
| Successful outcome rate | actual product performance |
| At-risk accounts | retention workload |
| Open SEV-1/2 incidents | trust/reliability risk |
| Support cost per account | service scalability |
| Verified customer ROI | renewal evidence |
| GRR | base durability |
| NRR | retention plus expansion |
| Churn reasons | learning loop |
| Gross margin by cohort | whether retention is economically healthy |

## Principle

**Customer success is the system that converts delivery evidence into trust, retention, and expansion. Optimize for recurring verified value—not engagement, lock-in, or the absence of complaints.**
