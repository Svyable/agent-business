# Agent API Contracts, Versioning, Compatibility & Interoperability

Autonomous buyers cannot stop mid-transaction to ask what a field means, whether an endpoint changed, or whether a new model version silently altered side effects. An agent business therefore needs a stronger contract than “the API returned valid JSON.” It needs a machine-readable agreement about **what can be called, what inputs mean, what outputs guarantee, what side effects may occur, what version governed the transaction, and how change is negotiated safely.**

This playbook is for founders exposing agent capabilities through APIs, tools, MCP servers, A2A-style interfaces, marketplaces, SDKs, internal agent platforms, or protocol gateways.

The core rule:

> **Protocol compliance is not semantic compatibility.** A request can validate against a schema and still break a buyer by changing meaning, quality, latency, price, permissions, side effects, retry behavior, or error recovery.

---

## 1. The compatibility lifecycle

Use this lifecycle for every externally callable capability:

```text
Specify -> Publish -> Negotiate -> Invoke -> Verify -> Observe -> Evolve -> Deprecate -> Retire
    ^                                                                            |
    +-------------------------------- learn --------------------------------------+
```

1. **Specify:** define machine-readable syntax plus human-readable semantic invariants.
2. **Publish:** expose a stable contract identifier and discovery metadata.
3. **Negotiate:** determine protocol, capability, schema, modality, and commercial compatibility before paid execution.
4. **Invoke:** execute against the exact negotiated contract.
5. **Verify:** validate output, side effects, idempotency, and outcome quality.
6. **Observe:** measure rejects, negotiation failures, legacy-version traffic, and semantic regressions.
7. **Evolve:** classify each proposed change as compatible or breaking before release.
8. **Deprecate:** publish migration guidance and a measurable sunset window.
9. **Retire:** remove old versions only after policy, telemetry, and customer commitments permit it.

A contract is an operating system for change, not a static documentation page.

---

## 2. Define four layers of compatibility

Do not collapse compatibility into a single “version” field.

### Layer 1: transport compatibility

Can the parties communicate at all?

Examples:

- HTTP vs stdio vs messaging transport,
- streaming vs request/response,
- authentication method,
- protocol revision,
- content encoding,
- compression,
- connection lifecycle.

### Layer 2: structural compatibility

Do request and response shapes validate?

Examples:

- required fields,
- JSON Schema types,
- enum values,
- cardinality,
- nested object shape,
- content type,
- input/output modalities.

### Layer 3: semantic compatibility

Does the same valid request still mean the same thing?

Examples:

- ranking criteria,
- default behavior,
- confidence interpretation,
- currency or timezone semantics,
- data-freshness expectations,
- whether a result is advisory or authoritative,
- whether an omitted field triggers a default action.

### Layer 4: operational/commercial compatibility

Can the buyer still safely use the capability under the same operating assumptions?

Examples:

- latency and timeout bounds,
- rate limits,
- concurrency limits,
- side effects,
- retry and idempotency semantics,
- required permissions,
- price and billable unit,
- entitlement requirements,
- data residency,
- SLA and support policy.

A release is backwards compatible only when the compatibility promise holds across every layer you committed to.

---

## 3. Publish a canonical capability contract

Each externally callable capability should have one canonical contract manifest that discovery systems, SDKs, marketplaces, billing, and incident tooling can reference.

Example:

```json
{
  "contract_id": "company-research@2.3.0",
  "capability": "company_research",
  "provider": "acme-agents",
  "status": "active",
  "protocols": [
    {"name": "https", "version": "2026-07"},
    {"name": "mcp", "version": "2026-07-28"}
  ],
  "input_schema": "sha256:2f0...",
  "output_schema": "sha256:8b1...",
  "semantic_spec": "sha256:52a...",
  "modalities": ["application/json", "text/markdown"],
  "side_effects": "none",
  "idempotency": {
    "supported": true,
    "key_header": "Idempotency-Key",
    "retention_hours": 48
  },
  "limits": {
    "timeout_seconds": 90,
    "max_concurrency": 20,
    "rate_limit_per_minute": 120
  },
  "commercial": {
    "pricing_version": "price_2026_08_15",
    "unit": "successful_report"
  },
  "deprecated_after": null,
  "sunset_after": null
}
```

At minimum, make these fields independently addressable:

- contract identifier,
- capability identifier,
- schema identifiers,
- semantic-spec identifier,
- protocol versions,
- supported modalities,
- side-effect class,
- idempotency behavior,
- error taxonomy,
- operational limits,
- pricing/entitlement references,
- lifecycle state,
- deprecation and sunset dates.

Do not make a mutable web page the only source of truth for a machine contract.

---

## 4. Version the capability, not just the endpoint

A URL such as `/v2/research` is useful but incomplete. The same endpoint may change schema, model behavior, defaults, pricing, and side effects over time.

Track at least:

```text
protocol version
capability version
schema version
semantic behavior version
pricing version
entitlement version
implementation release
```

These versions solve different problems.

A transaction receipt should be able to answer:

```text
Which protocol rules applied?
Which capability contract was negotiated?
Which schema validated the request and response?
Which semantic behavior policy applied?
Which pricing version rated the usage?
Which implementation produced the result?
```

This makes bugs, disputes, refunds, and migrations reproducible.

---

## 5. Use semantic versioning only where it actually fits

Semantic versioning is useful for capability contracts when you define what major, minor, and patch mean.

A practical policy:

- **MAJOR:** a previously valid consumer may need code, policy, pricing, or workflow changes.
- **MINOR:** additive behavior that does not invalidate existing compliant consumers.
- **PATCH:** fixes that preserve documented syntax, semantics, and operational behavior.

Do not label a release “patch” merely because the JSON shape did not change.

Examples of semantic major changes:

- changing the meaning of `confidence` from calibrated probability to heuristic score,
- changing default currency,
- adding a previously absent side effect,
- changing a successful retry from free to billable,
- increasing maximum execution time beyond a buyer’s budget policy,
- switching from deterministic ordering to relevance ordering,
- changing an entitlement requirement,
- making human approval optional where it was previously mandatory.

Schema compatibility is necessary, not sufficient.

---

## 6. Create a change-classification gate

Every contract-facing release should answer the same questions before deployment.

### Usually additive

- new optional response field,
- new optional request field with no changed default,
- new capability advertised separately,
- additional accepted content type,
- higher rate limit,
- new opt-in extension,
- new machine-actionable error metadata while retaining existing error semantics.

### Potentially breaking

- new required field,
- removal or rename,
- narrowed enum,
- changed default,
- changed ordering,
- new side effect,
- changed auth scope,
- changed retry behavior,
- changed idempotency window,
- changed price unit,
- stricter timeout,
- lower rate limit,
- changed output interpretation,
- changed privacy or residency guarantee.

### Always investigate semantically

- model replacement,
- prompt or policy change,
- ranking/retrieval change,
- data-source change,
- confidence calibration change,
- summarization depth change,
- tool-selection policy change,
- human-review change.

Make the classification decision a release artifact.

---

## 7. Negotiate before expensive or irreversible work

Autonomous systems should learn whether they can work together before execution consumes money or causes side effects.

A negotiation exchange should resolve:

1. protocol revision,
2. capability version,
3. input/output schema compatibility,
4. modality/content types,
5. authentication and authority,
6. required extensions,
7. pricing and entitlement compatibility,
8. latency/rate-limit requirements,
9. side-effect policy,
10. idempotency/retry support.

Conceptually:

```text
Buyer supports: protocol {P1,P2}, capability >=2.1 <3.0, JSON output, <=$0.20/call
Seller supports: protocol {P2,P3}, capability {2.2,2.3}, JSON+Markdown, $0.14/call

Negotiated: P2 + capability 2.3 + JSON + pricing v8
```

If no safe intersection exists, fail before billable execution.

---

## 8. Separate protocol version from capability version

Protocols evolve independently of the business capability.

A founder may support:

```text
Capability company_research@2.3
  over HTTPS contract 2026-07
  over MCP 2026-07-28
  over A2A-compatible interface 1.x
```

Do not require a capability major-version bump every time a transport protocol changes if the capability semantics remain stable.

Likewise, do not claim compatibility because two agents speak the same protocol. They may disagree on the capability schema, side effects, permissions, pricing, or semantics.

---

## 9. Treat discovery metadata as a compatibility surface

Discovery is the first contract negotiation.

A registry or agent card should point buyers to:

- exact capability identifiers,
- active contract versions,
- supported protocol versions,
- input/output modes,
- authentication requirements,
- geographic or residency constraints,
- pricing references,
- deprecation state,
- canonical contract URL or digest.

A stale registry entry can be as damaging as a stale SDK.

Track:

```text
discovery_version -> negotiated_contract_version -> executed_contract_version
```

Alert when these diverge unexpectedly.

---

## 10. Make schemas strict where ambiguity is dangerous

Schema design should reduce interpretation work for other agents.

Prefer:

- explicit units,
- explicit timezone,
- ISO dates,
- stable identifiers,
- bounded numeric ranges,
- documented nullability,
- enums where the set is actually controlled,
- discriminated unions for variant payloads,
- machine-readable validation constraints.

Avoid overloaded strings such as:

```json
{"budget": "a few hundred", "deadline": "soon"}
```

when autonomous execution depends on those values.

Prefer:

```json
{
  "budget": {"amount": 300, "currency": "USD", "type": "hard_cap"},
  "deadline": "2026-08-28T17:00:00Z"
}
```

Ambiguity is a hidden integration cost.

---

## 11. Define semantic invariants next to the schema

JSON Schema can prove shape; it cannot prove meaning.

For every important field, document invariants such as:

```text
confidence:
- range: 0..1
- interpretation: estimated probability the primary claim is correct
- calibration target: predictions in 0.8-0.9 should be correct 80-90% over the benchmark window
- not a substitute for source verification
```

For the capability itself, define invariants such as:

- output contains only evidence available at request time,
- no external side effects occur unless explicitly requested,
- all monetary values use the declared currency,
- retries with the same idempotency key cannot create duplicate transactions,
- omitted optional filters do not narrow results,
- citations refer to sources actually used in the result.

These invariants become semantic regression tests.

---

## 12. Design errors for autonomous recovery

A human-readable error string is not enough.

Use a stable taxonomy:

```json
{
  "error": {
    "code": "CAPABILITY_VERSION_UNSUPPORTED",
    "retryable": false,
    "message": "Requested capability version is unavailable",
    "supported_versions": ["2.2", "2.3"],
    "recovery": "renegotiate_version",
    "contract_id": "company-research@2.3.0",
    "request_id": "req_91"
  }
}
```

Useful dimensions:

- retryable vs terminal,
- client vs provider responsibility,
- authentication vs authorization,
- schema mismatch,
- capability/version mismatch,
- entitlement failure,
- budget exceeded,
- rate limited,
- transient dependency failure,
- partial execution,
- side effect unknown,
- output verification failed.

Every error class should tell an agent what it may safely do next.

---

## 13. Put retries and idempotency inside the contract

Agents retry aggressively. If retry semantics are undocumented, duplicate orders, charges, emails, reservations, and writes are inevitable.

Publish:

- which operations are safe to retry,
- required idempotency key format,
- key retention window,
- whether a retry returns the original result,
- whether partial failures can be resumed,
- how duplicate requests are reported,
- whether retries are billable,
- whether timeout means “not executed” or “execution status unknown.”

For side-effecting capabilities, prefer explicit state machines:

```text
accepted -> executing -> succeeded
                    \-> failed_safe_to_retry
                    \-> failed_side_effect_unknown
```

Never make an autonomous buyer infer side-effect safety from an HTTP status code alone.

---

## 14. Couple contract versions to pricing and entitlements

A capability version can change what is delivered, and that can change what should be billed.

Record:

```text
contract_id
pricing_version
entitlement_version
billable_unit
```

for every paid invocation.

Examples of dangerous drift:

- capability v3 doubles output depth but old pricing silently applies,
- a new premium data source is enabled without a new entitlement,
- an old buyer negotiates a deprecated capability but is rated against new units,
- a free retry becomes billable after an implementation change.

Commercial behavior is part of compatibility.

---

## 15. Maintain a compatibility matrix

For meaningful integrations, keep a machine-readable matrix such as:

| Component | Supported | Deprecated | Unsupported |
|---|---|---|---|
| Capability | 2.3, 2.2 | 2.1 | <=2.0 |
| MCP | 2026-07-28 | 2025-11-25 | older |
| Output | JSON, Markdown | — | binary |
| Auth | OAuth2, signed workload identity | API key | anonymous |
| Pricing | v8, v7 | v6 | <=v5 |

For each pair your customers actually use, run contract tests.

Do not maintain compatibility claims that you do not continuously verify.

---

## 16. Use producer and consumer contract tests

### Producer tests

The provider verifies that each release satisfies its published contract.

Test:

- schemas,
- error taxonomy,
- idempotency,
- side effects,
- rate limits,
- authentication requirements,
- response modality,
- declared semantic invariants.

### Consumer-driven tests

Important buyers publish the assumptions they rely on.

Examples:

- `status=accepted` always includes `delivery_id`,
- result ordering is stable,
- `retryable=true` never indicates an unknown side effect,
- response latency stays below a procurement SLA,
- `confidence` retains its calibration meaning.

Run these tests before a provider release.

This catches breakage that a generic schema test misses.

---

## 17. Add semantic regression evals

Agent capabilities frequently change behavior without changing schemas.

Maintain benchmark cases for:

- task success,
- output quality,
- refusal behavior,
- hallucination rate,
- tool-selection behavior,
- side-effect precision,
- latency,
- cost,
- source quality,
- calibration,
- policy adherence.

Compare candidate vs current production:

```text
schema compatible? yes
semantic success delta? -7.4%
side-effect false positive delta? +2.1%
median cost delta? +18%
```

That release is not “compatible” merely because validation passes.

---

## 18. Use safe rollout patterns

Prefer progressive exposure over flag-day upgrades.

Useful patterns:

### Shadow

Send production-shaped traffic to the new version without using its result.

Use for semantic and performance comparison.

### Canary

Route a small percentage of compatible traffic to the new version.

Use for operational validation.

### Version pinning

Allow high-value buyers to stay on a known version during migration.

Use when stability matters more than immediate adoption.

### Dual read

Read old and new representations and compare.

Use during schema or storage migrations.

### Dual write

Write both formats temporarily with reconciliation.

Use only when necessary; dual write adds failure modes.

### Compatibility gateway

Translate between old and new protocols or schemas at a controlled boundary.

Use to reduce migration burden, not to hide permanent fragmentation.

### Instant rollback

Keep the previous compatible release deployable until the new version clears observation windows.

---

## 19. Publish a deprecation policy before you need it

A credible API needs predictable retirement rules.

State:

- minimum support window,
- how breaking changes are announced,
- migration documentation expectations,
- whether security emergencies can accelerate retirement,
- whether enterprise contracts override defaults,
- how deprecated traffic is measured,
- what happens after sunset.

Example lifecycle:

```text
Active -> Deprecated -> Sunset announced -> Read-only/limited -> Removed
```

A deprecation announcement should include:

```text
version
replacement
breaking differences
migration steps
first deprecation date
sunset date
usage telemetry link
support contact
```

Do not retire based on calendar alone. Measure remaining live traffic and critical consumers.

---

## 20. Make compatibility observable

Track at least:

### Negotiation

- negotiation success rate,
- version mismatch rate,
- unsupported capability requests,
- modality mismatch,
- auth/authority mismatch,
- price/entitlement mismatch.

### Invocation

- schema reject rate,
- semantic verification failure rate,
- idempotency conflict rate,
- retry rate by contract version,
- error-code distribution,
- latency by version.

### Migration

- traffic by contract version,
- deprecated-version share,
- unique customers on deprecated versions,
- time-to-upgrade,
- compatibility-gateway volume,
- rollback frequency.

### Incidents

- incidents caused by contract drift,
- affected contract versions,
- transactions requiring refund or replay,
- time to detect,
- time to restore.

A compatibility incident should be traceable to exact contract and implementation versions.

---

## 21. Hash or sign contracts when tamper evidence matters

For regulated, high-value, or agent-to-agent transactions, preserve evidence of the exact contract that governed execution.

Useful techniques:

- content-addressed schema hashes,
- immutable contract manifests,
- signed manifests,
- contract digest in transaction receipts,
- timestamped registry snapshots,
- provenance links from discovery record to invocation.

A receipt might contain:

```json
{
  "request_id": "req_91",
  "contract_id": "company-research@2.3.0",
  "contract_digest": "sha256:4ef...",
  "pricing_version": "price_v8",
  "implementation": "release_2026_08_27_1"
}
```

This is useful when two parties later disagree about what the capability promised.

---

## 22. Compatibility rules for marketplaces

A marketplace should not force buyers to discover incompatibility after purchase.

Require providers to publish:

- contract identifier,
- capability/version range,
- protocol versions,
- auth methods,
- modalities,
- geographic constraints,
- price unit,
- side-effect class,
- deprecation state,
- contract-test status.

The marketplace can then match on compatibility before ranking on price or reputation.

A useful marketplace funnel is:

```text
Discovered -> Compatible -> Authorized -> Affordable -> Selected -> Invoked -> Verified -> Reused
```

Measure drop-off at every stage.

---

## 23. Compatibility rules for multi-agent workflows

In a multi-agent graph, local compatibility is not enough. A schema or semantic change can propagate downstream.

For each edge:

```text
producer contract -> transformation -> consumer assumption
```

Track dependencies so you can answer:

- which workflows consume capability v2.1,
- which downstream agents rely on a field being present,
- which contracts would break if an enum narrows,
- which billing policy applies after a gateway translation,
- which workflows must be replayed after a faulty release.

Treat the agent graph as a dependency graph with contracts on every edge.

---

## 24. Minimum viable interoperability stack

A startup does not need a standards department.

Start with:

1. one canonical capability manifest,
2. JSON Schema for request and response,
3. semantic invariants for important behavior,
4. stable machine-readable error codes,
5. idempotency rules,
6. protocol/capability version fields,
7. a compatibility test suite,
8. a deprecation policy,
9. invocation receipts with contract version,
10. dashboards for deprecated traffic and negotiation failures.

Add gateways, registries, signed manifests, and broad protocol support only when real integrations require them.

---

## 25. Interoperability anti-patterns

Avoid these patterns:

### “The model handles it”

Natural-language adaptability does not replace deterministic contracts for money, permissions, state changes, or auditability.

### Silent default changes

Changing default behavior is often a semantic breaking change even when schemas remain identical.

### One global version number

Protocol, capability, schema, pricing, and implementation releases evolve independently.

### Eternal backwards compatibility

Supporting everything forever creates security, test, and operational debt. Deprecate deliberately.

### Version detection by trial and error

Negotiate or discover before paid execution when possible.

### Error strings as APIs

Agents should not parse prose to decide whether retrying is safe.

### Gateway without provenance

If a gateway translates versions, preserve both original and translated contract identities.

### Unmeasured deprecation

Do not sunset a version without knowing who still uses it.

---

## 26. A compatibility release checklist

Before changing an externally consumed capability:

- [ ] Identify every affected contract layer: transport, structure, semantics, operations/commercials.
- [ ] Classify the change as additive, compatible-with-conditions, or breaking.
- [ ] Update capability, schema, semantic, pricing, or entitlement versions as appropriate.
- [ ] Run producer contract tests.
- [ ] Run important consumer-driven contract tests.
- [ ] Run semantic regression evals.
- [ ] Verify idempotency and retry behavior.
- [ ] Verify machine-actionable error recovery.
- [ ] Test protocol/capability negotiation paths.
- [ ] Verify discovery metadata points to the correct version.
- [ ] Compare latency, cost, quality, and side effects against production.
- [ ] Define rollout and rollback plans.
- [ ] Publish migration guidance for breaking changes.
- [ ] Define deprecation/sunset dates only within policy.
- [ ] Add observability for new and deprecated versions.
- [ ] Ensure transaction receipts retain the governing contract identity.

---

## 27. Business opportunities

Compatibility itself becomes a product as the agent ecosystem fragments across providers, protocol versions, schemas, and semantic assumptions.

Potential businesses:

### Agent contract registry

Host immutable, discoverable capability manifests and schema histories.

Revenue:

- hosted registry plans,
- private enterprise registries,
- compliance retention,
- signed attestations.

### Compatibility testing service

Continuously test agents, tools, and MCP/A2A-style interfaces against consumer contracts and semantic evals.

Revenue:

- per integration,
- CI subscription,
- enterprise compatibility matrix,
- certification.

### Protocol gateway

Translate between protocol eras, transport styles, or capability schemas while preserving provenance.

Revenue:

- usage fee,
- managed gateway subscription,
- enterprise deployment.

### Interoperability certification

Verify schema behavior, retry safety, error semantics, and declared operational guarantees.

Revenue:

- certification fee,
- recurring surveillance testing,
- marketplace trust signal.

### Migration automation

Discover deprecated consumers, generate adapters, run shadow tests, and track migration progress.

Revenue:

- per migrated integration,
- enterprise platform,
- agent fleet management.

### Semantic contract monitoring

Detect behavioral drift even when schemas do not change.

Revenue:

- eval subscription,
- per-capability monitoring,
- incident-response add-on.

The strongest infrastructure businesses reduce the cost of change without pretending change can be eliminated.

---

## 28. Founder scorecard

Review monthly:

| Metric | Question |
|---|---|
| negotiation success | Can compatible agents agree before invocation? |
| schema reject rate | Are contracts structurally usable? |
| semantic regression rate | Did behavior drift without a schema break? |
| deprecated traffic share | Are migrations progressing? |
| compatibility incidents | How often does change break consumers? |
| rollback rate | Are releases safe? |
| version sprawl | How many live versions must be supported? |
| contract-test coverage | Are important buyer assumptions continuously verified? |
| receipt reproducibility | Can a transaction be tied to its exact governing contract? |
| migration time | How long do important consumers take to upgrade? |

The objective is not zero versions. It is **controlled evolution with predictable buyer impact**.

---

## 29. Operating principle

The agent economy will contain many protocols, vendors, schemas, models, and execution environments. Winners will not be the businesses that freeze their interfaces forever. They will be the businesses that can evolve quickly **without surprising autonomous customers**.

Design every capability so another agent can answer, before spending money or taking action:

```text
Can I speak to it?
Can I understand it?
Am I authorized to use it?
Can I afford it?
What exactly will it do?
What happens if I retry?
Which contract governs this invocation?
How will I know if that contract changes?
```

If those questions are machine-answerable, interoperability becomes an operational capability rather than a hope.