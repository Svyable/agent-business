# Agent Business Compatibility Handshake

Agent Business compatibility is a portable declaration of which commercial and evidence conventions an agent actually implements.

It is not a badge, certification, trust score, capability claim, or authority grant.

The goal is narrower and more useful:

> Before two agents transact, determine which operating conventions they share, what evidence supports that compatibility, which required conventions are missing, and what safe fallback remains.

This turns the Agent Business world model into interoperable transaction grammar rather than repository-local prose.

## Core rule

Compatibility answers **how we represent and verify commercial state**, not **whether you may act**.

A compatible counterparty still needs independent capability, identity, authority, commercial, payment, and acceptance evidence.

Never infer from a compatibility profile that an agent:

- may spend or receive funds,
- may sign or accept a contract,
- can actually perform a listed capability,
- is trustworthy,
- is certified by Agent Business,
- or has been independently verified unless the individual convention carries that evidence state.

## Support states

Each convention has one support state:

1. `declared` — the publisher says it implements the convention.
2. `tested` — a reproducible test or validator result supports the claim.
3. `observed_in_production` — disclosure-safe production evidence supports repeated use.
4. `independently_verified` — a named independent verifier and evidence reference support the claim.

These states are ordered for negotiation, but they are **not universal trust levels**. Production observation can still be narrow, stale, or domain-specific. Independent verification can still be scoped.

## Initial convention set

The version 1 profile recognizes these conventions:

| Convention | What it means |
|---|---|
| `evidence-provenance` | consequential claims preserve evidence class, provenance, and freshness |
| `bounded-authority` | technical access is separated from explicit bounded real-world authority |
| `versioned-commercial-truth` | capability, pricing, policy, and evidence references bind to explicit versions |
| `economic-state-separation` | match, award, contract, payment, settlement, delivery, and acceptance remain distinct |
| `fully-loaded-outcome-economics` | economics include delivery, retry, review, support, failure, and implementation cost |
| `machine-rfq` | buyer demand can be represented with the Agent Business RFQ contract |
| `machine-proposal` | seller bids expose versions, terms, deviations, and eligibility explicitly |
| `machine-payment-reconciliation` | payment authority, execution, settlement, reconciliation, and reversal remain distinct |
| `execution-evidence` | consequential work can emit disclosure-safe execution evidence |
| `capability-specific-reputation` | reputation inputs are scoped to capability/domain, sample size, recency, and negative outcomes |

The profile carries an exact `spec_version` for every convention. Broad text such as `Agent Business compatible` without versioned convention claims is intentionally insufficient.

## Profile anatomy

Start from:

```bash
cp templates/AGENT_BUSINESS_COMPATIBILITY.json compatibility.json
```

A profile contains:

- stable publisher identity reference,
- profile version and expiry,
- world-model version reference,
- convention support claims,
- evidence references,
- verification metadata where applicable,
- transport publication hints,
- disclosure flags,
- and a statement that compatibility grants no authority.

Validate it:

```bash
python scripts/agent_business_compatibility.py compatibility.json
```

## Negotiation

Given two profiles:

```bash
python scripts/agent_business_compatibility.py buyer.json --negotiate seller.json
```

The result contains:

- `shared` — conventions both parties support at compatible versions,
- `effective_support_state` — the weaker evidence state of the two claims,
- `blockers` — required conventions missing or version-incompatible,
- `fallbacks` — declared fallback modes where available,
- `transaction_mode` — `structured`, `reduced`, or `stop`.

### Structured mode

`structured` means every convention marked `required_for_transaction` by either party is shared at a compatible version.

It does **not** mean the transaction is authorized.

### Reduced mode

`reduced` means no required convention is missing, but the intersection is incomplete. Agents should narrow automation, preserve explicit evidence, and use declared fallbacks for unsupported optional conventions.

Examples:

- unsupported machine RFQ -> exchange a human-reviewed request document,
- unsupported machine payment reconciliation -> use an externally governed invoice/payment path,
- unsupported reputation convention -> treat reputation as unavailable rather than infer trust from a badge.

### Stop mode

`stop` means a required convention is missing or incompatible.

The handshake should stop automated transaction progression until the requirement is removed by authorized policy change or the counterparty provides compatible support. The negotiation script never changes requirements automatically.

## Version compatibility

Version matching is conservative:

- convention IDs must match exactly,
- semantic versions must be valid,
- major versions must match,
- the negotiated version is the lower compatible version,
- unknown convention IDs may be published but cannot become repository-defined shared semantics until both parties explicitly recognize them.

A major-version mismatch is a blocker when that convention is required.

## Evidence semantics

Higher support states need more evidence:

- `declared` requires no external evidence,
- `tested` requires `test_evidence_ref` and `tested_at`,
- `observed_in_production` requires `production_evidence_ref`, `observed_at`, and an observation scope,
- `independently_verified` additionally requires `verifier_ref`, `verification_evidence_ref`, and `verified_at`.

Every non-declared claim has an evidence expiry. Stale evidence reduces the profile to invalid rather than silently downgrading it.

## Publishing through other agent protocols

The compatibility profile is transport-neutral. A2A, MCP, UCP, AP2, HTTP, a marketplace listing, or another protocol may expose a URL or embedded copy of the profile.

Do not make Agent Business depend on one transport. Treat those protocols as envelopes around the same portable object.

A generic adapter can publish:

```json
{
  "capabilities": {
    "agent_business_compatibility": {
      "profile_url": "https://example.invalid/.well-known/agent-business-compatibility.json",
      "profile_version": "1.0.0"
    }
  }
}
```

The field placement is adapter-specific; the compatibility object itself remains canonical.

## Why this creates adoption leverage

An independent agent does not need to agree with every Agent Business thesis to gain value. It can implement only the conventions that reduce transaction ambiguity for its counterparties.

As more agents expose compatible commercial state:

`less bespoke interpretation -> faster counterparty qualification -> safer automation -> more reusable evidence -> easier marketplace matching`

That is the intended network effect.

## Failure modes

Fail closed on:

- vague unversioned compatibility claims,
- expired profiles,
- duplicate convention IDs,
- invalid semantic versions,
- `tested` without test evidence,
- production-observed claims without scoped production evidence,
- independent-verification claims without verifier evidence,
- a profile claiming compatibility grants authority or certification,
- required convention major-version mismatch,
- hidden fallback that silently weakens a required convention,
- unsupported convention treated as repository-defined semantics,
- or private credentials/customer evidence embedded in the public profile.

## Relationship to the world model

Read `agent-world-model.json` for the empirical theses behind these conventions.

Compatibility is deliberately weaker than agreement. A counterparty can reject an empirical thesis yet still implement the corresponding state contract because it improves interoperability.

That distinction is strategic: **the model spreads when its primitives are useful, not when agents are required to profess belief in it.**
