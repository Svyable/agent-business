# Agent Privacy Requests, Erasure, Consent Withdrawal, and Deletion Verification

Persistent agents turn privacy requests into distributed state-management work. A subject's data can exist in conversations, structured memory, summaries, vector indexes, caches, tool outputs, analytics, exports, subprocessors, backups, and model-training pipelines. A successful delete API call is therefore an operation result, not proof of erasure.

This playbook defines a disclosure-safe operating system for access, correction, deletion/erasure, consent withdrawal, restriction, and portability requests. It is operational guidance, not jurisdiction-specific legal advice.

## Core rules

1. **Do not invent law.** Record the applicable policy/legal determination, supplied deadline, lawful-basis analysis, exemptions, and retention rules by reference. The repository does not manufacture statutory deadlines or legal conclusions.
2. **Map before claiming completion.** Build a subject-to-storage/derivation map across every known surface before saying a request is fulfilled.
3. **Derived state counts.** Summaries, embeddings, cached tool outputs, analytics features, fine-tuning inputs, and other artifacts derived from source data remain separate deletion/correction surfaces.
4. **Deletion needs verification.** Test for retrieval residue and derived-memory resurfacing. Do not equate HTTP/API success with absence.
5. **Recovery must preserve deletion.** Restore/failover paths need tombstones, purge manifests, key-destruction state, or equivalent controls so old backups do not resurrect erased/restricted data.
6. **Downstream uncertainty stays visible.** An unresolved subprocessor or technically unverifiable surface blocks a fully fulfilled erasure claim.
7. **Privacy status grants no unrelated authority.** Execution requires explicit, current authority for the affected data systems.

## Lifecycle

Use these states:

`received -> identity_scope_review -> mapped -> executing -> downstream_pending -> verification -> fulfilled`

Alternative terminal states are `partially_fulfilled`, `denied_with_basis`, and `escalated`.

A status is an operational statement, not a legal conclusion. A record may only advance when its evidence supports the asserted state.

## 1. Intake without public identifiers

Use an opaque `subject_ref` generated inside the authorized privacy system. Public records must not contain names, emails, phone numbers, government identifiers, customer content, raw prompts, credentials, or private evidence.

Record:

- request type;
- received timestamp;
- tenant/customer scope;
- identity/scope review state;
- policy/legal-basis reference;
- deadline only when supplied by the applicable policy/legal determination;
- owner and escalation path.

Do not infer identity from the agent conversation itself.

## 2. Subject-to-storage and derivation map

Inventory every known surface that can contain or regenerate subject-linked information:

| Surface | Examples | Typical operation | Verification question |
|---|---|---|---|
| raw conversation | messages, attachments | delete/redact | can exact records still be fetched? |
| structured memory | profile facts, episodic memory | delete/tombstone | can the subject facts still be recalled? |
| derived summary | rolling summaries, notes | regenerate/redact | does the summary still expose erased facts? |
| vector index | embeddings, chunks | delete/rebuild/partition purge | does scoped semantic retrieval still surface residue? |
| cache | prompt/tool/retrieval cache | evict | can stale cached content reappear? |
| tool output | CRM/support/search results | delete/correct downstream | did the authoritative downstream system acknowledge? |
| analytics/export | events, reports, data lake | delete/redact/aggregate | is subject-linked data still addressable? |
| training pipeline | fine-tuning/eval corpus | remove from future sets/escalate | what has and has not been technically changed? |
| subprocessor | external model/tool/storage | downstream request | has the processor acknowledged completion? |
| backup/recovery | snapshots, replicas | expire/tombstone/key destruction | will restore resurrect the subject data? |

Each surface needs an owner, action, status, evidence references, and restore-protection state.

## 3. Choose a truthful operation

Do not force every surface into a `DELETE` abstraction. Valid approaches include:

- direct deletion;
- redaction;
- tombstone plus compaction/rebuild;
- partition/index rebuild;
- cryptographic key destruction where architecture supports it;
- correction and regeneration of derived artifacts;
- restriction from retrieval/use;
- downstream processor request;
- backup expiry with resurrection prevention;
- escalation when the surface is technically or legally constrained.

The record must distinguish `deleted` from `verified_not_present` and from `unverifiable`.

## 4. Consent withdrawal

Consent withdrawal is a propagation problem, not a universal deletion command. Record the purpose/consent state and the separate policy determination for any processing that may continue under another basis.

Propagation should reach applicable collection, personalization, marketing, memory, analytics, model-training, and subprocessor paths. A request is not complete while an applicable consent-dependent path remains active.

## 5. Correction and restriction

Corrections must update or regenerate derived summaries, vector metadata, caches, and downstream copies so stale state cannot overwrite the corrected source later.

Restrictions must be enforced at retrieval/use time as well as storage time. A row marked restricted is insufficient if the agent can still retrieve the same fact from a vector index or cached tool result.

## 6. Access and portability

Exports require:

- authenticated/authorized request scope;
- tenant isolation;
- redaction of other subjects and protected business/security material as required by policy;
- provenance for exported records;
- disclosure-safe packaging;
- export evidence without placing the private payload in this public record.

A cross-tenant export is a privacy/security incident, not a successful request.

## 7. Erasure verification

For deletion/erasure, verify the declared scope after execution. At minimum measure:

- mapped surfaces versus verified surfaces;
- unresolved downstream processors;
- retrieval-residue count;
- derived-memory resurfacing result;
- known unverifiable surfaces;
- post-restore resurrection test result when backups/recovery can contain the data.

Use representative queries or deterministic probes inside the protected environment. Store only disclosure-safe pass/fail evidence and digests externally; never copy recovered private content into a public verifier log.

A `fulfilled` erasure requires zero known residue in the declared test scope, no unresolved required downstream copies, no unresolved exceptions, and a recovery path that is proven not to resurrect the erased state.

## 8. Holds, retention conflicts, and exceptions

Deletion can conflict with legal/investigation holds, fraud/security evidence, contractual retention, or other policy constraints. Do not resolve these conflicts by agent inference.

Record:

- exception type;
- policy/legal decision reference;
- affected surfaces;
- whether execution is blocked, narrowed, or permitted;
- evidence and reviewer/authority reference;
- resulting request state.

An unresolved exception blocks `fulfilled`.

## 9. Subprocessor propagation

Track every downstream processor that may hold or derive the subject data. Record the request reference, sent timestamp, acknowledgement state, and evidence reference. Do not mark the top-level request fulfilled while required downstream acknowledgements are pending or unknown.

## 10. Continuity and restore safety

Connect privacy operations to business continuity. A recovery plan should consume deletion/correction tombstones or equivalent manifests after restoring older snapshots. Test this explicitly.

If a disaster-recovery exercise resurrects erased/restricted information, reopen the privacy request, preserve evidence, correct the recovery process, and treat the event according to the incident/privacy policy.

## 11. Audit evidence

Keep disclosure-safe evidence references for:

- request receipt;
- identity/scope decision;
- policy/legal determination;
- authority to access/change each system;
- each direct action;
- downstream acknowledgement;
- verification results;
- exceptions/holds;
- final response decision.

Use `audit-evidence` for durable integrity/custody controls. Do not duplicate protected evidence into a portable privacy record.

## 12. Metrics

Useful operating metrics include request age, mapping completeness, verified-surface coverage, retrieval-residue rate, derived-memory residue rate, downstream acknowledgement latency, exception rate, reopen rate, correction regression rate, export isolation rejects, and post-restore resurrection incidents.

## Repository assets

- schema: `schemas/privacy-request-record.schema.json`
- conservative starter: `templates/PRIVACY_REQUEST_RECORD.json`
- dependency-free semantic validator: `scripts/validate_privacy_request.py`
- failure-mode tests: `tests/test_privacy_request.py`

Run:

```bash
python scripts/validate_privacy_request.py templates/PRIVACY_REQUEST_RECORD.json
python -m unittest tests.test_privacy_request
```

The starter intentionally has no identity proof, no execution authority, no mapped private systems, no deadline, and no completion claim. Populate only disclosure-safe references generated by the authorized privacy workflow.
