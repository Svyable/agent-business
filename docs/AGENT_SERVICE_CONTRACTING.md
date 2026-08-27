# Agent Service Contracting and Acceptance

Autonomous commerce needs more than a checkout and a payment rail. A buyer must know what it authorized, a seller must know what it owes, and both sides need a common object for delivery, acceptance, billing, credits, changes, and disputes.

This guide turns those boundaries into an operational contract pack. It is not legal advice and it does not create authority, consent, agency, or enforceability on its own. Use qualified legal counsel and the actual governing agreements for legal conclusions.

## The transaction spine

Treat every paid service as a linked sequence:

`authority → order → delivery → evidence → acceptance → billable event → invoice/payment → credit/dispute`.

Do not let these stages float as separate natural-language conversations. Every downstream artifact should carry stable identifiers back to the contract and relevant delivery receipt.

## Canonical artifacts

Use four durable objects:

1. **Service contract/order** — parties, capability/version, exact scope, price basis, authority limits, SLOs, acceptance criteria, change rules, billing rules, and dispute requirements.
2. **Change order** — a versioned record of any material modification to scope, dependencies, price, data handling, authority, SLOs, or acceptance logic.
3. **Delivery receipt** — what was delivered, when, which deliverable it satisfies, evidence references, acceptance state, and any billable-event ID.
4. **Dispute packet** — the exact contract version, receipt, verification result, billing event, credits, and incident evidence needed to reconstruct the disagreement.

The repository provides a starter contract at `templates/SERVICE_CONTRACT.json`, a schema at `schemas/service-contract.schema.json`, and a dependency-free validator at `scripts/validate_service_contract.py`.

## 1. Bind the contract to capability and version

Never contract for a vague label such as “research agent” or “support automation.” Bind the order to:

- a stable capability ID;
- a capability version;
- a precise scope and explicit out-of-scope list;
- measurable deliverables;
- material dependencies or provider assumptions;
- the applicable data-handling profile.

This prevents a seller from silently changing the service semantics after purchase and gives the buyer a deterministic compatibility check before execution.

## 2. Separate commercial authority from technical capability

An agent may technically be able to call a tool or transfer funds without being authorized to do so. Track separately:

- buyer approval/mandate reference;
- seller authority reference;
- automatic approval threshold;
- human-approval threshold;
- absolute spend ceiling;
- prohibited actions;
- allowed jurisdictions/regions when relevant.

The default template intentionally leaves authority references null. Moving a record from `draft` to `approved` or `active` should require real authority references from the operating environment, not values fabricated by the agent.

## 3. Make pricing replayable

A future auditor should be able to reproduce a charge using only the contract version and measured usage/outcome evidence.

Record:

- currency;
- pricing model;
- immutable price-version ID;
- rate IDs, units, amounts, and minimums;
- billing cadence;
- contract spend ceiling;
- tax treatment when known.

Do not mutate old price objects in place. New pricing should produce a new price version and, when material to an active contract, an approved change order or renewal.

## 4. Define service levels as measurement contracts

An SLO without an authoritative measurement source is just a promise. Each SLO should identify:

- metric;
- target;
- measurement source;
- evaluation window;
- exclusions;
- credit/remedy rule if the target is missed.

Prefer outcome-level metrics over infrastructure vanity metrics. “Successful accepted outcome rate ≥ 95%” is often more commercially useful than “model API uptime ≥ 99.9%,” provided the successful-outcome definition is objective.

## 5. Acceptance must be testable

Every deliverable should point to one or more acceptance criteria. Each criterion needs a verification method such as:

- deterministic test;
- signed system receipt;
- third-party evidence;
- buyer-system confirmation;
- explicitly authorized human approval.

Avoid “looks good” acceptance language for machine-to-machine transactions. When subjective review is unavoidable, name who can approve, what evidence they must review, and the time window.

### Auto-acceptance

Auto-acceptance is useful for high-volume low-risk services, but only when conditions are objective and observable. Good auto-acceptance conditions include deterministic tests passing, required evidence present, no policy violation, and no dispute raised within the acceptance window.

Never infer acceptance solely from silence unless the governing commercial terms expressly permit it.

## 6. Generate delivery receipts before billing

A delivery receipt should include:

- `receipt_id`;
- `contract_id` via the containing contract pack or external reference;
- `deliverable_id`;
- delivery timestamp;
- evidence references;
- acceptance state;
- acceptance timestamp when accepted;
- billable-event ID only when billing conditions are satisfied.

If the contract requires acceptance before charge, the validator rejects a receipt that has a billable-event ID while its acceptance state is not `accepted`.

This creates a clean bridge to the repository's billing and revenue-assurance guidance: billing does not decide whether work was accepted; it consumes the accepted commercial evidence.

## 7. Treat material changes as new authorization events

Model/provider swaps, dependency changes, pricing changes, expanded data access, weaker SLOs, altered acceptance tests, or broader authority can materially change buyer risk.

Define a list of material fields up front. A material change should:

1. create a change-order ID;
2. describe the proposed difference;
3. identify affected deliverables, price, risk, and timing;
4. obtain required approvals;
5. become effective only after approval;
6. preserve the old contract version for audit and dispute reconstruction.

Do not silently update an active JSON contract in place and call that consent.

## 8. Link service credits to observable failure

A service-credit rule should define a measurable trigger, a calculation basis, and a cap. Useful triggers include:

- accepted SLO breach;
- missed delivery deadline;
- verified duplicate charge;
- prolonged service unavailability;
- contractually defined quality failure.

Credits should not be manually improvised after every incident. Encode the rule so a buyer and seller can independently calculate the same result from shared evidence.

## 9. Make disputes reconstructable

A dispute path should specify both required evidence and escalation sequence. A complete packet typically links:

- contract/version;
- buyer and seller authority references;
- approved change orders;
- delivery receipt;
- verification result;
- relevant traces or incident record;
- invoice/billing event;
- payment or settlement reference;
- credits/refunds already applied;
- communications that are contractually relevant.

Keep evidence scoped. A dispute packet should reveal what is necessary to resolve the claim, not dump unrelated customer data, secrets, prompts, or internal traces.

## 10. Handoffs between agents

When a workflow delegates execution to another agent, propagate the commercial boundary, not just the task text.

A child agent should receive only the subset it needs:

- contract ID and version;
- deliverable ID;
- scope;
- deadline/SLO;
- applicable authority and spend limit;
- required evidence;
- acceptance criteria;
- prohibited actions;
- callback for receipt submission.

The child agent must not inherit broader authority than the parent is allowed to delegate.

## 11. Security rules

Treat contract artifacts as authorization-adjacent security objects.

- Bind approvals to the exact contract/version, not a mutable URL.
- Reject replay of single-use approvals or receipts where replay could charge twice.
- Preserve immutable IDs for orders, change orders, receipts, and billing events.
- Do not accept agent-provided evidence as trustworthy solely because it is well-formed JSON.
- Verify signatures, provenance, identity, and permissions in the actual deployment environment.
- Keep secrets and payment credentials out of portable contract files.
- Reject a material dependency change that bypasses change control.

Recent agent-payment work reinforces this pattern: typed mandates establish bounded authorization, while checkout/payment receipts bind authorization to a specific transaction. The same principle should extend through service delivery and acceptance rather than stopping at payment.

## 12. Recommended state machine

A simple contract lifecycle:

`draft → proposed → approved → active → suspended | terminated | expired`

Operational rules:

- `draft`: incomplete, no implied authority;
- `proposed`: ready for review, still no execution authority unless separately granted;
- `approved`: commercial terms accepted but service may not have started;
- `active`: execution and billing may occur within explicit bounds;
- `suspended`: no new execution except permitted remediation/termination actions;
- `terminated` / `expired`: no new delivery or spend unless a surviving obligation explicitly allows it.

The validator requires authority references and approval IDs once a contract enters an authorized lifecycle state.

## 13. Contract tests before launch

At minimum, test these scenarios:

| Scenario | Expected result |
| --- | --- |
| unknown acceptance criterion reference | reject |
| duplicate deliverable or receipt ID | reject |
| auto-approval threshold exceeds spend ceiling | reject |
| active contract lacks buyer/seller authority references | reject |
| billable event exists before required acceptance | reject |
| receipt references unknown deliverable | reject |
| SLO has no measurement source | reject |
| active contract allows silent material changes | warn/review |
| accepted receipt contains no evidence | reject |
| draft contains authority-looking fields | warn; never infer consent |

Run:

```bash
python scripts/validate_service_contract.py templates/SERVICE_CONTRACT.json
```

The starter template should pass with draft-state warnings kept to zero.

## 14. How this composes with the rest of the repository

- **Procurement:** buyer RFQ/bid selection becomes the input to the service contract.
- **Identity and trust:** authority references point to actual identity/mandate systems rather than being invented locally.
- **API interoperability:** `capability_id` and `capability_version` bind commercial expectations to a technical contract.
- **Runtime reliability:** SLOs and dependency changes consume runtime telemetry and incident evidence.
- **Billing:** accepted receipts generate canonical billable events and invoice references.
- **Treasury:** payment/settlement consumes the billing event; it should not recreate service acceptance logic.
- **Legal/compliance:** legal terms and jurisdictional obligations govern the commercial object; this template does not replace them.
- **Diligence:** reusable evidence about security, reliability, compliance, and finances can be disclosed before contracting without being copied into each order.

## 15. Founder opportunities

The missing commercial boundary is itself a business surface. Potential infrastructure products include:

- agent contract registry and version negotiation;
- mandate-to-order authorization gateway;
- acceptance and verification service;
- signed delivery-receipt infrastructure;
- SLO measurement and automatic service-credit engine;
- agent contract linting and policy enforcement;
- change-order approval workflow;
- dispute evidence assembler;
- contract-to-billing reconciliation;
- portable commercial reputation based on verified accepted outcomes rather than self-reported claims.

The defensible layer is not merely generating contract prose. It is maintaining a trustworthy, machine-verifiable state transition from authorized intent to verified outcome and settlement.

## 16. Launch checklist

Before allowing an agent to transact under a service contract, confirm:

- [ ] buyer and seller identities are resolved;
- [ ] real authority references exist outside the template;
- [ ] capability and version are pinned;
- [ ] scope and exclusions are explicit;
- [ ] deliverables map to measurable acceptance criteria;
- [ ] pricing is versioned and replayable;
- [ ] spend ceiling and approval thresholds are consistent;
- [ ] SLO measurement sources are authoritative;
- [ ] material changes require explicit change control;
- [ ] delivery receipts carry evidence;
- [ ] billing cannot outrun acceptance when acceptance is required;
- [ ] dispute evidence and escalation path are defined;
- [ ] the semantic validator passes;
- [ ] applicable legal/compliance review is complete.

A useful contract pack should make the safe action obvious to both humans and agents. When the state is ambiguous, execution or charging should stop rather than guessing what the parties intended.
