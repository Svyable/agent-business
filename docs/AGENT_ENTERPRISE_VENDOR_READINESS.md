# Enterprise Buyer Security, Procurement, and Vendor Readiness

Agent founders can have a capable product and still fail enterprise procurement because evidence is scattered, stale, overstated, or inconsistent.

This playbook turns existing Agent Business controls into a truthful buyer-facing evidence pack without pretending that repository guidance is a certification, audit opinion, penetration test, customer reference, legal approval, or grant of production authority.

The operating rule is:

> Answer enterprise buyers from current evidence, not memory, optimism, or a previous customer's questionnaire.

## Why this is a distinct founder problem

Enterprise buyers increasingly evaluate agent vendors across three layers at once:

1. **traditional vendor risk** — company, security, privacy, reliability, business continuity, incident response, contracts, support;
2. **AI-specific risk** — model/provider use, customer-data training, retention, residency, evals, change control, human oversight, prompt/tool abuse, rollback;
3. **agentic authority risk** — non-human identity, delegated permissions, tool access, external actions, observability, revocation, and autonomous blast radius.

A good vendor pack does not merely say "we are secure." It lets a buyer determine:

- who owns the system,
- what the system can access and do,
- what customer data it processes,
- which third parties participate,
- what evidence supports each important assertion,
- how incidents and changes are handled,
- what remains self-attested,
- what is independently verified,
- and what is still missing.

## Canonical artifacts

- Playbook: `docs/AGENT_ENTERPRISE_VENDOR_READINESS.md`
- Schema: `schemas/vendor-readiness-record.schema.json`
- Safe starter: `templates/VENDOR_READINESS_RECORD.json`
- Semantic validator: `scripts/validate_vendor_readiness.py`

Validate a record:

```bash
python scripts/validate_vendor_readiness.py templates/VENDOR_READINESS_RECORD.json
```

The starter is deliberately `needs_review`. It claims no certification, audit, penetration test, residency commitment, production-data approval, or production authority.

## Evidence states

Every reusable control assertion should be classified as one of:

### `verified`

Use only when current evidence is stronger than an internal assertion alone. Depending on the claim, appropriate evidence may include a public registry/artifact, third-party audit, current penetration-test reference, contractual evidence, or independently generated system evidence.

`verified` does **not** mean globally certified. Scope still matters.

### `self_attested`

The vendor has reviewed the assertion and stands behind it, but the claim is not independently verified.

This is often legitimate for policies, architecture decisions, operational procedures, or young-company controls. Label it truthfully.

### `not_applicable`

The question does not apply to the offering. Explain why. Do not use N/A to hide a missing control.

### `missing`

The control, owner, evidence, or answer is not ready.

Missing is a useful state because it creates a procurement backlog before a buyer discovers the gap.

### `expired`

Evidence was once useful but is no longer current enough for the claim.

Do not silently reuse an old audit, penetration test, subprocessor list, policy review, or architecture diagram as if nothing changed.

## Enterprise buyer evidence map

Build one reusable evidence pack across these categories.

| Category | Typical buyer question | Existing Agent Business source |
|---|---|---|
| Company/entity | Who is the contracting entity and who can bind it? | `docs/AGENT_ENTITY_GOVERNANCE.md` |
| Security | How are threats, secrets, isolation, and unsafe actions controlled? | `docs/AGENT_SECURITY_EVALS.md` |
| Privacy/data | What data is processed, retained, shared, or used for training? | `docs/AGENT_DATA_MEMORY_PROVENANCE.md`, `docs/AGENT_LEGAL_COMPLIANCE.md` |
| Agent identity | How are agents/workloads identified? | `docs/AGENT_IDENTITY_TRUST.md`, `docs/AGENT_CREDENTIAL_IDENTITY.md` |
| Authority | What can the agent actually do and how is authority revoked? | `docs/AGENT_AUTHORITY_DELEGATION.md` |
| Observability | What is logged and how is behavior investigated? | `docs/AGENT_DISCOVERY_OBSERVABILITY.md`, runtime/reliability guidance |
| Incident response | How are unsafe behavior, compromise, and customer impact contained? | security, economic-integrity, runtime guides |
| Reliability | What SLOs, failure recovery, idempotency, and rollback exist? | `docs/AGENT_RUNTIME_RELIABILITY.md` |
| Commercial | What exactly is bought, accepted, billed, and supported? | service contracting, billing, fiscal guides |
| Diligence | What evidence can be packaged safely for review? | `docs/AGENT_DILIGENCE_DEAL_ROOM.md` |
| AI governance | How are model/tool changes, evals, oversight, and rollback handled? | security/evals, capability assurance, authority guides |
| Customer lifecycle | How does pilot evidence become a bounded production service? | customer-success and service-contracting guides |

Do not copy all of those guides into a questionnaire. Reuse the evidence and link to the applicable control owner or private evidence location.

## The procurement workflow

### 1. Inventory the offering boundary

Before answering a questionnaire, state exactly what the buyer is evaluating:

- product/service name,
- deployment model,
- customer-facing components,
- agent/runtime components,
- model providers,
- tool/API dependencies,
- customer-data categories,
- expected external actions,
- human-review points,
- pilot versus production boundary.

Security answers for a customer-hosted deployment may differ materially from vendor SaaS. Scope the answer.

### 2. Build reusable control assertions

Convert recurring buyer questions into stable control assertions.

Examples:

- agent identities use bounded workload credentials rather than shared long-lived human credentials;
- production tool permissions are scoped by explicit authority policy;
- consequential external actions require deterministic policy and/or approval;
- customer data is not used for model training under the documented product/provider configuration;
- model and tool changes follow a versioned change-control path;
- critical incidents can disable or revoke agent access;
- production telemetry supports reconstruction of consequential actions without logging secrets.

Each assertion needs:

```text
control id
category
plain-language assertion
status
owner
current evidence references
scope/limitations
```

### 3. Separate evidence from the questionnaire

A customer questionnaire is not the source of truth.

Use this structure:

```text
canonical control/evidence record
        |
        +--> reusable answer library
        |
        +--> Customer A questionnaire
        |
        +--> Customer B portal
        |
        +--> diligence room
```

If two questionnaires receive contradictory answers to the same underlying question, fix the canonical record first.

## Evidence handling

Public repositories should contain only disclosure-safe metadata and public evidence.

Private buyer evidence often belongs elsewhere, including:

- audit reports,
- penetration-test reports,
- detailed network diagrams,
- customer-specific DPAs,
- insurance certificates with restricted details,
- private incident reports,
- private customer references,
- vulnerability details,
- confidential policy attachments.

A public record may reference a private evidence identifier such as:

```text
evidence/security/pen-test/2026-q2
```

Do not paste the report itself into a public issue or repository merely to make the validator happy.

## Certifications and audits

Never infer certification from best-practice guidance.

Bad:

```text
SOC 2 compliant because our architecture follows SOC 2-style controls.
```

Better:

```text
SOC 2 status: not held.
Security controls are self-attested and evidence-backed as listed in the vendor readiness record.
```

If a certification is actually held, record:

- exact name,
- status,
- scope,
- applicable product/entity,
- current evidence reference,
- validity period when relevant.

The validator requires current third-party/public evidence for `held` certification claims.

## Security questionnaire answer classes

### Reusable

Stable answer tied to canonical evidence.

Examples:

- authentication architecture,
- encryption approach,
- retention policy,
- incident process,
- supported deployment models,
- model-provider inventory.

### Customer-specific

Depends on negotiated scope or customer configuration.

Examples:

- a specific residency commitment,
- customer-specific retention period,
- private connectivity,
- custom model/provider exclusions,
- bespoke RTO/RPO,
- named support escalation,
- customer-specific audit rights.

Customer-specific answers require owner review because they may become contractual commitments.

## Subprocessor and provider inventory

Treat models, hosting, data services, observability platforms, communications providers, and support systems as part of the buyer's dependency picture when they process customer data or materially support the service.

For each relevant provider record:

- name,
- purpose,
- data categories,
- processing regions,
- current/planned/removed state,
- evidence reference.

Maintain a material-change process:

```text
provider change proposed
        |
        v
security/privacy impact review
        |
        v
contract/DPA constraints checked
        |
        v
buyer notice/consent obligation evaluated
        |
        v
inventory + evidence updated
        |
        v
production rollout
```

Do not promise a frozen provider list unless the contract actually supports that promise.

## Data flow, residency, retention, and training

An enterprise buyer should be able to trace:

```text
customer input
 -> application
 -> agent/runtime
 -> model/provider
 -> tools/subprocessors
 -> storage/logging
 -> output
 -> retention/deletion
```

Answer separately:

- input retention,
- output retention,
- telemetry/log retention,
- backup retention,
- training/fine-tuning use,
- human review/access,
- processing regions,
- storage regions,
- cross-border transfers,
- deletion path.

Do not convert "provider supports region X" into "all customer data stays in region X." Residency claims must match the actual architecture and configuration.

## AI- and agent-specific disclosures

Traditional SaaS questionnaires often miss the agent-specific risk surface. Add explicit answers for:

### Agent identity

- Is each production agent/workload individually identifiable?
- Is ownership recorded?
- Are credentials short-lived or rotation-capable?
- Can access be revoked independently?

### Tool authority

- Which tools can the agent call?
- Which actions change external state?
- What limits apply by amount, customer, environment, or time?
- What requires approval?

### Model/provider behavior

- Which models/providers may process customer data?
- Can providers retain or train on input?
- How are model/version changes controlled?
- Is fallback routing allowed?

### Human oversight

- Which actions require review?
- What does the reviewer see?
- Can the system fail closed when review is unavailable?

### Evals and monitoring

- What failure modes are tested before production?
- Which safety/quality metrics are monitored?
- What triggers rollback, access revocation, or kill switches?

### Prompt injection and untrusted input

- Which inbound content is treated as untrusted?
- Can retrieved content alter authority?
- Are tool outputs validated before consequential actions?

## SLA, SLO, support, and continuity evidence

Enterprise readiness is broader than security.

Package evidence for:

- service availability definition,
- measurement method,
- exclusions,
- incident severity definitions,
- support hours/channels,
- escalation path,
- backup/restore behavior,
- disaster recovery assumptions,
- RTO/RPO only when actually engineered and measured,
- dependency outage behavior,
- rollback and degraded-mode behavior.

Do not promise an RTO/RPO because a cloud provider has one. Your end-to-end service may have different recovery characteristics.

## Pilot authority is not production authority

A procurement process can create pressure to widen access just to unblock a demo.

Keep separate scopes:

| Phase | Data | Tools/actions | Typical rule |
|---|---|---|---|
| Demo | synthetic/public | non-production | no customer production access |
| Pilot | minimized approved data | bounded sandbox or narrow live workflow | explicit pilot authority |
| Production | approved production data | approved production actions | separate production authorization |

The vendor-readiness record itself always sets `offering.production_authority_granted` to `false`.

Real production authority must come from the customer's operating environment, contracts, access controls, and explicit delegation—not procurement metadata.

## Pilot-to-production gate

Before production, verify at minimum:

1. security review complete,
2. legal/commercial review complete,
3. customer data scope approved,
4. production agent/tool authority separately approved,
5. identity and credential lifecycle operational,
6. production observability and incident handling operational,
7. subprocessor/provider inventory current,
8. retention/residency behavior matches commitments,
9. support/SLO ownership assigned,
10. rollback and access-revocation path tested.

Passing procurement does not automatically satisfy this gate.

## Evidence freshness

Evidence should carry:

- observed date,
- expiry date when meaningful,
- current/expired/superseded/disputed state,
- exact scope.

Examples that frequently go stale:

- penetration tests,
- audit reports,
- subprocessor lists,
- model/provider settings,
- data-residency configurations,
- architecture diagrams,
- business-continuity tests,
- insurance evidence,
- customer references.

Expired evidence should become a visible backlog item rather than silently retained as current.

## Failure-mode evals

Test the procurement system against these cases.

### 1. Fabricated certification

**Scenario:** questionnaire says SOC 2 is held because controls resemble SOC 2.

**Expected:** reject the claim unless actual current scoped evidence exists.

### 2. Self-attestation mislabeled verified

**Scenario:** a control is marked `verified` using only the founder's own policy statement.

**Expected:** downgrade to self-attested or attach stronger evidence.

### 3. Expired penetration test

**Scenario:** old test remains linked as current after its evidence validity period.

**Expected:** validation fails until evidence status is corrected/refreshed.

### 4. Unsupported residency claim

**Scenario:** buyer answer says all data stays in one region while provider/tool flow is unresolved.

**Expected:** remain `needs_review`; do not make the commitment.

### 5. Incomplete subprocessor inventory

**Scenario:** current provider has no processing region or evidence.

**Expected:** block buyer-ready state.

### 6. Contradictory questionnaires

**Scenario:** two customers receive different reusable answers for the same control without a configuration difference.

**Expected:** reconcile canonical evidence before another submission.

### 7. Customer-specific answer reused globally

**Scenario:** one negotiated retention term becomes the default answer for all buyers.

**Expected:** keep it customer-specific and owner-reviewed.

### 8. Private questionnaire leaked publicly

**Scenario:** raw customer questionnaire or restricted security report is committed for convenience.

**Expected:** reject/redact; store only safe metadata/reference.

### 9. Excessive demo permissions

**Scenario:** sales demo receives production credentials to accelerate procurement.

**Expected:** deny; demo/pilot authority stays bounded independently of buyer urgency.

### 10. Procurement mistaken for production approval

**Scenario:** vendor is approved in procurement, so agent receives production authority automatically.

**Expected:** deny. Production authority requires separate explicit approval.

### 11. Model provider changes silently

**Scenario:** fallback model starts processing customer data in a new region.

**Expected:** run material-change review, update evidence, evaluate notice/contract implications before production use.

### 12. Unsupported RTO/RPO

**Scenario:** sales copies infrastructure-provider recovery claims into the customer SLA.

**Expected:** reject until end-to-end service recovery is engineered and evidenced.

## Readiness definition

A record may become `buyer_ready` when:

- required security/privacy/data/identity/observability/incident/reliability/continuity/AI-governance categories are represented,
- required controls are not missing or expired,
- assertions labeled verified/self-attested have current evidence,
- certifications labeled held have current external evidence,
- customer-data training use is known,
- residency assertions are supported,
- agent governance has current evidence,
- customer-specific answers are reviewed,
- disclosure-safe privacy flags pass.

`buyer_ready` means the reusable evidence pack is coherent enough to submit for buyer review.

It does **not** mean:

- certified,
- legally compliant in every jurisdiction,
- penetration-tested unless evidence says so,
- accepted by a specific buyer,
- contractually approved,
- authorized for customer production data,
- authorized to take production actions.

## Opportunity for agent founders

Enterprise procurement itself is an agent-business opportunity.

Useful products can help vendors:

- map repeated questionnaires to canonical evidence,
- detect contradictory answers,
- flag stale audit/control evidence,
- maintain subprocessor/model-provider inventories,
- generate scoped buyer packs,
- distinguish self-attested from externally verified claims,
- trace AI-specific questions to agent identity/authority/eval evidence,
- manage pilot-to-production gates.

The valuable automation is not "answer every security question yes."

It is **faster truthful evidence assembly with fewer unsupported commitments**.
