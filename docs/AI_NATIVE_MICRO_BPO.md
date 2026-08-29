# AI-Native Micro-BPO & Outcome-Managed Services

An agent founder does not have to sell software.

A powerful early business model is to sell a **measurable business outcome** and use agents, software, vendors, and human reviewers behind the scenes to deliver it. This is an AI-native managed service: smaller and more specialized than traditional BPO, but more accountable than a generic SaaS subscription.

Use this model when buyers care about the result more than the software interface.

> Sell the completed business job. Keep the delivery system as your internal advantage.

This playbook complements:

- [`BUSINESS_MODELS.md`](BUSINESS_MODELS.md) for picking a wedge;
- [`AGENT_WORKFLOW_ROI.md`](AGENT_WORKFLOW_ROI.md) for cost-versus-value analysis;
- [`AGENT_PRICING_PACKAGING_DEAL_DESK.md`](AGENT_PRICING_PACKAGING_DEAL_DESK.md) for pricing and commercial controls;
- [`AGENT_REVENUE_OPERATIONS.md`](AGENT_REVENUE_OPERATIONS.md) for pipeline and handoff;
- [`AGENT_CUSTOMER_IMPLEMENTATION_GO_LIVE.md`](AGENT_CUSTOMER_IMPLEMENTATION_GO_LIVE.md) for implementation/go-live;
- [`AGENT_CUSTOMER_SUCCESS_RETENTION.md`](AGENT_CUSTOMER_SUCCESS_RETENTION.md) for retention and expansion.

## Why this model matters now

Agentic systems are increasingly capable of completing multi-step business work, while buyers are becoming less interested in paying simply for software seats or raw model usage. Service providers are also moving toward outcome-oriented operating models.

For an early founder, that creates a useful wedge:

1. sell a business outcome before building a large product;
2. use agents and humans to learn the workflow in production;
3. measure the true cost and failure modes;
4. standardize the repeatable parts;
5. decide later whether to remain a managed service, become software, or expose an API/agent capability.

The business advantage is not “we use AI.” It is **we reliably own this narrow result**.

---

## 1. Decide whether a workflow belongs in a managed-service model

Score each candidate from 0–3.

| Dimension | 0 | 1 | 2 | 3 |
|---|---:|---:|---:|---:|
| Economic pain | Nice-to-have | Minor cost | Material cost | Direct revenue/cash/risk impact |
| Frequency | Ad hoc | Monthly | Weekly | Daily/high-volume |
| Measurable completion | Subjective | Proxy only | Mostly measurable | Binary/reconstructable outcome |
| Digital inputs | Mostly offline | Manual collection | Mixed | Available through systems/APIs/docs |
| Workflow repeatability | Unique every time | Some pattern | Repeated stages | Highly standardized core |
| Agent leverage | Low | Assistive | Majority of steps | Strong autonomous leverage with bounded exceptions |
| Human-review burden | Expert-heavy | Frequent | Exception-based | Low, targeted review |
| Reversibility | Irreversible/high stakes | Difficult | Mostly reversible | Easily corrected/replayed |
| Buyer ownership | No clear owner | Shared | Clear operator | Clear budget owner + KPI |
| Time to proof | >90 days | 60–90 days | 30–60 days | <30 days |

**Interpretation**

- **24–30:** strong candidate for an AI-native managed service.
- **18–23:** promising, but design around the weakest dimensions.
- **12–17:** start as consulting/productized service until the workflow is better understood.
- **<12:** avoid promising a repeatable outcome yet.

A high agent-leverage score does not override poor measurability or high consequence. A workflow that is autonomous but impossible to verify is a bad outcome-priced service.

---

## 2. Choose the unit of value before choosing the technology

Define one customer-visible unit that can be counted without arguing.

Good units include:

- qualified opportunity accepted by sales;
- overdue invoice resolved or advanced to an agreed state;
- compliant proposal delivered before deadline;
- support issue resolved within the allowed policy boundary;
- document package processed and accepted;
- reconciliation exception cleared;
- account research brief accepted against a rubric.

Weak units include:

- agent messages sent;
- tokens consumed;
- workflows started;
- research hours saved without a baseline;
- “AI productivity”; or
- arbitrary internal agent scores.

### Completion contract

For every billable or promised outcome, define:

1. **trigger** — what starts the work;
2. **eligible population** — which cases count;
3. **completion condition** — what observable state means success;
4. **exclusions** — cases outside scope;
5. **customer dependencies** — what the buyer must provide;
6. **evidence** — how completion can be reconstructed;
7. **dispute rule** — what happens when the parties disagree.

If the completion contract is fuzzy, use a fixed-fee pilot rather than outcome pricing.

---

## 3. Package the service around the buyer's KPI

A credible managed-service offer should fit on one page.

Use [`templates/OUTCOME_MANAGED_SERVICE_OFFER.md`](../templates/OUTCOME_MANAGED_SERVICE_OFFER.md).

The core sentence is:

> We help **[specific buyer]** move **[defined workload]** from **[baseline state]** to **[measurable completed state]** within **[service level]**, for **[commercial model]**, while escalating **[defined exception classes]** to **[human owner]**.

### Minimum offer anatomy

**Buyer**
- one operational owner;
- one budget owner if different;
- one KPI that already matters.

**Workload**
- start trigger;
- inclusion/exclusion rules;
- expected monthly volume;
- seasonality and peaks.

**Outcome**
- acceptance test;
- evidence source;
- deadline/service level;
- quality threshold.

**Exceptions**
- cases the service will not decide autonomously;
- escalation owner;
- review SLA;
- stop conditions.

**Commercial terms**
- minimum commitment;
- variable unit if any;
- included volume;
- overage behavior;
- fees/credits/limits;
- attribution rules for gainshare.

Do not sell “unlimited automation.” Sell a bounded service with known completion semantics.

---

## 4. Pick a commercial model that matches evidence quality

| Model | Best when | Primary risk | Guardrail |
|---|---|---|---|
| Fixed monthly fee | workload and support effort are predictable | volume spikes destroy margin | included volume + overage/cap |
| Per completed outcome | completion is objectively verifiable | disputes over what counts | deterministic completion contract |
| Minimum + per outcome | buyer wants predictability and provider needs downside protection | complexity | simple base + one variable unit |
| Gainshare | value can be causally attributed | fighting over attribution | baseline, holdout/comparison, attribution window |
| Capacity subscription | buyer needs reserved throughput | idle capacity/value mismatch | explicit capacity/SLA unit |
| Setup + managed fee | integrations/configuration are material | setup becomes hidden consulting | fixed implementation scope |

### Recommended default for a first customer

Use:

**setup fee + monthly minimum + one transparent variable unit**.

Example structure:

- one-time implementation fee;
- monthly service minimum covering fixed operations/support;
- per accepted completed outcome above included volume;
- monthly spend cap;
- explicit non-billable categories such as retries, duplicates, provider faults, or out-of-scope cases.

This is usually easier to explain and safer than pure gainshare.

---

## 5. Build the delivery system as a service factory

Treat the internal operation as a queue of work, not as a chatbot.

### Core stages

1. **Intake** — capture a valid unit of work.
2. **Normalize** — validate required fields, deduplicate, classify.
3. **Plan** — determine allowed workflow and dependencies.
4. **Execute** — use agents/tools/vendors for bounded actions.
5. **Review** — route exception or consequential cases to humans.
6. **Verify** — test the customer-visible acceptance condition.
7. **Record** — preserve completion evidence and cost.
8. **Deliver/update** — write the result into the customer's operating system.
9. **Reconcile** — confirm billing, exceptions, reversals, and unresolved cases.
10. **Learn** — classify failures and improve the runbook/evals.

### Every case should end in one of five states

- `completed`
- `customer_blocked`
- `provider_blocked`
- `human_review_required`
- `failed`

Never hide non-completion inside “processed.”

---

## 6. Design the human + agent staffing model

Humans should handle **judgment bottlenecks**, not manually repeat every task.

For each 100 units of work, estimate:

- agent-completed without review;
- agent-completed with sampled QA;
- human approval required;
- human rescue/rework required;
- fully manual fallback;
- abandoned/out-of-scope.

### Review capacity formula

Use:

`review_hours = volume × review_rate × average_review_minutes / 60`

Then add a safety buffer for peaks and incidents.

If 2,000 monthly cases require 15% review at 8 minutes each:

`2,000 × 0.15 × 8 / 60 = 40 review hours/month`

A service that appears “fully automated” but silently requires 120 expert hours is not an agent business; it is a labor business with an AI front end.

### Track why humans intervene

Use categories such as:

- missing information;
- low confidence;
- policy exception;
- customer-specific judgment;
- legal/compliance boundary;
- tool/provider failure;
- ambiguous outcome;
- quality defect.

The best automation roadmap comes from the distribution of human interventions.

---

## 7. Model gross margin from completed outcomes

Revenue per successful outcome is only useful if the provider knows the **fully loaded delivery cost**.

### Variable cost per attempted unit

Include:

- model inference;
- context/retrieval;
- paid data;
- tool/API fees;
- external agent/vendor spend;
- compute;
- human review;
- support directly caused by the unit;
- expected retry/rework;
- payment/marketplace fees when material.

### Failure-adjusted cost per successful outcome

Use:

`cost_per_success = total_variable_delivery_cost / successful_outcomes`

Do not divide only by attempts.

### Contribution per success

`contribution_per_success = net_revenue_per_success - cost_per_success`

### Managed-service margin

For a period:

`gross_margin = (revenue - variable_delivery_cost - allocated_delivery_labor) / revenue`

Also track fixed operating cost separately:

- on-call/support coverage;
- implementation amortization;
- compliance/security overhead;
- observability/eval tooling;
- customer-specific maintenance.

A healthy service can tolerate exceptions without turning every edge case into a margin crisis.

---

## 8. Run a 30-day paid pilot

A pilot should answer a commercial question, not merely prove that an agent can run.

### Before day 1

Record:

- historical baseline;
- sample size/volume expected;
- customer acceptance criteria;
- known exclusions;
- production authority boundaries;
- human-review plan;
- cost ceiling;
- stop conditions;
- expansion decision rule.

### Week 1 — observe and shadow

- map actual input variance;
- run on historical or shadow workload where appropriate;
- identify exception classes;
- establish real handling time and human effort;
- validate evidence capture.

### Week 2 — bounded live production

- expose a limited cohort or volume;
- require human approval for consequential steps;
- measure completion, defect, latency, review burden, and cost;
- investigate every failure category.

### Week 3 — optimize the bottleneck

Do not optimize token cost first unless it is actually the bottleneck.

Prioritize the largest source of:

1. customer-visible failure;
2. human review;
3. rework;
4. latency;
5. variable delivery cost.

### Week 4 — commercial decision

Choose one:

- **expand** — outcome, quality, and economics are strong;
- **continue pilot** — evidence is promising but incomplete;
- **narrow scope** — one subset works well;
- **change price** — value exists but economics do not;
- **stop** — no durable buyer value or delivery advantage.

### Pilot scorecard

At minimum track:

| Metric | Meaning |
|---|---|
| Eligible units | Work that truly fit scope |
| Successful outcomes | Accepted completed units |
| Success rate | Successful / eligible |
| Median + p95 cycle time | Delivery speed and tail |
| Human review rate | Operational burden |
| Rework rate | Quality/margin drag |
| Customer-blocked rate | Dependency friction |
| Provider/tool failure rate | External fragility |
| Cost per success | Fully loaded variable economics |
| Customer value per success | Avoided cost, revenue, cash, or risk where measurable |
| Contribution per success | Net revenue minus delivery cost |

---

## 9. Three concrete founder blueprints

The prices below are **validation hypotheses**, not market facts. Test them with buyers.

### Blueprint A — Accounts-receivable cash acceleration

**Buyer:** agencies, consultancies, B2B services, light industrial/service SMBs.

**Problem:** invoices age because follow-up is inconsistent and finance teams prioritize manually.

**Managed outcome:** move eligible overdue invoices into one of: paid, payment date committed, documented dispute, or human escalation.

**Workflow:**

1. ingest invoice/customer state;
2. deduplicate and classify aging/risk;
3. generate compliant/customer-approved follow-up;
4. send through authorized channel;
5. capture replies/payment promises/disputes;
6. update accounting/CRM state;
7. escalate sensitive or disputed cases;
8. reconcile payment outcomes.

**Do not autonomously:** threaten legal action, make unauthorized concessions, change contractual balances, or decide material disputes.

**Pilot:** 50–200 overdue invoices, 30 days.

**Price hypothesis:** $1,000–$4,000 monthly minimum plus a small success component tied only to clearly attributable recovered/advanced cash.

**Core metrics:** dollars advanced, days-to-payment movement, contact-to-response rate, dispute identification rate, review burden, cost per resolved invoice.

**Expansion path:** collections prioritization -> dispute routing -> cash forecasting -> AR operations service.

---

### Blueprint B — Proposal / RFP throughput service

**Buyer:** B2B service firms, agencies, contractors, consultancies, enterprise sales teams.

**Problem:** experts spend expensive hours finding evidence, mapping requirements, drafting, and checking proposals.

**Managed outcome:** deliver a review-ready, requirement-mapped proposal package by an agreed deadline.

**Workflow:**

1. intake RFP and deadline;
2. parse requirement matrix;
3. identify missing inputs;
4. retrieve approved prior claims/evidence;
5. draft compliant sections;
6. validate requirement coverage;
7. route pricing/legal/security sections to named owners;
8. assemble final review package.

**Do not autonomously:** invent capabilities, certifications, customer references, pricing authority, contract commitments, or regulated claims.

**Pilot:** 5–10 proposals or one month of eligible requests.

**Price hypothesis:** $2,000–$8,000 monthly managed-service fee, or $500–$2,500 per accepted proposal package depending on complexity.

**Core metrics:** expert hours avoided, cycle time, requirement coverage, defect/rework rate, on-time delivery, win-rate signal only when enough data exists.

**Expansion path:** proposal ops -> security questionnaire support -> deal desk evidence -> full bid operations.

---

### Blueprint C — Support back-office resolution service

**Buyer:** SaaS/ecommerce businesses with repeatable support operations.

**Problem:** support agents spend time on routine research, account checks, policy lookups, and repetitive resolutions.

**Managed outcome:** resolve one bounded class of support issue end-to-end or return a complete human-escalation packet.

**Workflow:**

1. classify eligible case;
2. retrieve account/order/product context;
3. verify policy and authority;
4. execute allowed remediation;
5. communicate resolution;
6. update support/CRM systems;
7. capture evidence and customer response;
8. escalate exceptions.

**Do not autonomously:** make high-value refunds outside authority, override fraud/safety controls, expose private account data, or fabricate policy exceptions.

**Pilot:** one ticket category with 200–1,000 monthly cases.

**Price hypothesis:** monthly minimum plus per verified resolution; do not bill the same as a resolution when the case is merely routed to a human unless the commercial contract explicitly defines that unit.

**Core metrics:** verified resolution rate, cost per resolution, escalation rate, reopen rate, customer response time, human minutes per case.

**Expansion path:** one issue category -> multiple bounded categories -> proactive customer operations -> retention workflows.

---

## 10. Know when to stay a managed service

Remain service-led when:

- customer workflows differ materially;
- integration work is a major part of value;
- buyer confidence depends on human accountability;
- exceptions contain valuable domain knowledge;
- high-touch service commands strong margins;
- the market is still changing faster than a product interface should.

Managed service is not a failure to become SaaS. It can be the superior business model when the provider can standardize operations without forcing every customer into identical software.

---

## 11. Know when to productize

Productize a component when all of the following are true:

- the same workflow appears across several customers;
- inputs/outputs are stable;
- exception types are known;
- acceptance criteria are machine-testable;
- onboarding/configuration is repeatable;
- customers want self-service or embedded API access;
- the component has positive unit economics without custom heroics.

### Productization ladder

1. **Founder-operated service** — learn the workflow manually.
2. **Agent-assisted productized service** — repeat a fixed offer.
3. **Managed outcome service** — own measurable delivery with operational SLAs.
4. **Configurable platform** — customers operate more of the workflow themselves.
5. **API/agent capability** — machine buyers can purchase the narrow function directly.

Do not jump from step 1 to step 5 because the protocol is exciting.

---

## 12. Build a moat from operational learning

Generic model access is not a durable advantage.

More defensible assets include:

- proprietary exception taxonomy;
- customer-approved workflow templates;
- evaluation cases grounded in real failures;
- high-quality outcome and cost benchmarks;
- integrations and data mappings;
- routing/policy logic;
- reputation for reliable completed outcomes;
- channel partnerships;
- historical operating data that improves forecasting and capacity planning;
- evidence-backed playbooks for narrow vertical work.

Every delivered unit should make the service easier to price, verify, or improve.

---

## 13. Avoid these managed-service traps

### Selling labor savings instead of buyer value

If the provider tells the buyer “we reduced our own labor,” the buyer may ask for a lower price. Anchor the offer to the customer's KPI and completed business outcome.

### Pure gainshare with weak attribution

Do not claim revenue caused by the service when many other factors could explain it. Use controlled or conservative attribution and a minimum fee.

### Hiding humans

Human review is not automatically bad. Hidden human cost is bad. Track it and price it.

### Taking responsibility for uncontrolled dependencies

If the customer controls critical inputs, document those dependencies and pause the SLA clock appropriately rather than absorbing unlimited blocked time.

### Over-automating consequential decisions

A profitable service does not need maximum autonomy. It needs reliable economics. Human approval can be part of a strong model when the review rate is bounded.

### Calling every attempt an outcome

Retries, duplicates, partial work, and escalations are not completed outcomes unless explicitly defined that way in the contract.

---

## 14. Founder operating cadence

### Daily

- failed/blocked workload;
- high-severity exceptions;
- SLA breaches or near misses;
- unusual human-review spikes;
- provider/tool incidents.

### Weekly

- success rate;
- review and rework rate;
- cost per success;
- top three failure categories;
- customer-blocked work;
- expansion or scope-narrowing opportunities.

### Monthly

- gross margin by customer/workflow;
- value delivered versus baseline;
- pricing fit;
- automation opportunity from review reasons;
- retention/expansion evidence;
- productization candidates.

---

## 15. First seven days for a founder

**Day 1:** choose one workflow scoring 24+ on the fit matrix.

**Day 2:** interview 5 buyers about the current process, baseline, failure cost, and who owns the KPI.

**Day 3:** define the completion contract and exclusions.

**Day 4:** model one unit of delivery cost, including human review and retries.

**Day 5:** fill out the one-page outcome offer template.

**Day 6:** propose a 30-day paid pilot with a bounded workload and explicit acceptance criteria.

**Day 7:** build only the minimum delivery system needed to complete the first real unit safely.

Do not build a platform before a buyer agrees that the outcome is worth paying for.

---

## Evidence and further reading

Current ecosystem direction motivating this playbook includes:

- McKinsey, **“Agentic AI and the future of global business services”** (August 11, 2026), on agentic AI changing shared-service operating models: https://www.mckinsey.com/capabilities/operations/our-insights/agentic-ai-and-the-future-of-global-business-services
- Gartner, **“Reinvent BPO With Agentic AI to Enhance Business Value”** (August 21, 2026), on AI-powered business delivery and outcome-based sourcing: https://www.gartner.com/en/documents/8291321
- Gartner, **“Transition Agentic Applications Pricing From Seats to Quantifiable Business Activities or Outcomes”** (August 4, 2026): https://www.gartner.com/en/documents/8221561

These references are directional evidence, not universal pricing or performance claims. Validate the offer against the actual buyer, workflow, jurisdiction, and operating data.