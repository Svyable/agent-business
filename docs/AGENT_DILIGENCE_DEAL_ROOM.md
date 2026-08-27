# Agent-Native Diligence, Deal Rooms, and Transaction Readiness

Autonomous businesses should not rebuild trust from scratch every time a customer, investor, insurer, marketplace, acquirer, or counterparty asks for evidence. The goal of an agent-native deal room is to maintain one canonical evidence graph, then expose the minimum authorized view needed for a specific transaction.

This is not a static folder of PDFs. It is a living system of claims, source artifacts, freshness dates, integrity metadata, access rules, material risks, and readiness state.

## 1. Operating model

Use this loop:

`Claim -> Evidence -> Freshness -> Scope -> Verify -> Share -> Revoke/Refresh`

A diligence response is only as strong as the evidence behind it. Treat generated prose as a presentation layer, never as the source of truth.

### Core rules

1. Every material external claim links to dated evidence.
2. Evidence has an owner, freshness rule, sensitivity level, and integrity proof.
3. Share only evidence authorized for the requesting audience.
4. Redact before disclosure; never rely on the recipient to ignore unnecessary sensitive data.
5. Stale, disputed, or contradictory claims block readiness instead of being silently summarized away.
6. Keep material risks visible. A credible deal room explains uncertainty rather than hiding it.
7. Record what was shared, with whom, when, and under what scope.
8. Reuse one canonical evidence graph across transaction types instead of maintaining inconsistent copies.

## 2. Canonical diligence domains

A serious agent business should be able to assemble evidence across these domains.

### Company and ownership

- legal entity, jurisdiction, status, and registered address
- cap table or ownership summary where relevant
- beneficial ownership and control
- material subsidiaries or related entities
- board or approval authority for material transactions
- key dependencies on founders, operators, or external principals

### Financial

- revenue model and pricing
- revenue by product or capability
- customer concentration
- gross and contribution margin
- cash runway and major commitments
- receivables/payables aging
- reconciliation controls
- material refunds, credits, disputes, or chargebacks
- financial assumptions with source dates

Never present estimated ARR, margin, or runway as booked fact. Label estimates and link them to the calculation inputs.

### Customers and commercial

- ICP and customer mix
- active contract count
- concentration by customer or segment
- retention/churn definitions and measurements
- representative contracts, order forms, or machine-readable service terms
- SLA commitments and actual performance
- major customer disputes or unresolved credits
- referenceability and permission to disclose logos or names

### Technical

- system architecture
- model, tool, MCP, API, and infrastructure dependencies
- data flows and trust boundaries
- production vs test separation
- runtime reliability controls
- failover and degraded modes
- capability/version compatibility policy
- deployment, rollback, and incident controls

### Security

- agent inventory and identity model
- tool permission boundaries
- approval thresholds for high-impact actions
- secrets management
- tenant isolation
- prompt-injection and tool-abuse controls
- vulnerability and dependency management
- security eval coverage
- incident response process and material incidents
- audit logs and provenance

### Legal and compliance

- applicable regulatory posture
- privacy notices, DPA terms, and subprocessors
- data retention/deletion practices
- regulated-workflow escalation rules
- IP ownership and training/data provenance where material
- licensing obligations
- disclosure requirements for AI-generated or autonomous interactions
- unresolved claims, investigations, or disputes

### Operations

- founder/operator dependencies
- human review model and staffing constraints
- supplier concentration
- critical SLOs and recent performance
- support and escalation process
- business continuity and recovery procedures
- dependency substitution plan

### Insurance and risk transfer

- active policies and relevant exclusions
- limits, deductibles, retention, and expiry dates
- warranties or guarantees offered to customers
- reserve policy for retained losses
- claims history
- material uninsured or ambiguous agent-caused risks

### IP and provenance

- ownership of code, prompts, workflows, datasets, and generated assets where relevant
- contributor agreements
- third-party licenses
- provenance for externally sourced data
- rights to redistribute or commercialize outputs
- unresolved ownership disputes

## 3. Claims should be machine-verifiable

A claim is a statement that a counterparty may rely on. Give it a stable ID and link it to one or more evidence artifacts.

Example:

```json
{
  "id": "claim-runtime-slo",
  "category": "operations",
  "statement": "The paid extraction capability met its 99.5% monthly availability objective in July 2026.",
  "evidence_ids": ["evidence-july-slo-report"],
  "as_of": "2026-08-01",
  "expires_on": "2026-09-01",
  "owner": "operations",
  "status": "verified"
}
```

Avoid vague claims such as "enterprise grade" or "secure by design" unless the terms are defined and evidenced.

### Claim statuses

- `verified`: supported by current evidence.
- `qualified`: directionally supported but requires an explicit caveat.
- `draft`: not ready for external reliance.
- `disputed`: conflicting evidence exists; external readiness should fail until resolved.

## 4. Evidence is a governed object

Every evidence item should specify:

- stable ID
- title and category
- canonical URI or artifact path
- capture date
- expiry or review date
- sensitivity
- permitted audiences
- required redaction
- integrity proof such as a hash, signed artifact, attestation, or repository commit

Do not put secrets, credentials, raw customer data, private keys, unredacted government IDs, or unrelated personal data into a shared diligence room.

### Evidence freshness

Different artifacts decay at different speeds. Suggested starting points:

| Evidence | Review cadence |
|---|---|
| legal entity documents | on change |
| cap table / ownership | on financing or transfer |
| security architecture | quarterly and on material change |
| dependency inventory | continuous or monthly |
| penetration/eval results | quarterly or after material change |
| financial performance | monthly |
| customer concentration | monthly |
| insurance certificates | on renewal/change |
| subprocessors | on change |
| incident history | continuous |
| SLO performance | monthly |

The right cadence depends on transaction risk. A high-value enterprise deployment or insurance renewal should require fresher evidence than a low-risk marketplace listing.

## 5. Audience-scoped views

One canonical evidence graph can generate different rooms.

### Enterprise customer

Prioritize security, privacy, architecture, business continuity, SLA evidence, subprocessors, incident handling, and contractual authority. Do not expose cap table details or unrelated financials unless necessary.

### Investor

Prioritize market evidence, revenue quality, unit economics, retention, concentration, capital needs, technology defensibility, material risks, and ownership. Customer-sensitive records should be aggregated or permissioned.

### Acquirer

Expect deeper access: ownership, IP chain, contracts, liabilities, security incidents, code/dependency provenance, customer concentration, financial history, and change-of-control restrictions.

### Insurer

Prioritize exposure inventory, agent authority, controls, incident history, loss scenarios, dependency concentration, evals, logs, human review, and evidence of risk reduction.

### Marketplace or autonomous counterparty

Prefer compact machine-readable evidence: identity, authority, capability assurance, pricing terms, transaction history, dispute rate, service reliability, security posture, and proof-of-performance.

## 6. Minimum-necessary disclosure

Use progressive disclosure instead of opening the whole room by default.

A useful sequence is:

1. public trust summary
2. machine-readable evidence manifest
3. scoped shared evidence
4. confidential artifacts under appropriate agreement
5. restricted raw evidence only when necessary and authorized

Before sharing an artifact, evaluate:

- Does the requester need this artifact to answer the question?
- Can a summary or attestation answer it with less sensitive data?
- Is the audience permitted?
- Is redaction complete?
- Is the artifact current?
- Does it contain data belonging to another party?
- Is disclosure allowed by contract, law, and policy?

## 7. Contradiction detection

Agent-generated diligence fails when different documents contain incompatible truths. Detect contradictions explicitly.

Examples:

- founder packet says gross margin is 70%; finance report says 52%
- security questionnaire says no customer data is retained; product docs say logs retain prompts for 30 days
- investor deck says no single customer exceeds 15% of revenue; billing data shows 31%
- insurance application says no material incidents; incident register contains an unresolved severity-1 event
- marketplace profile claims a capability version that has been deprecated

When contradictions appear:

1. stop external publication of the affected claim
2. identify the authoritative source and its owner
3. mark the claim `disputed`
4. resolve or qualify the discrepancy
5. regenerate all derived views
6. preserve the correction history

Do not let an LLM "harmonize" inconsistent numbers by inventing a compromise value.

## 8. Transaction readiness gates

### Enterprise procurement

Ready when:

- legal entity and signatory authority are verified
- security/privacy evidence is current
- subprocessors and data flows are known
- service levels have measurable definitions
- material incidents and limitations are disclosed appropriately
- contract and approval boundaries are clear
- implementation dependencies and rollback plans are documented

### Fundraising

Ready when:

- financial metrics reconcile to source systems
- market and traction claims cite evidence
- cap table and outstanding obligations are current
- customer concentration is transparent
- unit economics use consistent definitions
- material technical, legal, and operational risks are explicit
- investor metrics can be reproduced from source artifacts

### Acquisition

Ready when:

- ownership and IP chain are clean enough to evaluate
- critical contracts and change-of-control terms are indexed
- financial history reconciles
- security incidents and liabilities are traceable
- critical dependencies and founder concentration are visible
- unresolved disputes are disclosed

### Insurance underwriting

Ready when:

- agent inventory and authority boundaries are known
- exposure and loss scenarios are quantified
- controls and evals have current evidence
- incidents and claims history are complete
- provider concentration and systemic dependencies are visible
- retained risk and requested coverage are internally consistent

### Marketplace certification

Ready when:

- identity and authority are verifiable
- capability claims link to assurance evidence
- pricing and service terms are machine-readable
- transaction and dispute history is attributable
- reputation evidence resists self-dealing or wash activity
- revoked/deprecated capabilities cannot remain advertised as current

## 9. Diligence request protocol

When an agent receives a diligence question:

1. classify the requester and transaction type
2. authenticate the requester where needed
3. identify the exact claim being requested
4. locate authoritative evidence
5. check freshness, integrity, sensitivity, and permission
6. redact to minimum necessary scope
7. answer with claim ID, evidence IDs, as-of date, and qualification
8. log the disclosure event
9. set follow-up tasks for missing or stale evidence

A good response is: "Claim X is verified as of date Y by evidence A and B, subject to qualification Q." A bad response is a fluent paragraph with no source lineage.

## 10. Diligence automation architecture

A production implementation usually needs:

- source connectors to finance, CRM, observability, security, contract, and repository systems
- evidence normalizer
- canonical claim registry
- policy engine for audience and sensitivity
- freshness monitor
- contradiction detector
- redaction service
- integrity/attestation service
- request and disclosure ledger
- readiness evaluator
- human approval for high-risk disclosures

Keep the policy and authorization layer outside the model. The model may propose which evidence answers a question; deterministic controls decide whether it may be disclosed.

## 11. Useful diligence metrics

Track operating quality, not just room completeness.

- percent of material claims with current evidence
- stale evidence count by domain
- contradiction count and mean time to resolution
- median diligence response time
- percent of questions answered from canonical evidence without manual reconstruction
- unauthorized-disclosure blocks
- redaction defect rate
- evidence refresh SLA attainment
- procurement cycle time
- investor/insurer follow-up rate caused by missing evidence
- transaction close rate after room access

A useful north-star metric is **verified claims answered from canonical evidence / total material diligence claims requested**.

## 12. Failure modes

### Static PDF graveyard

Files exist but nobody knows which claims they support or whether they are current. Fix by linking every material claim to explicit evidence IDs and freshness rules.

### Over-sharing

The same full room is sent to every requester. Fix with audience-scoped views and progressive disclosure.

### Generated assertions without sources

An agent answers questionnaires from memory or model priors. Fix by requiring source-linked claims and failing closed when evidence is missing.

### Stale trust center

Security and compliance claims remain public after architecture or providers change. Fix with expiry dates, dependency-triggered recertification, and automated refresh tasks.

### Metric drift

Different teams calculate ARR, retention, margin, or availability differently. Fix with canonical metric definitions and source queries.

### Hidden bad news

Risks and incidents are omitted to make the company look cleaner. This destroys trust when discovered. Keep material risk explicit and permissioned.

## 13. Business opportunities

The evidence layer itself can become a business.

Potential products include:

- autonomous security questionnaire responders that only answer from approved evidence
- agent-native trust centers with live claim provenance
- diligence graph infrastructure connecting claims to source systems
- insurer underwriting feeds for autonomous-agent controls and incidents
- continuous marketplace certification
- evidence freshness and contradiction monitoring
- scoped disclosure gateways for agents
- machine-readable transaction readiness scores
- signed proof-of-capability and proof-of-control services
- acquisition/fundraising readiness agents that reconcile source systems before a process starts

The defensible layer is not generic document generation. It is trusted connectivity to authoritative systems, policy-aware disclosure, evidence provenance, and continuous verification.

## 14. Repository implementation

Start with:

- `templates/DILIGENCE_ROOM.json`
- `schemas/diligence-room.schema.json`
- `scripts/validate_diligence_room.py`

Validate a populated room with:

```bash
python scripts/validate_diligence_room.py path/to/diligence-room.json
```

The validator intentionally fails on placeholder hashes, unauthorized evidence for the selected audience, stale claims/evidence, broken references, unresolved critical risks, and inconsistent `ready` status.

The JSON Schema defines the portable shape. The validator adds cross-record business rules that JSON Schema alone cannot enforce.

## 15. Handoff checklist

Before another agent takes over diligence operations, ensure it can answer:

- What is the canonical room?
- What audience is currently being served?
- Which claims are verified, qualified, draft, or disputed?
- Which artifacts expire next?
- Which risks block readiness?
- Which systems are authoritative for financial, customer, security, legal, and operational facts?
- What may be disclosed automatically?
- What requires human or legal approval?
- What was most recently shared externally?
- What contradictions or evidence gaps remain open?

If those questions are machine-answerable, diligence becomes an operating capability rather than a recurring emergency.
