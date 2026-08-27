# Agent Founder Tool Directory

A practical, conflict-disclosed directory for choosing the minimum viable stack behind an agent business.

This is not a list of everything that exists. It is a shortlist organized around founder jobs-to-be-done. The default is to choose the simplest tool that clears the requirement, preserve portability, and add complexity only when measured demand justifies it.

## How to use this directory

Before choosing a tool, write down:

1. the workflow it must support,
2. the failure that would be most expensive,
3. the data it will handle,
4. the expected usage and budget,
5. the lock-in you are willing to accept,
6. the evidence that would make you switch.

Then compare tools on requirements rather than brand familiarity.

### Selection scorecard

Score each candidate from 1–5 on the dimensions that matter to the workload:

| Dimension | What to evaluate |
|---|---|
| Outcome fit | Does it solve the actual workflow rather than a neighboring problem? |
| Reliability | SLOs, failure modes, retries, durability, incident history, support path |
| Security | auth, scoped permissions, secret handling, auditability, isolation |
| Agent ergonomics | APIs, structured output, webhooks/events, tool calling, machine-readable errors |
| Observability | traces, usage, cost attribution, debugging, exportability |
| Portability | open standards, data export, interchangeable interfaces, migration cost |
| Economics | fixed fees, usage fees, minimums, egress, support and human-ops costs |
| Compliance fit | data residency, retention, subprocessors, regulated-workflow support |
| Speed to value | integration effort and time to first successful paid outcome |

Do not average away a hard requirement. A tool that scores 5/5 on convenience but fails a security or regulatory constraint is not eligible.

## Default founder stack

For an early agent business, the default stack should stay small:

- one primary model provider plus a tested fallback only if downtime is expensive,
- one application/runtime platform,
- one relational database,
- one observability/eval layer,
- one payment provider,
- one CRM or lightweight pipeline tracker,
- one support inbox,
- one analytics layer,
- one source-control and deployment workflow.

Every additional vendor becomes another credential, contract, failure mode, privacy surface, bill, and dependency to monitor.

---

## 1. Models and inference

### OpenAI

Official: https://openai.com/api/

**Best for**
- teams that want a broad model/API surface for reasoning, coding, tool use, multimodal work, and structured outputs,
- products that benefit from one vendor covering multiple capability classes,
- founders who want strong ecosystem support and production tooling.

**Avoid when**
- a regulated or customer-specific deployment requirement cannot be met,
- the economics of the target workload are materially better on a smaller/specialized model,
- single-provider dependence would violate a customer SLO or procurement rule.

**Pricing model:** primarily usage-based; confirm current model-specific pricing before launch.

### Anthropic

Official: https://www.anthropic.com/api

**Best for**
- reasoning-heavy and coding workflows,
- tool-using agents that need strong instruction following,
- teams that want a second frontier-provider option for resilience or workload routing.

**Avoid when**
- required modalities, regions, commercial terms, or integrations are not available for the workload,
- the use case can be served more cheaply by a smaller model without reducing successful outcomes.

**Pricing model:** primarily usage-based; verify current model-specific pricing.

### Google Gemini API / Vertex AI

Official: https://ai.google.dev/ and https://cloud.google.com/vertex-ai

**Best for**
- Google Cloud-native teams,
- multimodal or long-context workloads,
- organizations that want model access integrated with cloud IAM, data, and enterprise operations.

**Avoid when**
- the product would take on unnecessary cloud complexity solely to access a model,
- portability across providers is a hard requirement and the implementation becomes cloud-specific.

**Pricing model:** usage-based, with cloud/service-specific commercial terms.

### Model-selection rule

Benchmark models on the paid workflow, not generic leaderboards. Track at least:

`cost per successful outcome = total model + tool + retry + review cost / verified successful outcomes`

A more expensive model can be cheaper if it materially reduces retries, human review, or failed outcomes.

---

## 2. Application hosting and runtime

### Vercel

Official: https://vercel.com/

**Best for**
- web-first products,
- Next.js applications,
- teams optimizing for fast deployment and preview environments,
- agent frontends and API surfaces that fit serverless/runtime constraints.

**Avoid when**
- the workload needs long-lived stateful workers or specialized infrastructure not suited to the platform,
- egress/runtime economics become worse than a simpler cloud or container deployment.

**Pricing model:** plan + usage based.

### Cloudflare Workers

Official: https://workers.cloudflare.com/

**Best for**
- globally distributed low-latency request handling,
- edge APIs, gateways, lightweight agents, queues, and event-driven workloads,
- teams that benefit from Cloudflare security/network primitives.

**Avoid when**
- the workload depends on unsupported runtime behavior or long-running compute patterns,
- the team would create unnecessary platform coupling for a conventional backend.

**Pricing model:** plan + usage based.

### AWS

Official: https://aws.amazon.com/

**Best for**
- enterprise procurement requirements,
- workloads needing a broad infrastructure surface, regional controls, networking, queues, storage, and managed services,
- teams with existing AWS expertise.

**Avoid when**
- the startup is pre-revenue and the infrastructure surface will add operational burden without customer value,
- a managed platform can provide equivalent outcomes with less complexity.

**Pricing model:** service-specific usage pricing.

### Runtime rule

Prefer boring deployment until runtime complexity is purchased by real demand. Durable execution, multiple regions, provider failover, and advanced queueing should follow measured failure modes and customer SLOs—not architecture aesthetics.

---

## 3. Databases, state, and memory

### Supabase

Official: https://supabase.com/

**Best for**
- founders who want managed Postgres plus auth/storage/realtime primitives,
- rapid product development with a relational source of truth,
- teams that value SQL portability.

**Avoid when**
- specialized scale, networking, or compliance requirements exceed the managed offering,
- the team is tempted to store uncontrolled agent memory directly in authoritative business tables.

**Pricing model:** plan + usage based.

### Neon

Official: https://neon.com/

**Best for**
- serverless Postgres workloads,
- branchable development/test databases,
- teams that want standard Postgres with elastic operations.

**Avoid when**
- the product needs an all-in-one backend rather than primarily a database,
- workload characteristics or region requirements are a poor fit.

**Pricing model:** plan + usage based.

### Database rule

Keep authoritative execution state in explicit schemas. Treat vector search and agent memory as retrieval layers with provenance, TTL, permissions, and deletion behavior—not as an unbounded substitute for transactional state.

---

## 4. Evals, tracing, and observability

### LangSmith

Official: https://www.langchain.com/langsmith

**Best for**
- tracing and evaluation of LLM/agent applications,
- teams already using LangChain/LangGraph or wanting an integrated agent-debugging workflow,
- datasets, experiments, and production trace analysis.

**Avoid when**
- the team requires a fully open/self-hosted observability stack,
- the product only needs basic application telemetry and would duplicate existing tooling.

**Pricing model:** plan + usage based.

### Arize Phoenix

Official: https://phoenix.arize.com/

**Best for**
- open-source-oriented LLM observability and evaluation,
- tracing, retrieval analysis, experiments, and self-hosting needs,
- teams that want standards-friendly telemetry.

**Avoid when**
- a managed turnkey workflow is more valuable than operating observability infrastructure,
- the organization already has an equivalent eval stack.

**Pricing model:** open-source core; managed/commercial options may vary.

### Observability rule

Do not ship an autonomous paid workflow without being able to answer:

- what the agent attempted,
- what tools/data it used,
- what it cost,
- where it failed,
- whether the customer outcome succeeded,
- whether a human intervened,
- which model/prompt/tool version produced the result.

Token dashboards alone are not agent observability.

---

## 5. Payments and billing

### Stripe

Official: https://stripe.com/

**Best for**
- card and bank-payment acceptance,
- subscriptions and usage-linked commercial flows,
- teams that need a mature payments ecosystem and broad integration surface.

**Avoid when**
- the target geography/payment rail is not well supported,
- the business requires a specialized marketplace, treasury, or regulated-money-movement structure that needs separate legal/product evaluation.

**Pricing model:** transaction and product-specific fees.

### Payment rule

Keep usage evidence, pricing version, entitlement state, invoice/charge state, and settlement records independently auditable. A successful payment does not prove a successful agent outcome, and a successful outcome does not itself prove that the correct amount was charged.

---

## 6. CRM and pipeline

### HubSpot

Official: https://www.hubspot.com/

**Best for**
- teams that want CRM, pipeline, marketing, and support-adjacent capabilities in one ecosystem,
- founders expecting a sales process to grow beyond a spreadsheet.

**Avoid when**
- the company has fewer than ~100 active prospects and a spreadsheet is still faster,
- automation complexity creates more admin work than sales leverage.

**Pricing model:** free/paid tiers with seat/product-based commercial plans.

### CRM rule

Before adding a CRM, prove that the sales process itself works. The first useful pipeline may be five columns: prospect, pain, next step, expected value, next-action date.

---

## 7. Customer support

### Intercom

Official: https://www.intercom.com/

**Best for**
- products needing integrated support inbox, help center, customer messaging, and automation,
- teams with enough support volume to justify a dedicated platform.

**Avoid when**
- a shared inbox and simple SLA can handle current demand,
- the support stack would obscure rather than expose product failures.

**Pricing model:** plan/seat/usage components depending on products used.

### Support rule

Agent support should emit machine-readable status and errors for automated customers while preserving a human escalation path for high-impact failures. Track resolution quality and recurrence, not just deflection rate.

---

## 8. Data acquisition and web research

### Tavily

Official: https://tavily.com/

**Best for**
- agent-oriented web search and research workflows,
- products that need a purpose-built search API rather than building crawling/indexing infrastructure.

**Avoid when**
- authoritative first-party data is available and should be queried directly,
- licensing, freshness, provenance, or geographic coverage does not meet the use case.

**Pricing model:** usage/tier based.

### Firecrawl

Official: https://www.firecrawl.dev/

**Best for**
- extracting web content into model-friendly formats,
- agent workflows that need structured crawling/scraping from permitted sources.

**Avoid when**
- source terms, robots controls, law, or customer policy prohibit the collection pattern,
- a source provides a stable official API that is more reliable and contractually clear.

**Pricing model:** tier/usage based.

### Data rule

For every data source record provenance, collection time, license/permission basis, freshness expectations, and deletion/revocation behavior. “Publicly reachable” is not the same as “unrestricted for commercial reuse.”

---

## 9. Analytics

### PostHog

Official: https://posthog.com/

**Best for**
- product analytics, funnels, feature flags, experiments, session analysis, and event data,
- startups that want a broad product-engineering analytics surface.

**Avoid when**
- the product only needs a small number of business metrics that can be computed directly,
- sensitive-data handling requirements are not configured and validated.

**Pricing model:** usage based with product-specific tiers.

### Analytics rule

Instrument the business loop before vanity events. Minimum useful metrics:

- qualified leads,
- paid pilots/customers,
- time to first value,
- verified successful outcomes,
- retention,
- gross/contribution margin,
- human-review rate,
- cost per successful outcome.

---

## 10. Source control and delivery

### GitHub

Official: https://github.com/

**Best for**
- source control, issues, pull requests, actions, releases, and broad ecosystem integrations,
- teams that want code changes tied to reviewable operational evidence.

**Avoid when**
- customer/regulatory requirements mandate a different hosting model,
- autonomous write access is granted without branch protection, scoped credentials, or rollback controls.

**Pricing model:** free/seat/usage components depending on products used.

### Delivery rule

Agents that can change production should operate through reviewable branches, bounded permissions, test/eval gates, and reversible deployments. Never grant a coding agent broader repository or cloud authority than the task requires.

---

## 11. Legal and compliance support

There is no universal “AI legal tool” recommendation because the correct choice depends on jurisdiction, customer type, data, claims, regulated activities, and contracting model.

For early-stage founders, choose counsel or a compliance service based on:

- relevant jurisdiction and sector experience,
- ability to review the actual agent workflow and data flow,
- privacy/security contract experience,
- comfort with AI-specific disclosure, IP, automated-decision, and delegated-action issues,
- clear scope and fee structure,
- willingness to identify which controls are legally required versus merely conservative preferences.

**Avoid** buying a generic policy template and assuming it makes the underlying workflow compliant.

See [Agent Legal, Liability, Compliance & Contracting](docs/AGENT_LEGAL_COMPLIANCE.md) for operating guidance.

---

## Buying checklist for agent founders

Before signing or deeply integrating a vendor, record:

- [ ] exact workload and owner
- [ ] required regions/data residency
- [ ] data categories sent to the vendor
- [ ] retention/training settings
- [ ] authentication and permission model
- [ ] availability target and documented failure behavior
- [ ] export/migration path
- [ ] pricing unit and expected monthly range
- [ ] hard spending cap or alert
- [ ] rate limits and concurrency behavior
- [ ] support/escalation path
- [ ] subprocessor/dependency implications where relevant
- [ ] fallback or graceful-degradation plan for critical dependencies
- [ ] benchmark on representative paid-workflow examples
- [ ] contract renewal/termination date

For critical suppliers, rerun this review after material API, model, pricing, data-policy, or ownership changes.

## When to add a second vendor

Redundancy is valuable only when it is tested and economically justified. Add a second provider when at least one is true:

- the primary vendor is a material share of customer-visible failures,
- a customer contract requires redundancy,
- concentration risk exceeds your stated limit,
- workload routing produces measurable margin gains,
- one provider serves a distinct capability materially better,
- procurement or regional constraints require alternatives.

Do not add a fallback that has never passed the same compatibility and outcome evals as the primary path.

## Commercial disclosure policy

Trust is more valuable than short-term affiliate revenue. Every listed vendor must have a disclosure status.

Allowed statuses:

- **No commercial relationship** — no compensation tied to inclusion.
- **Affiliate** — the project may receive a commission when a reader buys through a tracked link.
- **Sponsor** — the vendor paid for a clearly labeled placement or campaign.
- **Customer/partner relationship** — a maintainer has another material commercial relationship with the vendor.

Current directory status: **all entries are editorial references with no commercial relationship recorded in this file.** If that changes, update the relevant entry and this statement in the same pull request that introduces the commercial link.

### Affiliate policy

Affiliate relationships may not:

- determine whether a vendor qualifies for inclusion,
- change factual comparison criteria,
- suppress “avoid when” guidance,
- receive hidden ranking boosts,
- be disguised as neutral editorial links.

Where an affiliate link exists, label it next to the link and preserve a non-affiliate canonical vendor URL where practical.

### Sponsorship policy

Sponsorship is permitted only when:

1. the underlying directory remains useful without the sponsor,
2. paid placement is visibly labeled **Sponsored**,
3. sponsors do not control editorial rankings or negative caveats,
4. the commercial term is separate from inclusion in the core shortlist,
5. sponsored slots are capped so they cannot dominate a category,
6. renewal is evaluated on reader usefulness and qualified outcomes, not clicks alone.

A sponsor may buy attention. It may not buy the conclusion.

## Contribution standard

A proposed tool addition should include:

- category and founder job-to-be-done,
- official canonical link,
- concrete “best for” cases,
- concrete “avoid when” cases,
- pricing model at the level that can remain reasonably stable,
- commercial relationship disclosure,
- evidence for any performance, security, compliance, or market-share claim.

Do not add vendors solely because they are popular, newly launched, or willing to sponsor the project.

## Directory maintenance cadence

Review entries when:

- pricing units materially change,
- a product is deprecated or acquired,
- terms materially change data use or retention,
- a major security or reliability event changes the risk profile,
- a new open standard materially improves portability,
- multiple founders report the same integration failure or migration reason.

The purpose of this directory is not to stay large. It is to stay useful.
