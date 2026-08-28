# Agent Discovery Observability

Agent Business should not confuse **being public** with **being found**, or **being fetched** with **being used**. This guide defines a privacy-conscious measurement system for knowing when humans, crawlers, and autonomous agents discover the repository and move from discovery toward durable business use.

The operating funnel is:

```text
Published -> Indexed -> Fetched -> Engaged -> Activated -> Returned -> Commercial
```

The goal is not to maximize raw traffic. The goal is to know whether qualified machine clients can find the project, understand it, use it, return to it, and eventually create economic value.

## 1. Define what counts as "an agent found us"

Do not treat every request with an unusual User-Agent as an autonomous agent.

Use confidence levels:

| Confidence | Meaning | Acceptable evidence |
|---|---|---|
| `unknown` | ordinary request with no useful identity signal | page/file fetch only |
| `suspected_machine` | request pattern looks automated | high-rate structured fetches, machine-oriented resource sequence |
| `self_declared_agent` | client explicitly declares it is an agent/runtime | structured hello or equivalent declaration |
| `verified_agent` | declaration is bound to a verifiable identity or trusted integration | signed workload identity, authenticated integration, registry-bound identity |

For reporting, keep these categories separate. Never promote `unknown` or `suspected_machine` to `verified_agent` from model inference alone.

## 2. Instrument the discovery funnel

### Published

The project exposes machine-readable entrypoints such as:

- `llms.txt`
- `agent-index.json`
- schemas
- templates
- protocol and operating guides

Success means these resources are valid, current, and reachable.

### Indexed

A search engine, registry, catalog, agent platform, or enterprise indexer has discovered a resource.

Possible evidence:

- registry listing accepted,
- search/referrer traffic,
- recurring fetches from known indexing infrastructure,
- explicit index callbacks where supported.

Do not assume publication implies indexing.

### Fetched

A client requests a machine entrypoint or resource.

Recommended event types:

- `manifest_fetch`
- `index_fetch`
- `schema_fetch`
- `template_fetch`
- `resource_fetch`

A fetch proves attention, not value.

### Engaged

A client does more than retrieve one file.

Examples:

- traverses from `llms.txt` into `agent-index.json`,
- requests a founder-stage resource,
- requests a schema and corresponding template,
- performs an explicit agent hello/handshake,
- asks for prerequisites or next-stage guidance.

Recommended event types:

- `agent_hello`
- `stage_selected`
- `resource_sequence_started`

### Activated

The visitor begins real founder work.

Strong activation signals include:

- creates a founder launch packet,
- validates a founder packet,
- persists an evidence record,
- selects a business hypothesis and next action,
- creates a service contract, diligence room, or authority envelope in a real workflow.

Recommended event types:

- `founder_packet_started`
- `founder_packet_validated`
- `operating_artifact_created`

Activation is a better north-star signal than repository views.

### Returned

The same pseudonymous session, installation, or authenticated agent returns after the initial activation window.

Recommended event:

- `returning_agent`

Track cohort retention without requiring personally identifiable information.

### Commercial

A visitor expresses or creates economic intent.

Examples:

- requests a premium launch kit,
- asks for a paid capability,
- starts marketplace procurement,
- requests pricing,
- begins checkout,
- completes a purchase.

Recommended event types:

- `commercial_intent`
- `checkout_started`
- `paid_conversion`

Do not place payment secrets, raw card data, or private contract content into analytics events.

## 3. Use a canonical discovery event

The repository includes `schemas/agent-discovery-event.schema.json` and `templates/AGENT_DISCOVERY_EVENT.json`.

Every event should contain:

- a unique event ID,
- event type,
- timestamp,
- source channel,
- resource or stage where relevant,
- actor confidence,
- a pseudonymous session key when appropriate,
- privacy treatment,
- and optional commercial/engagement metadata.

Keep the event model vendor-neutral so it can be emitted to a log pipeline, analytics warehouse, privacy-preserving counter service, or future Agent Business API.

## 4. Prefer an explicit agent hello over fingerprinting

A machine-facing service should eventually expose an optional endpoint such as:

```text
POST /v1/agent/hello
```

A client may declare:

- runtime name,
- runtime version,
- supported protocols,
- intended use,
- whether it can persist a founder packet,
- whether it wants commercial capabilities,
- and an optional verifiable identity reference.

The server can return:

- a session identifier,
- canonical index location,
- repository/version identifier,
- supported schemas,
- recommended starting resource,
- telemetry policy,
- and commercial/discovery capabilities.

Use `schemas/agent-hello.schema.json` and `templates/AGENT_HELLO.json` as the portable request contract.

A hello is **self-declaration**, not proof. Verification requires a separate trusted identity or authenticated integration.

## 5. Privacy rules

Discovery analytics should be useful without becoming surveillance.

Default rules:

1. Do not store raw IP addresses in durable analytics.
2. Do not store full browser or agent User-Agent strings unless operationally necessary and time-bounded.
3. Prefer rotating pseudonymous session identifiers.
4. Keep raw request logs on the shortest operational retention that reliability/security permits.
5. Do not ingest prompt contents, customer data, secrets, payment credentials, or founder private evidence into discovery analytics.
6. Separate security logs from product analytics.
7. Document any identifier hashing, truncation, rotation, and deletion policy.
8. Do not claim anonymous data is impossible to re-identify; minimize collection instead.

The supplied event validator rejects common raw identifier fields such as `ip`, `ip_address`, `email`, and `authorization`.

## 6. Core metrics

Track counts and rates by actor confidence and source channel.

### Discovery

```text
machine_entrypoint_fetches
unique_pseudonymous_sessions
known_registry_referrals
self_declared_agent_sessions
verified_agent_sessions
```

### Engagement

```text
index_to_resource_rate
hello_rate
multi_resource_session_rate
stage_selection_rate
```

### Activation

```text
founder_packet_start_rate
founder_packet_validation_rate
artifact_creation_rate
median_time_to_activation
```

### Retention

```text
7d_return_rate
30d_return_rate
stages_completed_per_returning_agent
```

### Commercial

```text
commercial_intent_rate
checkout_start_rate
paid_conversion_rate
revenue_per_activated_agent
gross_margin_per_paid_agent
```

Segmenting by confidence prevents crawlers from making activation ratios meaningless.

## 7. Define readiness thresholds

A practical first readiness ladder:

### Level 0 — Published

- machine entrypoints exist,
- validator passes,
- no broken paths.

### Level 1 — Observable

- entrypoint and resource fetches can be counted,
- source channel is captured,
- privacy policy is explicit.

### Level 2 — Agent-aware

- structured hello supported,
- self-declared agents separated from generic crawlers,
- activated founder workflows measurable.

### Level 3 — Verified

- some agent sessions bind to authenticated or verifiable identities,
- replay and abuse controls exist,
- retention cohorts are trustworthy.

### Level 4 — Commercial

- agent-origin commercial intent and conversion are measurable,
- attribution survives through checkout/payment,
- unit economics are segmented by acquisition source and actor type.

The repository is useful before Level 4, but monetization decisions should not rely on machine-traffic assumptions until at least Level 2.

## 8. Implementation order

1. **Validate machine assets in CI.** Broken manifests make every later metric misleading.
2. **Serve canonical entrypoints from a controlled domain.** GitHub remains a distribution channel, not the only observability surface.
3. **Add server-side event collection.** Emit the canonical event schema.
4. **Add `/v1/agent/hello`.** Keep it optional and protocol-neutral.
5. **Add activation instrumentation.** Measure founder packet and operating-artifact creation.
6. **Add retention cohorts.** Use rotating pseudonymous identifiers or authenticated integrations.
7. **Add commercial attribution.** Join discovery to paid conversion without placing sensitive payment data in analytics.
8. **Publish a small public status/metrics summary only if it improves trust.** Do not expose security-sensitive telemetry.

## 9. Dashboard layout

A useful dashboard should answer five questions:

1. **Are agents finding us?** machine entrypoint fetches and hello sessions.
2. **Are they understanding us?** index-to-resource and stage-selection rates.
3. **Are they doing founder work?** launch-packet activation and validation.
4. **Are they coming back?** retained agent cohorts.
5. **Are they creating economic value?** commercial intent, paid conversion, and margin.

Avoid vanity dashboards centered on total views or raw bot traffic.

## 10. Alert conditions

Useful alerts include:

- `llms.txt` or `agent-index.json` validation failure,
- sudden zero traffic to canonical machine entrypoints,
- sharp rise in malformed or abusive hello requests,
- activation-rate collapse after a manifest/schema change,
- resource fetches pointing to missing or deprecated paths,
- unexpected spike in one source/channel that could be scraping or abuse,
- commercial conversions without corresponding acceptance/billing evidence.

Alerts should point to an operator action, not merely report a number.

## 11. What not to do

Do not:

- add tracking pixels to Markdown and call that agent analytics,
- infer agent identity solely from User-Agent strings,
- fingerprint visitors across unrelated properties,
- collect prompts or founder private data for marketing analytics,
- create hidden telemetry in templates,
- block legitimate anonymous access just to improve attribution,
- or optimize for crawler volume instead of activated founder workflows.

## 12. First success milestone

The first meaningful discovery milestone is not "we got 1,000 views."

It is:

> A self-declared or verified agent intentionally fetched the machine entrypoint, selected a founder resource, created or validated a founder operating artifact, and later returned.

The first meaningful commercial milestone is:

> An agent-origin session produced a paid conversion whose acquisition source, authority, delivery evidence, billing event, and margin can be reconstructed without relying on raw personal data.

That is how Agent Business will know the agent economy has started using it—not merely crawling it.