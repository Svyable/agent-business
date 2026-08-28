# Agent Discovery Production Deployment

This guide describes how to promote the reference discovery runtime into a real, observable Agent Business service **without weakening its privacy or durability claims**.

The deployment rule is:

> A production endpoint is not ready merely because the function is reachable. It is ready only when session signing is persistent and the telemetry sink proves that accepted events are durably stored.

Issue #69 remains the production milestone. This document and `service/deployment.py` make that milestone deployable without creating cloud resources or committing secrets.

## Architecture

```text
agent / crawler / human
        |
        v
Agent Business discovery runtime
  - llms.txt
  - agent-index.json
  - /v1/agent/hello
  - /v1/events
        |
        | HTTPS + bearer credential
        v
durable event ingestion service
  - /health -> durability attestation
  - /events -> per-event persistence acknowledgement
        |
        v
append-only durable storage
        |
        v
cohorts / activation / revenue analytics
```

The discovery runtime and event store are deliberately separated. This keeps database credentials and storage-vendor logic out of the public founder OS.

## Vercel entrypoint

The repository includes:

```toml
[tool.vercel]
entrypoint = "service.deployment:application"
```

Current Vercel Python deployments support a custom Python entrypoint through `[tool.vercel] entrypoint`. The exported `application` is the deployment wrapper around the WSGI reference runtime.

Do not add Flask or FastAPI solely to satisfy deployment routing unless a future product requirement justifies the dependency.

## Required production environment

Set these server-side variables in the deployment platform. Never commit their values.

```text
AGENT_BUSINESS_ENV=production
AGENT_BUSINESS_SESSION_SECRET=<random secret, at least 16 bytes>
AGENT_BUSINESS_RELEASE_ID=<immutable deploy/commit identifier>
AGENT_BUSINESS_EVENT_SINK_URL=https://<sink>/v1/events
AGENT_BUSINESS_EVENT_SINK_HEALTH_URL=https://<sink>/health
AGENT_BUSINESS_EVENT_SINK_TOKEN=<server-only bearer credential>
```

Optional bounds:

```text
AGENT_BUSINESS_EVENT_SINK_TIMEOUT_SECONDS=2
AGENT_BUSINESS_EVENT_SINK_MAX_RESPONSE_BYTES=8192
AGENT_BUSINESS_EVENT_SINK_HEALTH_CACHE_SECONDS=10
AGENT_BUSINESS_MAX_BODY_BYTES=65536
AGENT_BUSINESS_WRITE_RATE_LIMIT_PER_MINUTE=60
```

### Secret rules

- `AGENT_BUSINESS_SESSION_SECRET` must survive function restarts and deployments where return-session continuity is expected.
- `AGENT_BUSINESS_EVENT_SINK_TOKEN` is server-only and must never appear in browser-visible environment variables.
- Rotate the sink token independently from the session secret.
- A session-secret rotation intentionally invalidates previously issued pseudonymous session IDs unless the deployment adds a bounded multi-key verification window.
- Never print either secret in application logs, CI output, issue comments, or telemetry.

## Durable sink health contract

The configured health URL must return a 2xx JSON object:

```json
{
  "status": "ready",
  "durable": true
}
```

Anything else means **not durable**:

- timeout,
- DNS/network failure,
- non-2xx response,
- invalid JSON,
- `status != "ready"`,
- or `durable != true`.

The adapter caches a successful/failed health result only for the bounded configured cache interval, at most 60 seconds.

This health contract should mean the sink can currently acknowledge events only after they have reached the durability boundary documented by the sink operator.

## Event persistence contract

For each POSTed discovery event, the sink must return a 2xx JSON object:

```json
{
  "persisted": true,
  "event_id": "evt_exact_submitted_id"
}
```

A generic HTTP `200` or `202` is insufficient.

The runtime rejects the acknowledgement when:

- `persisted` is not exactly `true`,
- the acknowledgement event ID does not equal the submitted event ID,
- the response is malformed,
- the response exceeds the configured size bound,
- or the request fails.

When persistence fails after readiness, the deployment wrapper returns:

```http
503 Service Unavailable
Retry-After: 30
```

with:

```json
{"error":"telemetry_unavailable"}
```

This is preferable to returning a successful hello or activation response whose evidence was silently lost.

## Authentication contract

The runtime sends:

```text
Authorization: Bearer <AGENT_BUSINESS_EVENT_SINK_TOKEN>
```

The sink should:

1. authenticate this credential before parsing business fields,
2. apply a narrow ingest-only permission,
3. reject expired/revoked credentials,
4. rate-limit independently from the discovery runtime,
5. never echo the credential,
6. bind the credential to this ingestion audience where supported.

The sink token is not agent authority and must not be reusable for any customer-facing action.

## Storage semantics

A sink may set `durable: true` only when its acknowledgement means the event has crossed a documented persistence boundary.

Acceptable examples:

- committed append-only database row,
- acknowledged durable queue/stream write,
- object/event store write with documented durability,
- analytics ingestion API whose acknowledgement contract guarantees persistence.

Not sufficient:

- process memory,
- function-local filesystem,
- stdout/stderr alone,
- an in-memory queue,
- a best-effort asynchronous request whose downstream write has not been acknowledged.

## Event-store schema minimum

The durable system should retain at least:

```text
event_id            unique / idempotency key
schema_version
event_type
occurred_at
received_at
session_id          nullable pseudonymous value
actor_confidence
source_channel
resource_id         nullable
resource_path       nullable
stage               nullable
intent              nullable
commercial fields   only when present and non-sensitive
full sanitized event JSON
```

Recommended database constraints:

- unique `event_id`,
- immutable raw event body after insertion,
- server-generated `received_at`,
- constrained actor/source/event enums where practical,
- no raw IP column,
- no raw User-Agent column,
- no prompt or secret columns.

Treat ingestion retries as idempotent by `event_id`.

## Privacy boundary

The external event sink receives the same sanitized event contract enforced by the runtime.

It must not enrich the product-analytics record with:

- raw IP addresses,
- full User-Agent strings,
- prompt content,
- emails,
- customer secrets,
- bearer/API credentials,
- payment credentials,
- private founder evidence.

If infrastructure/security logs retain request addresses for abuse response, keep those logs logically separate, access-controlled, and on a short documented retention schedule.

## Readiness semantics

`GET /healthz` in production returns `200` only when:

1. `AGENT_BUSINESS_SESSION_SECRET` is configured, and
2. the injected event sink's live health contract attests `status=ready` and `durable=true`.

Otherwise it returns `503`.

A deployment platform should use `/healthz` for post-deploy verification, not merely check that the function process started.

## Preview before production

Use a staged rollout:

1. create a dedicated Agent Business hosting project intentionally,
2. configure preview-only secrets and a preview event sink,
3. deploy the exact commit to preview,
4. run the smoke journey below,
5. inspect runtime errors and sink persistence,
6. verify no secrets or raw identifiers appear in logs,
7. promote the already-tested artifact to production,
8. repeat smoke checks against the production alias,
9. monitor error rate and ingestion acknowledgement failures.

Do not point preview traffic at the production telemetry table unless the sink explicitly tags and isolates environments.

## Production smoke journey

After deployment:

```bash
BASE=https://<agent-business-host>

curl -fsS "$BASE/healthz"
curl -fsS "$BASE/llms.txt" >/dev/null
curl -fsS "$BASE/agent-index.json" >/dev/null

HELLO=$(curl -fsS -X POST "$BASE/v1/agent/hello" \
  -H 'content-type: application/json' \
  -d @templates/AGENT_HELLO.json)

printf '%s\n' "$HELLO"
```

Verify:

- health says `production_ready: true`,
- hello says `self_declared_agent`, not `verified_agent`,
- a pseudonymous session is returned only when requested,
- the durable store contains exactly one corresponding `agent_hello` event,
- the stored event contains no raw IP/User-Agent/prompt/secret values.

Then send one synthetic `stage_selected` or `founder_packet_started` event using the issued session and verify the exact event ID in storage.

## Rollback

Rollback triggers include:

- health endpoint becomes 503,
- persistence acknowledgements fail,
- malformed-event rejection materially regresses,
- raw sensitive fields appear in analytics,
- session validation breaks unexpectedly,
- activation rate drops immediately after a contract change.

Rollback the application artifact independently from the durable event store. Do not delete event evidence during application rollback.

## What remains for Issue #69

The repository is deployment-ready after this adapter, but #69 remains open until all of these exist in a real controlled environment:

- a dedicated Agent Business hosting project,
- a dedicated or explicitly approved durable event store,
- deployment secrets configured outside Git,
- preview smoke-test evidence,
- production smoke-test evidence,
- 7-day/30-day cohort aggregation,
- dashboarding and alerting,
- token/session-secret rotation procedure,
- production rollback evidence.

Until then, the correct status is:

> **deployable and testable, not yet live agent telemetry.**
