# Agent authority, consent, and delegation

Autonomous agents should not infer permission from access. A tool being reachable, a credential being present, or a service contract existing does not prove that a specific action is authorized now.

This guide defines a protocol-neutral operating pattern for bounded authority: a principal issues a machine-readable envelope, runtime policy checks evaluate proposed actions against it, delegated agents may only receive narrower authority, and material actions emit evidence linking execution back to the authority that justified it.

## 1. The control object

Use `templates/AUTHORITY_ENVELOPE.json` as the portable control object and validate instances with:

```bash
python scripts/validate_authority_envelope.py path/to/authority.json
```

The envelope separates several concepts that are often dangerously collapsed:

- **identity** — who the principal and delegate are
- **authority** — what the delegate may do
- **purpose** — why the authority exists
- **scope** — actions, tools, data, communications, spend, and geography
- **validity** — when the grant starts and stops
- **delegation** — whether authority may be passed on, and how deeply
- **replay bounds** — whether a grant is single-use or reusable
- **audit evidence** — what approved issuance and what evidence supports it

Do not store private keys, passwords, access tokens, raw secrets, or high-risk credentials in the envelope. Reference secure systems instead.

## 2. Authorization happens at action time

An active envelope is necessary but not sufficient. Before each material action, evaluate the proposed action against current state.

A runtime decision should consider at least:

1. Is the envelope active, unexpired, and not revoked or suspended?
2. Does the proposed action match an allowed action and avoid prohibited actions?
3. Is the requested tool allowed?
4. Is every data class in scope for the stated purpose?
5. Does an outbound message target an approved channel and audience?
6. Is spend below the per-action, cumulative, and approval thresholds?
7. Is geography permitted?
8. Is the replay nonce unused or still within its bounded-use allowance?
9. If delegated, is the parent still valid and is the child strictly no broader?
10. Is any required human approval current and bound to the exact action context?

Fail closed when any required fact is unavailable.

A useful decision record is:

```json
{
  "decision": "deny",
  "authority_id": "auth_...",
  "proposed_action_id": "act_...",
  "reason_code": "SPEND_LIMIT_EXCEEDED",
  "evaluated_at": "2026-08-27T23:00:00Z",
  "policy_version": "2026-08-27"
}
```

Stable reason codes make denied actions observable and debuggable without leaking sensitive policy details.

## 3. Distinguish standing authority from per-action approval

Standing authority is appropriate for low-risk repetitive work. High-impact actions should use narrower, short-lived or single-use grants.

Prefer per-action approval for:

- sending funds or changing payout destinations
- signing or accepting legal terms
- deleting or exporting customer data
- changing production permissions
- publishing public claims on behalf of a principal
- hiring, firing, or materially changing compensation
- creating credentials or adding privileged integrations
- actions with irreversible or difficult-to-compensate effects

A standing grant may state that such an action is generally eligible while still requiring a separate approval threshold at execution time.

## 4. Delegation must attenuate

Delegation is safe only when a child can receive the same or less authority than its parent.

For every child envelope:

- `parent_authority_id` must point to the actual parent
- purpose must remain aligned with the parent's approved purpose
- child action and tool allowlists must be subsets of the parent allowlists
- child spend limits must be no larger
- child expiry must be no later
- child delegation depth must increase by exactly one
- child depth must remain within the parent's maximum depth
- prohibited parent capabilities remain prohibited
- data-use restrictions and consent requirements must not loosen

Validate a child against its parent with:

```bash
python scripts/validate_authority_envelope.py child.json --parent parent.json
```

The local validator checks core attenuation invariants. Production enforcement should also compare data, geography, communication audiences, parameter constraints, and any business-specific policies.

Never accept a chain merely because each object is signed. Signatures prove integrity and issuer identity; they do not prove that a child grant stayed within parent scope or that the parent remains valid.

## 5. Consent and data use

Treat data authorization as purpose-bound rather than as generic access.

For each material data class, capture:

- allowed and prohibited categories
- precise purpose limitation
- retention period
- onward-sharing rule
- consent or lawful-basis reference where applicable
- deletion or revocation propagation path

If onward sharing is allowed, the child agent still needs its own valid authority and should receive only the minimum data necessary.

Revocation must propagate to cached copies, working memory, queues, derived artifacts, and delegated workers where required. See `AGENT_DATA_MEMORY_PROVENANCE.md` for lineage and deletion patterns.

## 6. Replay and idempotency

A captured approval should not be reusable forever.

Use `single_use` for high-risk actions. Bind the nonce to the material action context where possible: recipient, amount, asset, contract version, tool, or request digest. Mark it consumed atomically with execution.

Use `bounded_reuse` only for intentionally repetitive workflows. Track observed uses outside the envelope in trusted state and reject once `max_uses` is reached.

The validator can check a known use count:

```bash
python scripts/validate_authority_envelope.py authority.json --used 3
```

If execution is retried after an ambiguous network failure, use an idempotency key tied to the original authorized action rather than minting a fresh authorization automatically.

## 7. Spend authority

Separate three controls:

- **per-action maximum** — hard ceiling for one transaction
- **total maximum** — cumulative budget for the envelope
- **approval threshold** — amount above which additional approval is required

Runtime spend evaluation should use authoritative settled + reserved spend, not an agent-maintained estimate. Reserve budget before executing non-idempotent purchases and release or settle it deterministically.

A child agent cannot increase any spend bound. Currency conversion should happen through a trusted price source and should include a conservative buffer rather than letting agents exploit stale FX rates.

See `AGENT_COMMERCE.md`, `AGENT_PROCUREMENT_MARKET_DESIGN.md`, and `AGENT_TREASURY_FINOPS.md` for payment and treasury controls.

## 8. Communication authority

Outbound communication is an action surface, not harmless text generation.

Specify approved channels and audiences. Require explicit approval for categories such as:

- public statements
- legal commitments
- contractual promises
- pricing exceptions
- customer-impacting incident notices
- regulated claims
- messages containing sensitive or personal data

Bind approvals to the final rendered message or a deterministic digest when wording matters. If the content changes materially after approval, request approval again.

## 9. Revocation and kill switches

Revocation must beat convenience.

A production system should:

- maintain a low-latency revocation source of truth
- reject cached authority after a short bounded freshness interval
- terminate or quarantine in-flight work when policy requires it
- propagate revocation to delegated children
- invalidate unused reservations and pending approvals
- record who revoked the authority, when, and why

Do not rely solely on an expiry timestamp for emergency control.

## 10. Audit receipts

Each material action should emit an audit receipt that links execution to the authority decision without exposing secrets.

Recommended fields:

```json
{
  "action_id": "act_123",
  "authority_id": "auth_123",
  "parent_chain": ["auth_root"],
  "delegate_id": "agent_ops_7",
  "decision": "permit",
  "policy_version": "2026-08-27",
  "action_digest": "sha256:...",
  "executed_at": "2026-08-27T23:01:04Z",
  "result_reference": "receipt:..."
}
```

Store receipts append-only where practical. A verifier should be able to reconstruct which envelope, policy version, and runtime facts justified the action.

## 11. Integration with the rest of Agent Business

### Service contracts

`AGENT_SERVICE_CONTRACTING.md` defines commercial obligations. Reference an authority envelope for the buyer and seller instead of assuming that possession of a contract grants authority. Contract acceptance and change orders should be signed or approved by principals whose envelopes permit those actions.

### Identity and reputation

Identity proves who an actor is; authority proves what that actor may do. Keep them separate so replacing credentials does not silently widen permissions. See `AGENT_IDENTITY_TRUST.md`.

### Orchestration

Pass an attenuated child envelope with each delegated task. Do not forward a root credential or broad parent token. See `AGENT_ORCHESTRATION.md`.

### Memory

Record the authority ID that permitted any durable write of sensitive business state. When consent is revoked, provenance makes affected memories discoverable. See `AGENT_DATA_MEMORY_PROVENANCE.md`.

### Incidents

Security incident playbooks should include global and principal-specific authority suspension. See `AGENT_SECURITY_EVALS.md`.

## 12. Evals

At minimum, test that the enforcement layer denies:

- expired authority
- revoked authority
- action outside allowlist
- prohibited tool use
- data purpose mismatch
- external communication outside approved audience
- per-action spend overflow
- cumulative spend overflow
- approval-threshold bypass
- nonce replay
- child scope wider than parent
- child expiry beyond parent
- child delegation beyond maximum depth
- execution after parent revocation
- changed action arguments after approval
- action when revocation state cannot be checked

Also test false denials. An authority system that blocks legitimate work unpredictably will be bypassed by operators.

## 13. Business opportunities

Authority infrastructure is itself an agent-native market:

- protocol-neutral policy decision points for MCP/A2A/HTTP tools
- delegated capability-token services
- approval inboxes that bind humans to exact proposed actions
- consent and data-purpose ledgers
- agent spend-control and reservation systems
- cross-agent revocation networks
- authority-chain verification for marketplaces
- audit receipt storage and forensic reconstruction
- policy-as-code test harnesses and certification

The durable moat is not a prettier permission screen. It is reliable enforcement across heterogeneous agents, tools, organizations, and commercial relationships.

## 14. Design principles

1. **Access is not authority.**
2. **Identity is not authority.**
3. **A signature is not sufficient authorization.**
4. **Evaluate authorization at action time.**
5. **Children can only narrow authority.**
6. **High-risk approvals should be short-lived and context-bound.**
7. **Revocation must fail closed.**
8. **Replay protection is part of authorization.**
9. **Every material action should be attributable to an authority object.**
10. **Templates must never fabricate consent, signatures, identity, or legal authority.**

## 15. Current ecosystem signal

This design direction is consistent with emerging 2026 agent infrastructure. Recent work on per-action authorization separates identity and standing capabilities from the decision to approve a specific action under live budget and kill-switch state. Other proposals use attenuating delegation chains across MCP/A2A, while agent-commerce standards increasingly bind consent and transaction context to machine-readable mandates.

Treat these protocols as evolving inputs, not as universal standards. The repository schema is deliberately protocol-neutral so it can wrap whichever identity, signature, transport, or payment system a founder actually uses.
