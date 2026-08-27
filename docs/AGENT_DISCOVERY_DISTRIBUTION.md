# Agent Discovery, Registries & Distribution

Agent supply is growing faster than any one directory, marketplace, or protocol can organize it. For an agent business, **being callable is not enough**. Buyers—human or autonomous—must be able to discover what you do, understand when to use you, evaluate whether you are trustworthy, estimate the cost and latency, invoke you successfully, and decide to return.

This guide treats discovery as a full business funnel rather than a publishing checkbox.

## The discovery funnel

```text
Published -> Indexed -> Matched -> Evaluated -> Invoked -> Paid -> Reused
```

A founder should instrument every stage. A capability that is listed but never selected has a positioning problem. A capability that is selected but rarely completes has a product or reliability problem. A capability that completes but is not repurchased has a value, price, or retention problem.

## 1. Design for two audiences

Most agent businesses need to be legible to both humans and machines.

### Human-facing distribution

Humans still choose vendors, approve budgets, install integrations, and override agents. Maintain:

- a clear landing page,
- examples tied to business outcomes,
- transparent pricing or pricing logic,
- security and data-handling information,
- proof such as case studies or eval results,
- documentation with a fast first success,
- and a way to contact a human when trust is high-stakes.

### Agent-native distribution

Autonomous buyers need structured data instead of persuasive prose. Publish machine-readable metadata that answers:

- **What can this agent/tool do?**
- **What inputs are required?**
- **What outputs are returned?**
- **What constraints and side effects exist?**
- **How is it authenticated?**
- **What does it cost?**
- **How long does it usually take?**
- **What reliability or SLA should be expected?**
- **What evidence supports the claims?**
- **Who is the publisher?**
- **How should versions and deprecations be handled?**

Do not assume a single protocol or registry will own agent discovery. Keep one canonical capability model internally, then translate it into the formats required by each channel.

## 2. Create a canonical capability record

Maintain one source-of-truth record for every sellable capability.

Example:

```yaml
id: reconcile-invoices
name: Reconcile invoices against purchase orders
version: 1.3.0
publisher: acme-agent
category: finance-operations
summary: Match invoices to purchase orders and flag exceptions.
inputs:
  - invoice_pdf
  - purchase_order_records
outputs:
  - reconciliation_report
  - exception_list
side_effects: none
human_approval_required: false
expected_latency_seconds: 45
pricing:
  model: per_invoice
  currency: USD
  amount: 0.35
reliability:
  target_success_rate: 0.995
  target_p95_latency_seconds: 90
security:
  data_retention: 0d
  auth: oauth2
provenance:
  publisher_url: https://example.com
  docs_url: https://example.com/docs/reconcile
```

The exact schema can vary. The discipline should not.

### Capability naming

Good names describe the job, not the implementation.

Prefer:

- `reconcile-invoices`
- `qualify-inbound-leads`
- `extract-renewal-terms`
- `schedule-field-technician`

Avoid vague names such as:

- `smart-agent`
- `ai-assistant`
- `business-helper`
- `super-agent`

Machine search improves when the capability name, description, input schema, and examples all describe the same narrow job.

## 3. Write descriptions for retrieval, not hype

A capability description should contain:

1. the job performed,
2. the customer or workflow context,
3. the main inputs,
4. the output,
5. important constraints,
6. and one or two concrete examples.

Example:

> Matches vendor invoices against purchase orders for finance teams, returns a reconciliation report and exception list, and does not approve payment or modify accounting records.

That is more useful to an agent than:

> Revolutionary AI-powered finance automation that transforms your back office.

Avoid keyword stuffing. Search systems increasingly combine structured fields, semantic similarity, behavior, and trust signals. Repetition that harms clarity can reduce selection even if it increases impressions.

## 4. Publish portable capability metadata

### A2A-style Agent Cards

Agent-to-Agent ecosystems commonly use an Agent Card or similar descriptor to advertise identity, endpoint information, supported skills, authentication, and capabilities.

Use these records to expose:

- canonical agent identity,
- supported skills,
- examples,
- endpoint and transport information,
- authentication requirements,
- supported content types,
- version,
- and operational metadata.

Do not confuse discovery metadata with authorization. A public card can describe a powerful capability while the actual service still enforces scoped credentials, approval thresholds, and policy checks.

### MCP registries

For MCP servers, registry listings help users and agents discover deterministic tools. Registry quality improves when:

- server names are stable,
- tool names map to real jobs,
- argument schemas are precise,
- descriptions explain side effects,
- versions are published correctly,
- documentation is reachable,
- and package or remote-server information is current.

The official MCP Registry provides a public discovery surface, but founders should treat it as one channel—not the entire market.

### Enterprise and private registries

Large organizations increasingly maintain private catalogs of agents, MCP servers, endpoints, and skills. Winning distribution inside an enterprise may therefore mean passing governance checks before winning user attention.

Be ready to provide:

- publisher identity,
- owner/team,
- data classifications,
- authentication method,
- approved scopes,
- compliance evidence,
- support contact,
- version history,
- risk tier,
- and deprecation policy.

Enterprise distribution is partly a search problem and partly a governance problem.

## 5. Make the offer easy for an autonomous buyer to evaluate

A human may tolerate missing information and ask sales. An autonomous buyer often cannot.

Expose enough metadata to compare alternatives without guessing.

### Recommended evaluation fields

| Field | Why it matters |
|---|---|
| capability | Determines task fit |
| inputs / outputs | Determines interoperability |
| price | Enables budget decisions |
| expected latency | Enables workflow planning |
| success rate | Supports reliability decisions |
| side effects | Supports risk policy |
| permissions required | Supports authorization |
| data handling | Supports privacy policy |
| publisher identity | Supports trust |
| version | Supports reproducibility |
| support / escalation | Supports recovery |
| evidence | Supports ranking and confidence |

If some fields are unknown, say so explicitly instead of inventing precision.

## 6. Build a machine-readable offer

A capability record explains **what exists**. An offer explains **what can be purchased now**.

Example:

```json
{
  "capability": "reconcile-invoices",
  "version": "1.3.0",
  "price": {"amount": 0.35, "currency": "USD", "unit": "invoice"},
  "max_batch": 1000,
  "p95_latency_seconds": 90,
  "refund_policy": "automatic-credit-on-failed-job",
  "requires": ["invoice_pdf", "purchase_order_records"],
  "returns": ["reconciliation_report", "exception_list"]
}
```

Keep the commercial contract separate from marketing language. Autonomous buyers should be able to reason about cost and expected result before invoking.

## 7. Treat distribution as a portfolio

Do not rely on one marketplace or registry.

A resilient portfolio may include:

- your own website and documentation,
- GitHub,
- MCP registries,
- A2A-compatible directories,
- cloud-provider agent registries,
- enterprise private catalogs,
- vertical marketplaces,
- API directories,
- partner integrations,
- developer communities,
- customer referrals,
- and human-led outbound.

Each channel serves a different discovery mode: branded search, semantic search, workflow integration, governed enterprise selection, or direct sales.

## 8. Optimize for selection, not impressions

Agent discovery has an SEO-like layer, but the goal is not traffic. The goal is profitable selection.

Track:

```text
registry impressions
  -> detail views / metadata fetches
  -> shortlist or selection events
  -> auth attempts
  -> successful invocations
  -> completed outcomes
  -> paid transactions
  -> repeat invocations
```

### Core metrics

| Metric | Formula | Signal |
|---|---|---|
| match rate | matched searches / indexed searches | discoverability |
| selection rate | selections / matches | positioning + trust |
| invocation success | successful calls / attempted calls | integration quality |
| paid conversion | paid calls / successful calls | monetization |
| repeat rate | returning buyers / buyers | retention |
| revenue per discovered buyer | revenue / unique matched buyers | channel quality |
| acquisition cost per buyer | channel spend / new buyers | economics |

A channel with fewer impressions can be far more valuable if its buyers have higher authority, budgets, and repeat rates.

## 9. Improve discoverability with evidence

Descriptions help agents understand claims. Evidence helps them trust those claims.

Useful evidence includes:

- public eval results,
- completion-rate history,
- latency history,
- signed publisher metadata,
- verified customer outcomes,
- security attestations,
- refund behavior,
- uptime history,
- version changelogs,
- and reputation from repeat counterparties.

Never fabricate ratings, reviews, usage counts, or benchmark results. Reputation is more valuable when it is difficult to fake.

## 10. Version capabilities like products

A registry listing is an API promise.

### Safe versioning rules

- Use stable identifiers for stable capabilities.
- Increment versions when schemas or behavior change materially.
- Keep old versions available long enough for buyers to migrate when practical.
- Publish migration guidance for breaking changes.
- Mark deprecated capabilities explicitly.
- Include a sunset date when one exists.
- Never silently repurpose an existing capability name for a different job.

### Deprecation metadata

```yaml
status: deprecated
replacement: reconcile-invoices-v2
sunset_date: 2026-12-01
migration_docs: https://example.com/migrate/v2
```

Autonomous systems need explicit lifecycle data because they may continue selecting capabilities long after a human has stopped reading release notes.

## 11. Design for registry portability

Registries will change. Keep your distribution layer portable.

Store internally:

- canonical capability IDs,
- descriptions,
- schemas,
- auth requirements,
- pricing,
- trust metadata,
- version history,
- endpoints,
- and channel-specific publishing state.

Then create adapters that transform this model into each registry’s required format.

This prevents a cloud provider, marketplace, or protocol from becoming the source of truth for your business identity.

## 12. Build a registry publication checklist

Before publishing a capability:

- [ ] The capability solves one clear job.
- [ ] Name and description use the customer’s language.
- [ ] Inputs and outputs have strict schemas.
- [ ] Side effects are explicit.
- [ ] Authentication requirements are documented.
- [ ] Authorization is enforced server-side.
- [ ] Price or pricing logic is machine-readable where possible.
- [ ] Latency and reliability claims are evidence-backed.
- [ ] Publisher identity is verifiable.
- [ ] Data-retention and privacy behavior are documented.
- [ ] Version is explicit.
- [ ] Documentation contains a working example.
- [ ] Error states are actionable.
- [ ] A support/escalation path exists.
- [ ] Discovery and conversion events are instrumented.

## 13. Launch an agent-discoverable product

### Day 1: define the capability

Write the narrow job, input/output contract, side effects, buyer, price, and proof.

### Day 2: publish machine-readable metadata

Create the canonical capability record, an Agent Card or equivalent where applicable, and precise tool or API descriptions.

### Day 3: publish to two channels

Pick one public channel and one channel close to your buyer. For example:

- public MCP registry + vertical developer community,
- cloud agent registry + enterprise design partner,
- GitHub + direct outbound,
- marketplace + partner integration.

### Day 4: test discovery

Have a fresh human or agent attempt to find the capability using realistic job language. Record whether it appears, how it is interpreted, and why it is or is not selected.

### Day 5: test invocation

Run the complete path from discovery to authentication to successful outcome. Capture failures as funnel events rather than anecdotes.

### Day 6: test commercial selection

Give the buyer alternatives. Does your metadata make price, trust, latency, and outcome easy to compare?

### Day 7: improve the weakest funnel stage

Do not add more channels until the existing path produces useful signal.

## 14. Agent-native distribution experiments

Useful experiments include:

- two capability descriptions with the same underlying service,
- one broad tool versus several narrow tools,
- price shown before invocation versus quote-on-request,
- richer examples versus shorter descriptions,
- verified identity metadata versus anonymous publishing,
- public benchmark evidence versus claims only,
- low-cost trial capability that leads to a higher-value workflow,
- bundling complementary tools under one publisher reputation layer.

Change one variable at a time when possible.

## 15. Business opportunities around discovery

The discovery layer itself creates businesses.

### Registry infrastructure

Build searchable catalogs for public, private, or vertical agent ecosystems. Revenue can come from SaaS fees, enterprise licenses, or managed registry operations.

### Verification and trust

Verify publisher identity, security posture, performance claims, or business credentials. Charge per verification, subscription, or enterprise policy bundle.

### Agent distribution analytics

Measure which searches produce selections, paid calls, and retained buyers across multiple registries. This can become analytics SaaS for agent publishers.

### Capability optimization

Help publishers improve schemas, descriptions, examples, latency, pricing, and trust metadata based on selection data. This can resemble conversion-rate optimization for agent marketplaces.

### Brokerage and routing

Match buyer intent to qualified agents and earn a transaction fee, referral fee, or spread—provided ranking incentives are transparent.

### Enterprise discovery gateways

Provide a governed layer that searches internal and external catalogs, filters by policy, verifies trust requirements, and routes the request to an approved provider.

## 16. Anti-patterns

Avoid:

- publishing one vague “do everything” agent,
- keyword stuffing capability descriptions,
- fake usage counts or testimonials,
- hiding important side effects,
- making reliability claims without measurements,
- coupling your canonical metadata to one registry,
- treating public discovery as authorization,
- silently breaking existing schemas,
- publishing dozens of nearly identical capabilities to dominate search results,
- and optimizing for impressions while ignoring paid repeat usage.

## 17. The durable principle

**Distribution for agents is becoming structured, measurable, and machine-consumable.**

The strongest agent businesses will not merely expose endpoints. They will make capabilities easy to find, easy to compare, safe to invoke, simple to pay for, and worth choosing again.

Treat every registry entry as a storefront, every schema as a sales interface, every successful invocation as a conversion event, and every repeat call as proof that the business—not just the agent—works.
