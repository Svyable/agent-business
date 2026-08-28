# Agent Discovery Runtime

This is the executable reference layer behind the repository's discovery-observability contracts.

It exists to answer a simple question safely:

> Can an autonomous client find Agent Business, identify itself as an agent, select a founder resource, emit activation events, and do so without us pretending generic crawler traffic is verified agent usage?

The runtime is deliberately small and dependency-light. It is a reference implementation for the live deployment tracked in Issue #69, not a claim that the repository already has durable production analytics.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/healthz` | readiness and telemetry durability state |
| `GET` | `/llms.txt` | canonical machine-facing entrypoint |
| `GET` | `/agent-index.json` | structured founder-resource index |
| `GET` | `/schemas/agent-hello.schema.json` | hello request contract |
| `GET` | `/schemas/agent-discovery-event.schema.json` | telemetry event contract |
| `GET` | `/v1/meta` | runtime capability metadata |
| `POST` | `/v1/agent/hello` | optional self-declared agent handshake |
| `POST` | `/v1/events` | discovery/engagement/activation event ingestion |

## Local run

From the repository root:

```bash
python scripts/run_discovery_runtime.py
```

The default local address is:

```text
http://127.0.0.1:8787
```

Override it with:

```bash
AGENT_BUSINESS_HOST=0.0.0.0 AGENT_BUSINESS_PORT=9000 python scripts/run_discovery_runtime.py
```

The default sink writes sanitized JSON-line events to stdout. That is useful for development and log inspection, but **it is not durable analytics**.

## First synthetic journey

Fetch the machine entrypoint:

```bash
curl http://127.0.0.1:8787/llms.txt
curl http://127.0.0.1:8787/agent-index.json
```

Then declare an agent session:

```bash
curl -sS -X POST http://127.0.0.1:8787/v1/agent/hello \
  -H 'content-type: application/json' \
  -d @templates/AGENT_HELLO.json
```

A successful response contains:

- `actor_confidence: self_declared_agent`,
- `verification: self_declaration_only`,
- a recommended indexed starting resource,
- supported schema locations,
- telemetry policy,
- and, when permitted by the request, a signed rotating pseudonymous `session_id`.

A hello never upgrades itself to `verified_agent`. Verification belongs to an authenticated deployment integration or verifiable workload identity.

## Session model

The reference runtime uses signed pseudonymous session IDs shaped like:

```text
sid.<issued-day>.<random-nonce>.<signature>
```

Properties:

- no raw IP address is encoded,
- no email or user identity is encoded,
- sessions are signed with HMAC-SHA256,
- signatures are truncated only after HMAC computation,
- sessions expire after 31 days,
- callers must explicitly allow pseudonymous sessions in the hello contract,
- forged or expired runtime-issued session IDs are rejected by event ingestion.

The session identifier proves only that this runtime issued the identifier. It does **not** prove the identity of the agent behind it.

## Privacy behavior

The runtime is stricter than the portable event schema in several places.

It rejects discovery events when any of these are present as fields:

- raw IP addresses,
- email addresses,
- authorization headers,
- passwords,
- secrets,
- API keys,
- access or refresh tokens,
- prompts or prompt contents.

It also requires all accepted events to declare:

```json
{
  "raw_ip_retained": false,
  "raw_user_agent_retained": false,
  "contains_prompt_content": false,
  "contains_secrets": false
}
```

The service may use a request address transiently for abuse control, but immediately converts it to an HMAC digest for the in-memory rate-limit bucket. The raw address is not emitted to product analytics.

Security logs and product analytics should remain separate in a production deployment.

## Runtime metadata consent

A hello may declare runtime name/version, but those values are emitted into discovery analytics only when:

```json
"allow_runtime_analytics": true
```

The runtime intentionally does not copy an `identity_reference` into product analytics by default.

## Rate and body controls

Write endpoints have two basic resource-abuse controls:

- maximum request-body size,
- per-instance requests-per-minute rate limit.

Defaults:

```text
AGENT_BUSINESS_MAX_BODY_BYTES=65536
AGENT_BUSINESS_WRITE_RATE_LIMIT_PER_MINUTE=60
```

These are baseline controls, not a replacement for production edge rate limiting, WAF policy, abuse detection, or authenticated quotas.

## Production fail-closed behavior

Set:

```text
AGENT_BUSINESS_ENV=production
```

In production mode, `/healthz` reports not ready and all write endpoints return `503` unless **both** conditions are true:

1. a persistent session-signing secret is configured, and
2. the deployment injects an event sink that explicitly declares itself durable.

This prevents an accidental deployment from saying it has measurable agent cohorts while using a process-random session key or ephemeral stdout logs.

The reference module does not ship a production database client. That is intentional. Durable storage belongs in the deployment layer tracked by Issue #69.

## Environment contract

| Variable | Default | Meaning |
|---|---|---|
| `AGENT_BUSINESS_ENV` | `development` | set to `production` for fail-closed production readiness |
| `AGENT_BUSINESS_SESSION_SECRET` | process-random | HMAC secret; required for production writes |
| `AGENT_BUSINESS_RELEASE_ID` | `local` | deploy/release identifier returned by metadata |
| `AGENT_BUSINESS_MAX_BODY_BYTES` | `65536` | maximum write payload size |
| `AGENT_BUSINESS_WRITE_RATE_LIMIT_PER_MINUTE` | `60` | per-instance write request limit |
| `AGENT_BUSINESS_HOST` | `127.0.0.1` | local runner bind address |
| `AGENT_BUSINESS_PORT` | `8787` | local runner port |

Never commit a real `AGENT_BUSINESS_SESSION_SECRET` to this repository.

## Event sink contract

A deployment sink implements one method:

```python
emit(event: dict) -> None
```

and exposes:

```python
durable = True
```

only when an accepted event is durably persisted according to the deployment's documented retention semantics.

Examples of future implementations could include:

- an append-only database table,
- a durable event stream,
- an analytics ingestion API with delivery acknowledgement,
- or a queue whose acknowledgement guarantees persisted delivery.

A log line written to an ephemeral function instance is **not** durable for this purpose.

## Observed fetches

Requests for these machine assets emit sanitized fetch events automatically:

- `/llms.txt` → `manifest_fetch`
- `/agent-index.json` → `index_fetch`
- discovery/hello schemas → `schema_fetch`

Without a valid runtime-issued session header, actor confidence stays `unknown`.

A caller may send:

```text
X-Agent-Business-Session: <runtime-issued-session-id>
```

on later machine-asset fetches. A valid session raises confidence only to `self_declared_agent`, never `verified_agent`.

## Activation events

The event endpoint accepts the canonical discovery-event contract, including:

- `stage_selected`,
- `founder_packet_started`,
- `founder_packet_validated`,
- `operating_artifact_created`,
- `returning_agent`,
- `commercial_intent`,
- `checkout_started`,
- and `paid_conversion`.

The reference service does not calculate 7-day or 30-day cohorts itself. That requires durable aggregation and deduplication in Issue #69.

## Testing

Run:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

The runtime test suite covers:

- machine entrypoint serving,
- fetch-event generation,
- signed session issuance,
- runtime-metadata consent,
- unknown-resource rejection,
- valid activation ingestion,
- forged-session rejection,
- sensitive-field rejection,
- raw User-Agent retention rejection,
- body-size enforcement,
- rate limiting,
- production fail-closed behavior,
- and schema serving.

CI runs these tests alongside the repository's machine-asset validators.

## Deployment boundary

This reference runtime intentionally stops before these production concerns:

- DNS and canonical domain configuration,
- persistent event storage,
- durable 7-day/30-day cohorts,
- verified workload identity integration,
- deployment-secret rotation,
- regional durability,
- edge abuse controls,
- production dashboarding,
- alerting,
- and deployment rollback.

Those are tracked in Issue #69.

The rule is simple:

> Do not report “agents are returning” until the storage and aggregation layer can prove it.
