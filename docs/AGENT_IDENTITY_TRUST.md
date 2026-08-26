# Agent Identity, Authority & Reputation

A practical, vendor-neutral trust layer for autonomous agents that need to act, spend, buy, sell, delegate, and explain what happened afterward.

Agent commerce breaks when a counterparty cannot answer four questions:

1. **Who is this agent?**
2. **Who does it represent?**
3. **What is it allowed to do right now?**
4. **Why should I trust it enough to transact?**

This guide turns those questions into product requirements, operating controls, and business opportunities.

> **Core rule:** identity is not authority, and authority is not reputation. Treat them as separate layers.

## The trust stack

| Layer | Question | Typical evidence |
|---|---|---|
| Identity | Who are you? | account, key, domain, certificate, signed identifier |
| Authentication | Can you prove it? | challenge-response, OAuth/OIDC, mTLS, signed request |
| Authorization | What may you do? | scopes, capabilities, policy, budget, role |
| Delegation | Who gave you that authority? | signed grant, token chain, principal record |
| Reputation | Should I trust you? | history, outcomes, disputes, attestations, ratings |
| Auditability | Can we reconstruct the action? | immutable logs, receipts, approvals, policy decisions |
| Revocation | Can authority be stopped? | token expiry, denylist, key rotation, grant revocation |

Do not collapse these into one `trusted=true` flag.

## Principal-agent model

Every autonomous action should map back to a principal.

```text
Principal -> delegates -> Agent -> invokes -> Tool / Service / Counterparty
    |                        |
    +---- policy ----------->+
```

A principal may be:

- a human,
- a company,
- a team,
- another service,
- or another agent with delegated authority.

For sensitive actions, record the delegation chain rather than only the final agent identity.

### Minimum delegation record

```json
{
  "principal_id": "org_acme",
  "agent_id": "agent_procurement_01",
  "grant_id": "grant_2026_08_26_001",
  "issued_at": "2026-08-26T20:00:00Z",
  "expires_at": "2026-08-27T20:00:00Z",
  "scopes": ["vendor.search", "quote.request", "purchase.create"],
  "constraints": {
    "max_transaction_usd": 500,
    "max_daily_usd": 1500,
    "allowed_categories": ["cloud", "software"],
    "blocked_merchants": []
  },
  "approval_required_above_usd": 250
}
```

The exact format can vary. The invariant is what matters: **authority must be explicit, bounded, attributable, and revocable.**

## Least privilege for agents

Agents should receive the narrowest authority needed for the current task.

Bad:

```text
Agent can access billing, CRM, email, payroll, production, and all payment methods indefinitely.
```

Better:

```text
Agent can create software purchases under $250 from approved vendors for the next 4 hours.
```

Useful scope dimensions:

- action type,
- resource,
- merchant or counterparty,
- geography,
- time window,
- transaction amount,
- cumulative budget,
- data classification,
- tool,
- environment,
- customer/account,
- and required human approval level.

## Approval thresholds

A good autonomous system has explicit escalation rules.

| Risk level | Example | Default control |
|---|---|---|
| Low | read public data | autonomous |
| Medium | create draft, request quote | autonomous + audit |
| Elevated | send external message, modify CRM | autonomous within policy |
| High | spend money, sign contract, delete production data | threshold + approval |
| Critical | irreversible or regulated action | explicit human authorization |

Thresholds should consider more than dollars. A $0 action can still be high risk if it exposes secrets or binds a company contractually.

## Example purchasing policy

```yaml
policy: procurement-agent-v1
principal: acme-inc
allowed_actions:
  - discover_vendor
  - request_quote
  - create_purchase
limits:
  max_single_purchase_usd: 300
  max_daily_spend_usd: 1000
  max_monthly_spend_usd: 5000
allow:
  categories:
    - developer-tools
    - cloud-services
  countries:
    - US
    - CA
require_approval:
  purchase_over_usd: 250
  new_vendor: true
  annual_commitment: true
deny:
  - cryptocurrency_transfer
  - payroll_change
  - production_secret_export
```

The model may recommend an action, but a deterministic policy layer should decide whether the action is permitted.

## Keep secrets out of model context

Do not hand long-lived credentials directly to the reasoning model when a broker, scoped token, or isolated execution layer can hold them instead.

Prefer:

```text
Agent -> asks for permitted operation -> policy/broker -> credentialed action -> result
```

over:

```text
Agent context contains reusable API key -> arbitrary tool invocation
```

Useful controls:

- short-lived credentials,
- token exchange,
- scoped OAuth grants,
- secret brokers,
- workload identity,
- isolated execution environments,
- just-in-time authorization,
- and automatic credential rotation.

## Agent identity design

An agent identity should be stable enough to build history but separable from a human login.

Recommended fields:

```json
{
  "agent_id": "agent:acme:procurement:01",
  "principal": "org:acme",
  "operator": "team:finance-automation",
  "version": "2026-08-26.3",
  "public_key_id": "key_7f2...",
  "capabilities": ["vendor_search", "quote_compare", "purchase"],
  "endpoint": "https://agents.example.com/procurement",
  "created_at": "2026-06-01T00:00:00Z"
}
```

Avoid using a model name as the identity. Models are replaceable components; the accountable business agent should retain a stable identity across model upgrades.

## Discovery is not trust

Protocols and registries can help agents discover each other, but a discoverable endpoint is not automatically trustworthy.

A discovery card may tell you:

- service identity,
- endpoint,
- capabilities,
- supported authentication methods,
- and interaction metadata.

Trust still requires independent evaluation of authority, reputation, policy, and risk.

## Reputation architecture

Reputation should summarize evidence, not replace it.

Good reputation inputs include:

- successful transaction count,
- transaction value,
- completion rate,
- dispute rate,
- refund rate,
- response latency,
- SLA adherence,
- verified principal or business status,
- age of identity,
- security incidents,
- signed attestations,
- buyer concentration,
- recency of activity,
- and category-specific outcomes.

### Example reputation record

```json
{
  "subject": "agent:vendor:research:042",
  "window_days": 90,
  "transactions": 481,
  "completion_rate": 0.982,
  "dispute_rate": 0.006,
  "median_latency_seconds": 42,
  "verified_principal": true,
  "security_incidents": 0,
  "last_updated": "2026-08-26T21:00:00Z"
}
```

Do not expose a single opaque score without underlying evidence.

## Sybil and manipulation resistance

Agent ecosystems make it cheap to create identities, so naive rating systems are easy to game.

Common attacks:

- thousands of fresh identities rating each other,
- fake transactions designed only to create history,
- wash trading,
- self-attestations,
- coordinated review rings,
- reputation transfer after key compromise,
- and identity resets after bad behavior.

Countermeasures:

- weight reputation by verified economic activity,
- distinguish verified and unverified principals,
- cap influence from correlated counterparties,
- detect circular transaction graphs,
- decay stale evidence,
- keep historical links after key rotation,
- require stronger verification for higher limits,
- and expose confidence alongside scores.

## Counterparty risk checklist

Before allowing autonomous transactions with a new service or agent, evaluate:

- [ ] Is the endpoint bound to a stable identity?
- [ ] Can the counterparty prove control of that identity?
- [ ] Is the represented principal known?
- [ ] Is the requested permission narrower than the task requires?
- [ ] Is there a clear price and maximum spend?
- [ ] Are refund and dispute rules available?
- [ ] Is there verifiable transaction history?
- [ ] Are there recent security or abuse signals?
- [ ] Is the requested data appropriate for this counterparty?
- [ ] Can access be revoked immediately?
- [ ] Will the action produce a receipt and audit record?
- [ ] Does the transaction exceed an approval threshold?

## Signed attestations and verifiable claims

Attestations can be useful when one party needs to make a claim another party can verify without calling the issuer for every transaction.

Examples:

- "this agent is operated by Acme, Inc.",
- "this agent passed security review on August 20, 2026",
- "this agent is allowed to spend up to $500/day",
- "this service completed 1,000 verified jobs",
- or "this agent may act on behalf of principal X until time Y".

Use signed claims when they materially reduce trust friction. Do not add cryptography to low-risk workflows merely because it sounds advanced.

## Revocation

Every authorization mechanism needs a way to stop working.

Design for:

- expiration by default,
- manual revocation,
- automated revocation after anomaly detection,
- key compromise,
- principal termination,
- agent retirement,
- policy changes,
- budget exhaustion,
- and contract termination.

A credential without practical revocation is a liability.

## Audit receipts

Every consequential action should produce a machine-readable receipt.

Recommended fields:

```json
{
  "receipt_id": "rcpt_9a2...",
  "timestamp": "2026-08-26T21:15:00Z",
  "principal_id": "org_acme",
  "agent_id": "agent_procurement_01",
  "grant_id": "grant_2026_08_26_001",
  "action": "purchase.create",
  "counterparty": "vendor_xyz",
  "amount_usd": 129,
  "policy_version": "procurement-v12",
  "decision": "allowed",
  "approval_id": null,
  "input_hash": "sha256:...",
  "output_reference": "order_18373"
}
```

For higher-risk systems, consider signing receipts or storing hashes in append-only infrastructure.

## Explainability for authority decisions

When an action is blocked, the system should be able to say why without leaking sensitive policy details.

Useful denial reasons:

```text
Denied: transaction exceeds autonomous spending limit.
Denied: merchant category is outside delegated scope.
Denied: grant expired.
Denied: new vendor requires human approval.
Denied: requested data classification exceeds counterparty trust level.
```

Avoid opaque failures such as `authorization error` when a precise policy reason is available.

## Trust tiers

A practical ecosystem can use escalating trust tiers.

| Tier | Evidence | Suitable actions |
|---|---|---|
| 0 — Unknown | endpoint only | public/read-only |
| 1 — Authenticated | proves key/account control | low-risk interactions |
| 2 — Verified | principal or business verified | routine transactions |
| 3 — Established | verified history + low disputes | higher autonomous limits |
| 4 — Strategic | contract, SLA, security review | sensitive or high-value workflows |

Trust should affect limits, not merely access/no-access.

## Building an agent reputation product

Identity and reputation can themselves be businesses.

Potential products:

### 1. Agent identity registry

Provide stable identifiers, principal verification, key rotation, and discovery metadata.

Revenue:

- per verified identity,
- enterprise subscription,
- API access,
- compliance tier.

### 2. Authorization broker

Keep secrets and tokens out of agent context while resolving policy-controlled actions.

Revenue:

- per active agent,
- per authorization decision,
- enterprise platform fee,
- premium audit retention.

### 3. Agent reputation API

Aggregate transaction history, disputes, attestations, and risk signals into machine-readable evidence.

Revenue:

- per lookup,
- subscription by lookup volume,
- premium monitoring,
- fraud/risk product.

### 4. Delegation and policy engine

Let businesses define exactly what each agent may do, spend, access, and delegate.

Revenue:

- per agent,
- per policy decision,
- enterprise license,
- governance/compliance package.

### 5. Trust attestation network

Allow auditors, security vendors, platforms, insurers, or marketplaces to publish signed claims about agents and services.

Revenue:

- verification fees,
- issuer tooling,
- enterprise API,
- monitoring subscriptions.

## What buyers will pay for

"Agent identity" alone is abstract. Sell an economic outcome:

- reduce fraud,
- increase autonomous transaction limits,
- shorten vendor onboarding,
- pass enterprise security review,
- reduce manual approvals,
- create defensible audit trails,
- or prevent credential exposure.

The winning trust companies will monetize **permission to automate more valuable actions safely**.

## Standards landscape

As of August 2026, the space is still evolving. Build with abstraction boundaries rather than assuming one protocol will own identity or authorization.

Relevant concepts and standards include:

- **OAuth/OIDC** for authentication and delegated access patterns,
- **MCP** for agent-to-tool connectivity and authorization integrations,
- **A2A** for interoperable agent-to-agent communication and discovery,
- **W3C Verifiable Credentials / DIDs** where portable signed claims are useful,
- workload identity and mTLS patterns from cloud/service infrastructure,
- and emerging agent-specific identity and authorization drafts.

NIST's 2026 work on software and AI agent identity explicitly highlights identity, authorization, provenance, least privilege, and existing standards such as OAuth/OIDC and MCP. A2A likewise separates authentication from implementation-specific authorization and recommends least privilege.

Treat emerging agent-specific specifications as experiments until adoption, governance, interoperability, and conformance are clear.

## Founder implementation checklist

Before an agent can take consequential autonomous action:

- [ ] Give the agent a stable identity separate from its underlying model.
- [ ] Record the principal it represents.
- [ ] Define explicit scopes and constraints.
- [ ] Add transaction and cumulative budgets where money is involved.
- [ ] Keep reusable secrets outside model context where practical.
- [ ] Enforce authorization in deterministic infrastructure.
- [ ] Add approval thresholds for high-risk actions.
- [ ] Make grants expire.
- [ ] Provide immediate revocation.
- [ ] Log every consequential decision.
- [ ] Generate receipts linking action, agent, principal, policy, and outcome.
- [ ] Evaluate counterparty identity and reputation before autonomous transactions.
- [ ] Add anomaly detection for abnormal spending or behavior.
- [ ] Test key compromise and revocation paths.
- [ ] Revisit limits as reputation accumulates.

## 30-day build sequence

### Week 1 — Identity and logs

Create stable agent IDs, principal mapping, structured audit events, and versioned policy records.

### Week 2 — Scoped authority

Add bounded grants, expiry, budgets, approval thresholds, and secret isolation.

### Week 3 — Counterparty trust

Add verified metadata, reputation inputs, deny/allow policy, and new-counterparty review.

### Week 4 — Revocation and adversarial testing

Test expired grants, revoked keys, compromised agents, spoofed counterparties, budget bypass attempts, and replayed actions.

## References

Use these as current starting points, not declarations that the standards race is settled:

- NIST NCCoE — *Accelerating the Adoption of Software and AI Agent Identity and Authorization* (2026): https://www.nccoe.nist.gov/projects/software-and-ai-agent-identity-and-authorization
- Agent2Agent Protocol: https://a2a-protocol.org/
- Model Context Protocol: https://modelcontextprotocol.io/
- OAuth: https://oauth.net/
- OpenID Connect: https://openid.net/developers/how-connect-works/
- W3C Verifiable Credentials: https://www.w3.org/TR/vc-data-model-2.0/

---

**Design target:** an autonomous agent should be able to prove who it represents, operate only inside explicit authority, evaluate counterparties proportionally to risk, and produce enough evidence for a human or another agent to reconstruct every consequential decision.