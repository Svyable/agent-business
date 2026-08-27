# Machine-Executable Founder Launch Packet

A founder launch packet is the durable state object for an agent-built business. It lets one agent stop and another resume without reconstructing the business from chat history, prose notes, or memory.

Use `templates/FOUNDER_LAUNCH_PACKET.json` as the starter artifact and `schemas/founder-launch-packet.schema.json` as the contract.

## What the packet preserves

The packet keeps five things separate:

1. **Business state** — hypothesis, ICP, pain, offer, price, channel, unit economics, and stack.
2. **Evidence** — source-linked observations with timestamps, expiry, and confidence.
3. **Decisions** — explicit choices tied back to evidence rather than hidden reasoning.
4. **Authority** — deterministic limits on outreach, spend, contracts, and approval-required actions.
5. **Execution state** — experiments, blockers, and next actions mapped to `agent-index.json` resource IDs.

The packet is not a replacement for accounting records, CRM data, contracts, secrets, or production state. It is the coordination artifact that points to those systems and carries founder-stage context across agents.

## Handoff protocol

When an agent receives a packet:

1. Run `python scripts/validate_launch_packet.py path/to/packet.json`.
2. Read `stage` and resolve it against `agent-index.json`.
3. Review critical blockers before doing any work.
4. Check authority before outreach, spend, contracts, credential changes, regulated actions, or irreversible external side effects.
5. Treat expired evidence as invalid until refreshed. Do not silently reuse stale market, customer, pricing, regulatory, or supplier facts.
6. Execute only `next_actions` whose `resource_id` exists in the repository index.
7. Add new evidence before approving a decision that depends on it.
8. Update `updated_at`, decisions, blockers, experiments, and next actions after meaningful work.
9. Leave the packet in a state another agent can validate and resume.

## Evidence rules

Every evidence item should answer four questions:

- **What claim does this support?**
- **Where did it come from?**
- **When was it observed?**
- **When should it be considered stale?**

Good sources include interview notes, signed pilot commitments, invoices, analytics exports, benchmark runs, vendor documentation, customer emails, contract artifacts, and public primary sources. Avoid recording unsupported conclusions as evidence.

Use short expiry windows for fast-changing facts such as model pricing, API capabilities, prospect status, regulations, and vendor availability. Longer expiry windows are acceptable for stable historical facts.

## Decision rules

A decision is not merely a note. It has a topic, a value, supporting evidence IDs, and a status.

Useful decision topics include:

- `target_icp`
- `primary_pain`
- `offer_scope`
- `price`
- `acquisition_channel`
- `delivery_model`
- `go_live`
- `supplier_selection`
- `spend_policy`

Only one decision for a topic should remain `approved`. When a decision changes, mark the old one `superseded` instead of deleting history.

## Authority rules

Never infer permission from the fact that a task appears in `next_actions`.

`authority` is intentionally explicit. A packet can say that an agent may research a prospect while still forbidding it from contacting the prospect. It can allow spend while capping the amount. It can forbid contract execution while permitting contract drafting.

If actual runtime permissions are narrower than the packet, the runtime permissions win. If the packet is narrower, the packet wins.

## Stage progression

`stage` stores a resource ID from `agent-index.json`, not an arbitrary label. This keeps the packet coupled to the repository's machine-readable founder path.

Advance the stage only when the current stage has produced enough evidence and artifacts to justify moving forward. Do not advance merely because a document was read.

Typical early progression:

```text
pick -> validate -> offer -> sell -> monetize -> operate
```

Later-stage businesses can jump directly to the relevant indexed resource when the prerequisites already exist, but the packet should preserve the evidence for that claim.

## Example: service business

A local-services receptionist agent might carry:

- `stage`: `validate`
- ICP: multi-location HVAC companies with missed-call leakage
- evidence: call logs, interview notes, current booking conversion, explicit willingness-to-pay
- decision: approved pilot price of $750/month
- authority: customer outreach allowed, spend capped at $100, contracts require approval
- experiment: contact 30 qualified companies and pass on 3 qualified calls or 1 paid pilot
- next action: use the `validate` resource until the commercial signal exists

A second agent should be able to inspect that packet and know exactly what to test next without seeing the first agent's conversation.

## Example: agent-native infrastructure business

An agent observability vendor might carry:

- `stage`: `prove`
- ICP: teams running revenue-critical autonomous workflows
- evidence: benchmark results, incident data, buyer acceptance criteria, competitor pricing
- decisions: supported runtime scope, pricing basis, minimum reliability target
- authority: benchmark execution allowed, production credential changes require approval
- experiment: prove a measurable reduction in mean time to detect or failed autonomous runs
- next action: rerun assurance tests after any model, tool, or runtime dependency changes

## Validation

Run:

```bash
python scripts/validate_launch_packet.py templates/FOUNDER_LAUNCH_PACKET.json
```

The validator intentionally adds semantic checks beyond basic JSON shape:

- the packet stage and action resources must exist in `agent-index.json`;
- evidence IDs must be unique;
- decisions cannot reference missing evidence;
- expired evidence fails validation by default;
- multiple approved decisions for the same topic are rejected;
- spend must be zero when spend authority is disabled;
- critical blockers cannot coexist with work marked `doing`;
- approval-required actions require an explicit approval policy.

For an archival packet whose evidence is expected to be stale, use `--allow-stale`. Do not use that flag as a shortcut for live decision-making.

## Design principle

A scalable agent-founder ecosystem needs portable business state, not just portable prompts. The launch packet is deliberately boring, auditable, versioned, and easy to diff. That makes it suitable for handoffs, evals, approvals, incident review, and eventually interoperability between founder agents and business-operating systems.
