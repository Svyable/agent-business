# Agent Third-Party Platform Access, Delegated Authorization, and Terms Compliance

Autonomous agents increasingly browse, sign in to, read from, write to, message through, and transact with systems they do not control. A customer instruction can authorize the agent **as between the customer and the agent business** while still leaving a separate question: whether the target platform, account owner, counterparty, API, or integration authorizes the selected access method and action.

This playbook keeps those facts separate and gives agent founders a practical stop/go contract for third-party automation.

## Core rule

Do not infer target-platform permission from user delegation, public availability, technical reachability, possession of a session, or model confidence.

A production interaction should be reconstructable as:

`business purpose -> principal delegation -> platform authorization basis -> approved access method -> bounded action -> current policy evidence -> observed platform response -> audit record`

If a required link is unknown, stale, revoked, blocked, or contradicted by the platform, fail closed and escalate.

## Lifecycle

`proposed -> platform_review -> authorized_method_selected -> configured -> tested -> active -> restricted / suspended -> retired`

- **proposed** — business purpose and target platform identified; no access authority implied.
- **platform_review** — principal delegation, platform authorization basis, access method, terms/policies, identity requirements, and data/actions are being reviewed.
- **authorized_method_selected** — an evidence-backed access path and action matrix have been selected.
- **configured** — credentials/session references and runtime controls are configured outside public records.
- **tested** — representative safe tests passed within the approved method and action matrix.
- **active** — current platform evidence supports the access path and runtime signals show no unresolved revocation/blocking condition.
- **restricted** — a bounded subset of actions remains permitted while other actions are disabled.
- **suspended** — automation must stop until authorization or policy uncertainty is resolved.
- **retired** — the integration is intentionally decommissioned and credentials/session material are revoked through the private operating environment.

Status is descriptive. It does not grant transaction, spend, destructive-action, or unrelated account authority.

## Two independent authorization questions

### 1. Principal/user delegation

Record why the user, customer, employer, or other principal may ask the agent to act. Useful evidence can include an OAuth grant, customer configuration, signed scope, tenant policy, contract reference, or explicit workflow approval.

This bounds what the agent may do **for the principal**.

### 2. Platform/counterparty authorization

Separately record why the target system permits the agent business to use the chosen method. Examples can include:

- official API documentation and granted scopes;
- approved partner or marketplace integration;
- OAuth application registration and consent;
- written platform approval;
- documented browser-automation policy;
- customer-controlled browser use where platform rules permit it;
- published crawling/automation policy relevant to the exact activity.

This bounds what the agent may do **to or through the platform**.

Neither record should silently substitute for the other.

## Access-method classification

Classify every integration as one of:

- `official_api`
- `partner_integration`
- `oauth_delegated_app`
- `browser_automation`
- `user_controlled_browser`
- `scraping_or_crawling`
- `email_or_messaging_interface`
- `mcp_or_tool_endpoint`
- `other`

Prefer the narrowest supported official method that satisfies the workflow. Record why a less-direct method is necessary when an official API exists but is not used.

## Terms and policy provenance

Do not encode remembered policy summaries as authority. Store a reference with:

- policy/terms name;
- version, publication date, or retrieval date when available;
- canonical URL or private evidence reference;
- clauses or categories relevant to automation, identity, rate limits, data use, messaging, purchases, or account actions;
- next review/change-detection date.

A robots/crawler file can be one machine-readable policy signal for crawling behavior. It is not a universal conclusion about contractual, statutory, privacy, authentication, messaging, or transaction authorization.

## Identity and disclosure

Record whether the platform expects:

- a registered app/client identity;
- agent or automation disclosure;
- a truthful user-agent string;
- a service account;
- an end-user identity plus delegated application identity;
- a partner/integration identifier.

Do not disguise automation as human activity when disclosure or a registered application identity is required. Never treat successful evasion of a platform control as evidence of authorization.

## Authentication and credential boundaries

Public platform-access records may contain credential **references** and properties such as issuer, owner, scope, rotation owner, expiry class, and secret-store location class. They must never contain:

- passwords;
- cookies or session tokens;
- API keys;
- access/refresh tokens;
- private keys;
- authentication headers;
- raw private account content.

A user-supplied session still requires both principal delegation and platform authorization for the intended automation.

## Action matrix

Explicitly classify each consequential capability as `allowed`, `blocked`, or `review_required`:

- read/search;
- write/update;
- send message/comment;
- upload/download;
- purchase/order;
- account/profile changes;
- permission/member changes;
- destructive/delete actions.

The runtime should default-deny actions absent from the matrix. An allowed read path does not imply allowed writes, purchases, messages, or deletes.

## Rate, concurrency, challenge, and abuse controls

Record platform-specific limits where known and add conservative local limits even when platform limits are unpublished. Include:

- requests per interval;
- concurrent sessions/jobs;
- retry count and backoff;
- message/action velocity;
- transaction caps;
- response to `429`, account lock, CAPTCHA/challenge, block pages, unusual verification, or explicit objection.

CAPTCHA, challenge, blocking, or account restriction is a stop/escalation signal, not a permission path. Do not build bypass logic into this operating system.

## Change detection

Re-review the record when any of these occur:

- terms or developer-policy update;
- API version/deprecation notice;
- OAuth scope or app-review change;
- new robot/crawler directive relevant to the workflow;
- authentication or identity requirement change;
- repeated `401`, `403`, `429`, block page, challenge, or account lock;
- explicit platform/counterparty objection;
- customer account ownership change;
- access method or material action change.

A material unresolved change should move the integration to `restricted` or `suspended`, not remain `active` by inertia.

## Active-state gate

Before `active`, require current evidence for all of the following:

1. principal delegation exists for the intended purpose and actions;
2. platform authorization basis exists for the selected access method;
3. terms/policy provenance is recorded and not stale under the configured review window;
4. identity/disclosure behavior is compatible with known requirements;
5. credentials are referenced, not embedded;
6. allowed and blocked actions are explicit;
7. rate/retry/challenge controls are configured;
8. representative tests passed;
9. no unresolved explicit revocation, blocking, or authorization uncertainty exists.

## Suspension and recovery

Immediately suspend or narrow automation when:

- platform authorization is revoked or expires;
- the platform explicitly objects to the automation;
- the integration receives a material access block or challenge that cannot be safely explained;
- terms/policy evidence becomes materially uncertain;
- credential ownership or principal delegation is revoked;
- the agent performs or attempts an action outside the approved matrix;
- cross-user/session leakage is suspected.

Recovery requires new evidence for the condition that caused suspension. Do not resume merely because a retry succeeds.

## Audit and incident handoff

Audit at minimum:

- platform-access record/version;
- principal delegation reference;
- platform authorization evidence reference;
- selected access method;
- material terms/policy reference;
- identity/app identifier class;
- action category;
- consequential side-effect receipt/reference;
- block/challenge/revocation signals;
- suspension/restriction decisions and approvals.

Open an incident path for suspected unauthorized access, cross-user session leakage, actions outside the matrix, credential exposure, account lockout affecting customers, or consequential actions performed after suspension.

## Founder metrics

Track operationally useful metrics rather than raw request volume:

- percentage of active integrations with current authorization evidence;
- stale-policy exposure hours;
- access denials and challenges by platform/method;
- retries prevented by stop controls;
- unauthorized-action attempts blocked locally;
- suspensions caused by policy/access changes;
- mean time from revocation signal to automation stop;
- customer workflows affected by suspension;
- official-API migration rate for less-supported access methods.

## Safe starter

Use `templates/PLATFORM_ACCESS_RECORD.json`. It begins in `proposed` with no active authority, no credentials, no allowed consequential actions, and no assumption that a public or technically reachable surface permits automation.

Validate records with:

```bash
python scripts/validate_platform_access.py templates/PLATFORM_ACCESS_RECORD.json
```

## Related resources

- `docs/AGENT_AUTHORITY_DELEGATION.md` — principal authority boundaries.
- `docs/AGENT_LEGAL_COMPLIANCE.md` — legal/compliance escalation framework.
- `docs/AGENT_API_CONTRACTS_INTEROPERABILITY.md` — stable machine contracts.
- `docs/AGENT_AUDIT_EVIDENCE.md` — durable action evidence.
- `docs/AGENT_INCIDENT_RESPONSE.md` — containment and forensic response.
- `docs/AGENT_PRIVACY_REQUESTS_ERASURE.md` — downstream privacy obligations.

This is an operating and evidence framework, not a legal conclusion about any particular platform or access method.