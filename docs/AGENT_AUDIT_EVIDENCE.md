# Agent Audit Trails, Evidence Retention, and Tamper-Evident Action History

Production agents need more than logs. They need a durable evidence layer that can answer **who acted, for whom, under which release/policy/authority, what happened, what proof survives, and what may be missing** without re-executing the action.

This guide defines that layer for agent businesses. It complements runtime observability and incident response; it does not replace either.

## Core rule

**Tamper-evident is not tamper-proof, and integrity is not completeness.**

A hash chain can show that captured records were not silently reordered or rewritten inside its declared trust boundary. It cannot prove that every relevant action was captured. A production evidence system therefore needs two independent claims:

1. **integrity claim** — can retained events be checked for alteration, ordering, and declared signatures/anchors?
2. **coverage claim** — what event population was expected, which records arrived, and which spans or side effects may be absent?

Never collapse these into a single “audit complete” flag.

## What belongs in the audit plane

Capture evidence for consequential lifecycle events, including:

- agent run start/end and outcome;
- model calls and material model-routing decisions;
- tool calls, approvals, refusals, and execution results;
- authority and policy allow/deny decisions;
- retrieval/source access and memory writes with disclosure-safe references;
- external side effects such as payments, orders, messages, account changes, or deployments;
- billing/metering decisions and customer-visible usage events;
- selected release, model, tool, and policy versions;
- incident, containment, recovery, and evidence-freeze events.

Do not automatically store raw prompts, credentials, access tokens, private customer content, or full tool payloads. Prefer stable references, digests, field classifications, and receipts that let an authorized investigator retrieve protected evidence from its proper boundary.

## Canonical event correlation

A reconstructable event should carry enough context to join across systems:

- `event_id` and monotonic `sequence` within the declared stream;
- `occurred_at` with timezone;
- `event_type`;
- `run_id` / workflow correlation;
- tenant or customer reference;
- agent identity and principal/delegator reference;
- release, model/tool, and policy version references where applicable;
- authority decision or envelope reference for consequential actions;
- trace/span identifiers when observability exists;
- side-effect receipt reference when an external system was changed;
- payload digest/reference rather than sensitive raw content;
- previous-event hash and event hash when hash chaining is declared.

Prompt text, model confidence, or an agent-generated explanation is not authority evidence.

## Integrity levels

Use the weakest truthful level that the implementation can actually verify.

| Level | Meaning | Appropriate claim |
|---|---|---|
| `observed_unverified` | Event exists but has no integrity mechanism beyond ordinary storage | “Observed record; alteration not independently detectable” |
| `internally_checked` | Append-only controls and/or hash chain can detect alteration within an internal trust boundary | “Integrity checked within declared boundary” |
| `independently_verifiable` | Portable signatures/receipts or verifier artifacts can be checked outside the runtime that acted | “Independently verifiable under stated keys/trust assumptions” |
| `externally_anchored` | Integrity state is additionally anchored/attested by an external system | “Externally anchored as of the recorded checkpoint” |

External anchoring can strengthen *when a particular digest existed*. It still does not prove that omitted events never happened.

## Hash-chain profile for portable bundles

The repository verifier uses a deliberately simple dependency-free profile for portable examples. For each event, compute SHA-256 over this UTF-8 string:

`sequence|event_id|occurred_at|event_type|run_id|tenant_ref|authority_ref|prev_hash|payload_digest`

Use an empty string for an optional value that is absent. The first event uses `GENESIS` as `prev_hash`; each later event must point to the previous `event_hash`.

This profile is for interoperability and testability, not a claim that SHA-256 chaining alone creates legal-grade evidence. Production systems may use Merkle structures, signed receipts, transparency logs, HSM-backed signatures, trusted timestamps, or other mechanisms. Record the actual trust boundary and verifier assumptions.

## Separation of duties

Do not let the same autonomous runtime silently own every evidence function.

At minimum distinguish:

- **runtime writer** — emits events; does not gain deletion or retention authority from that role;
- **evidence custodian** — stores and protects retained evidence;
- **verifier** — checks sequence/integrity/coverage claims;
- **export authority** — approves bounded disclosure to a customer, auditor, investigator, or counterparty;
- **retention/hold authority** — changes retention or releases a legal/investigation hold.

Execution authority and evidence-custody authority are separate. An incident-response privilege to disable a tool does not imply permission to delete its audit history.

## Retention without invented law

Do not hard-code a legal retention period from this repository. Determine obligations from applicable law, contracts, security policy, insurance, dispute windows, and counsel where needed.

For each evidence class record:

- policy/class identifier;
- minimum and maximum retention configured by the business;
- customer-contract constraints;
- deletion eligibility;
- whether a hold blocks deletion;
- storage boundary and cost owner;
- escalation owner for uncertain obligations.

A hold or active investigation must fail closed: an automated retention job must not delete covered evidence until authorized release is recorded.

## Privacy and tenant isolation

Evidence can be more sensitive than the action it describes. Apply minimization and isolation at capture time:

- use tenant-scoped identifiers and export filters;
- hash or reference private inputs when the raw material is unnecessary;
- redact credentials, secrets, private prompts, and restricted customer content from portable bundles;
- classify protected fields and keep raw material in its authorized storage boundary;
- encrypt retained evidence according to the business security model;
- log evidence access and exports;
- never include another tenant’s events in a customer evidence pack.

## Completeness and coverage

A bundle may claim `complete_for_declared_scope` only when the declared scope has an expected event population and deterministic coverage accounting. Track at least:

- expected versus captured event count;
- missing sequence numbers;
- orphan tool calls with no matching run/decision context;
- tool side effects lacking authority provenance;
- ingestion delay or dropped-event evidence;
- known logging outages or compromised emitters;
- scope start/end and event classes included.

When these cannot be established, use `partial` or `unknown`; do not infer completeness from the absence of errors.

## Incident integration

When an incident is suspected:

1. preserve evidence before cleanup or destructive remediation where safe;
2. freeze applicable retention/deletion paths;
3. record which logger/collector components may themselves be compromised;
4. compare independent receipts, traces, provider records, and side-effect systems against the primary event stream;
5. flag missing or tampered spans instead of rewriting them;
6. reconstruct what can be supported by evidence and keep hypotheses separate;
7. release evidence holds only through authorized review.

The incident record should reference audit evidence; it should not copy private evidence into a public postmortem.

## Export and chain of custody

A bounded evidence export should declare:

- bundle ID and exact event scope;
- tenant/customer scope;
- exporter identity/reference and authority evidence;
- export timestamp;
- redactions and excluded classes;
- integrity mode and verification result;
- known coverage gaps;
- custody transfers (from/to, timestamp, purpose, digest/reference);
- whether signatures or external anchors were actually verified.

A verifier must not execute commands, replay payments, resend messages, or invoke tools. Reconstruction is analysis of retained evidence, not re-execution.

## Metrics founders should watch

Useful operating metrics include evidence coverage percentage, orphan tool-call rate, missing authority-link rate, delayed-ingestion rate, integrity failures, cross-tenant export rejects, retention cost, anomalous evidence access, reconstruction success rate, and time to produce a bounded customer/audit evidence pack.

## Repository assets

- schema: `schemas/audit-evidence-record.schema.json`
- conservative starter: `templates/AUDIT_EVIDENCE_RECORD.json`
- dependency-free verifier: `scripts/verify_audit_evidence.py`
- failure-mode tests: `tests/test_audit_evidence.py`

Run:

```bash
python scripts/verify_audit_evidence.py templates/AUDIT_EVIDENCE_RECORD.json
python -m unittest tests.test_audit_evidence
```

The starter is intentionally non-operational: no captured events, no destructive retention authority, no completeness claim, and no assertion that integrity has been proven.