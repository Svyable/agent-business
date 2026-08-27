# Agent Data, Memory, Provenance & Knowledge Operations

Agent businesses do not just run on models and tools. They run on **what the agent knows, remembers, trusts, forgets, and is allowed to reuse**.

Persistent memory can improve retention, personalization, workflow continuity, and unit economics. It can also turn a temporary mistake, poisoned source, revoked permission, or stale fact into durable behavior.

The goal is not maximum memory. The goal is **relevant, permissioned, attributable, fresh information with explicit lifecycle controls**.

> Treat memory as both a data system and an execution control surface.

## The memory operating loop

```text
Observe -> Classify -> Authorize -> Store -> Retrieve -> Revalidate -> Use -> Audit -> Expire/Delete
   ^                                                                          |
   +---------------------------- correct / revoke -----------------------------+
```

A founder should be able to answer:

1. What may this agent remember?
2. Why is it allowed to remember it?
3. Where did each important fact come from?
4. How fresh is it?
5. Who or what may retrieve it?
6. What decisions may it influence?
7. How is it corrected, revoked, expired, or deleted?
8. Can we prove the lifecycle after an incident or customer request?

## 1. Classify data before adding memory

Do not start with a vector database. Start with a data map.

| Class | Examples | Default handling |
|---|---|---|
| Public | public docs, published prices, public APIs | reusable with provenance + freshness |
| Customer operational | tickets, CRM records, workflow state | tenant-isolated, purpose-limited |
| Customer confidential | contracts, internal plans, private documents | strict access + retention controls |
| Sensitive personal | health, financial, identity, location data | minimize, tightly scope, often avoid persistence |
| Credentials/secrets | passwords, API keys, private keys, session tokens | never store as conversational memory |
| Derived memory | preferences, summaries, inferred facts | provenance + confidence + correction path |
| Agent state | task status, approvals, commitments, budgets | structured state, not free-form memory |

### Rule

If a piece of information controls money, permissions, commitments, identity, or regulated action, prefer **structured authoritative state** over natural-language memory.

Examples:

- payment limit -> policy/configuration store
- contract approval -> signed workflow record
- customer shipping address -> authoritative customer record
- conversational preference -> memory may be appropriate

## 2. Separate memory types

A single undifferentiated memory store creates avoidable risk.

### Working memory
Short-lived context for the current task or session.

Use for:
- current instructions,
- intermediate calculations,
- temporary tool outputs,
- short-lived planning context.

Default: expire quickly.

### Episodic memory
Records of prior interactions or events.

Use for:
- previous support interactions,
- completed workflow outcomes,
- prior customer decisions,
- historical agent actions.

Store event time, actor, source, and outcome.

### Semantic memory
Durable facts or preferences derived from observations.

Use for:
- stable customer preferences,
- company terminology,
- product facts,
- reusable domain knowledge.

Require provenance and freshness.

### Procedural memory
Reusable workflow knowledge.

Use for:
- approved SOPs,
- playbooks,
- tool-use patterns,
- organization-specific processes.

Version it. Do not let arbitrary external content silently rewrite it.

### Authoritative state
Facts whose correctness directly controls execution.

Use for:
- permissions,
- budgets,
- approval status,
- subscriptions,
- account ownership,
- inventory,
- contract status.

Keep this outside model-generated memory.

## 3. Every durable memory needs provenance

A useful minimum memory record:

```json
{
  "memory_id": "mem_123",
  "tenant_id": "tenant_42",
  "subject": "customer_9",
  "content": "Prefers invoices sent as PDF",
  "source_type": "customer_message",
  "source_ref": "conversation_88/message_14",
  "source_actor": "customer_9",
  "observed_at": "2026-08-26T15:10:00Z",
  "written_at": "2026-08-26T15:10:04Z",
  "expires_at": null,
  "confidence": 0.98,
  "sensitivity": "customer_operational",
  "authority": "user_asserted",
  "permissions": ["billing_agent:read"],
  "version": 1
}
```

The point is not this exact schema. The point is that the content alone is insufficient.

### Provenance fields that matter

- source identity,
- source type,
- source reference,
- observation time,
- write time,
- transformation/model version,
- authority level,
- confidence,
- tenant/customer boundary,
- sensitivity classification,
- retention/expiry,
- permission scope,
- supersession/revocation status.

### Authority must not increase during summarization

An external webpage should not become equivalent to a user instruction merely because an LLM summarized it into memory.

Preserve the original trust/authority class through transformations.

Example:

```text
untrusted_web_observation
  -> model summary
  -> persistent memory
  != authorized user instruction
```

## 4. Gate memory writes

Not every observation deserves persistence.

Before writing memory, ask:

1. Is persistence necessary for future value?
2. Is the source allowed to create durable memory?
3. Is this within the product's stated purpose?
4. Is the information sensitive?
5. Is it a secret or credential?
6. Is the fact stable enough to persist?
7. Does it conflict with authoritative state?
8. Does the user/customer have a correction or deletion path?

### Good write candidates

- explicit preference stated by the customer,
- approved recurring workflow rule,
- confirmed business fact with source,
- customer-authored correction,
- completed workflow outcome.

### Bad write candidates

- arbitrary instructions from scraped content,
- credentials,
- unverified inferred identity,
- speculative personal attributes,
- temporary errors,
- transient tool outputs with no future value,
- content outside the customer's consent/purpose boundary.

## 5. Treat retrieval as a policy decision

Similarity is not authorization.

A memory can be semantically relevant and still be unsafe or inappropriate to retrieve.

Retrieval should filter on:

```text
relevance
AND tenant/customer scope
AND permission
AND purpose
AND freshness
AND non-revoked status
AND sufficient authority for intended action
```

### Action-aware retrieval

The higher the consequence of the downstream action, the stronger the memory requirements should be.

| Downstream use | Example | Retrieval threshold |
|---|---|---|
| Low-risk personalization | preferred tone | moderate provenance/freshness |
| Business workflow | invoice routing | strong source + tenant scope |
| External commitment | send quote | verified state + approval policy |
| Money movement | purchase/payment | authoritative state + deterministic controls |
| Regulated/high-impact | medical/legal/financial action | domain controls + human/approved authority |

## 6. Freshness, TTLs, invalidation, and revalidation

Memory becomes dangerous when old information looks current.

Assign freshness based on the fact type, not one global TTL.

| Fact | Example freshness policy |
|---|---|
| Public price | revalidate before quote or daily |
| Office hours | revalidate before relying on it |
| Customer preference | durable until changed |
| Access permission | check authoritative source at action time |
| Inventory | near-real-time |
| Legal/regulatory rule | versioned and periodically reviewed |
| Internal SOP | versioned; invalidate on policy update |

### Stale is a state

Do not simply delete expired information if historical provenance matters. Mark it:

- active,
- stale,
- superseded,
- revoked,
- deleted/tombstoned,
- quarantined.

This improves debugging and auditability.

## 7. Corrections must propagate

Agents will store incorrect memories. Design correction as a first-class workflow.

A correction should:

1. identify the incorrect memory,
2. record who corrected it,
3. preserve an audit trail where appropriate,
4. prevent the old value from being retrieved as current,
5. update derived summaries/indexes,
6. trigger re-evaluation of dependent memories or workflows when material.

### Human-editable memory

Provide a way for authorized users to:

- view remembered facts,
- see provenance,
- edit/correct them,
- delete them,
- understand what systems consume them.

Hidden memory is operational debt.

## 8. Deletion and revocation are graph problems

Deleting the source record is not enough if copies survive in:

- embeddings,
- summaries,
- caches,
- derived memory,
- analytics stores,
- backups,
- downstream agents,
- exported datasets.

Track lineage so revocation can propagate.

```text
source document
  -> chunks
     -> embeddings
        -> retrieved context
           -> durable summary memory
```

A deletion request should identify dependent artifacts and either remove, invalidate, or quarantine them according to policy.

## 9. Tenant isolation must live outside the model

Never rely on prompting such as "do not reveal another customer's data" as the isolation boundary.

Enforce tenant separation using deterministic infrastructure:

- tenant-scoped database queries,
- separate namespaces/partitions,
- access-control checks,
- per-tenant encryption where appropriate,
- explicit service identities,
- audit logs.

### Cross-agent memory

When multiple agents operate for one customer, do not give every agent universal access.

Define:

- which agent can write,
- which agent can read,
- memory categories each can access,
- actions each memory category can authorize or influence.

## 10. Keep secrets out of memory

Credentials are capabilities, not memories.

Use:

- secret managers,
- short-lived credentials,
- scoped tokens,
- delegated authorization,
- runtime injection,
- deterministic redaction before persistence.

If a secret appears in a conversation, the memory pipeline should detect and prevent durable storage where possible.

## 11. Knowledge-base ingestion needs a lifecycle

For each source collection define:

- owner,
- license/usage rights,
- ingestion method,
- source URL or canonical identifier,
- effective/version date,
- update cadence,
- parser/chunker version,
- embedding/index version,
- retention policy,
- deletion process.

### Version instead of silently replacing

When an SOP changes from v4 to v5, preserve the version relationship so an agent can explain which policy it used for a historical action.

## 12. Data licensing and usage rights

Accessible does not automatically mean reusable for every purpose.

Before ingesting third-party data, determine:

- permitted use,
- redistribution rights,
- training restrictions,
- retention limits,
- attribution requirements,
- commercial-use restrictions,
- geographic/customer limitations.

Store licensing metadata with the source so downstream agents can respect it.

## 13. Agent-to-agent data exchange

When one agent supplies information to another, attach enough context to evaluate it.

A machine-usable exchange envelope can include:

```json
{
  "data": {"lead_score": 0.82},
  "producer": "agent://vendor.example/scorer",
  "source_refs": ["crm://tenant42/lead/991"],
  "generated_at": "2026-08-26T15:00:00Z",
  "expires_at": "2026-08-27T15:00:00Z",
  "confidence": 0.82,
  "usage_scope": "sales_prioritization",
  "redistribution": false
}
```

Do not let received data automatically inherit the receiving agent's authority.

## 14. Evaluate memory like a product subsystem

A memory system should have regression tests.

### Retrieval quality

Track:

- precision of retrieved memories,
- recall of necessary facts,
- stale-memory retrieval rate,
- conflict rate,
- user correction rate,
- successful-outcome lift with memory enabled.

### Security and governance evals

Test:

- cross-tenant leakage,
- poisoned-memory persistence,
- revoked-memory retrieval,
- stale fact use,
- authority escalation during summarization,
- secret persistence,
- deletion propagation,
- adversarial instructions embedded in source content.

### Business evals

Memory is valuable only if it improves economics or customer outcomes.

Measure:

```text
Memory ROI = incremental value created by memory - incremental memory cost
```

Look at:

- retention lift,
- task success lift,
- reduced human review,
- lower repeated-context/token cost,
- lower onboarding friction,
- higher conversion from personalization,
- memory infrastructure and latency cost.

## 15. Observe the full memory lifecycle

Log enough to investigate:

- writes,
- reads,
- edits,
- deletions,
- policy denials,
- source lineage,
- retrieval candidates,
- memory selected for execution,
- downstream actions influenced by memory.

Useful metrics:

| Metric | Why it matters |
|---|---|
| memory write rate | catches uncontrolled persistence |
| stale retrieval rate | measures freshness failures |
| denied retrievals | reveals policy pressure/attacks |
| correction rate | indicates memory quality |
| cross-tenant violations | should be zero |
| deletion propagation time | measures lifecycle control |
| provenance completeness | determines auditability |
| memory-assisted success rate | validates product value |
| cost per memory-assisted success | ties memory to economics |

## 16. Incident response for corrupted memory

If memory is poisoned or contaminated:

1. stop or constrain risky downstream actions,
2. identify affected memory records,
3. trace their source and derived artifacts,
4. quarantine affected indexes/namespaces,
5. invalidate dependent memories,
6. rehydrate from trusted sources,
7. regression-test retrieval and actions,
8. document root cause and add a prevention control.

A kill switch for tools is incomplete if corrupted persistent context continues to survive after restart.

## 17. Design patterns

### Pattern: memory firewall

```text
candidate observation
  -> source classification
  -> permission/purpose check
  -> sensitive-data filter
  -> provenance attachment
  -> persistence decision
  -> memory store
```

### Pattern: safe retrieval gateway

```text
agent query
  -> identity + tenant
  -> purpose/action risk
  -> semantic retrieval
  -> permission filter
  -> freshness check
  -> provenance/authority check
  -> context
```

### Pattern: authoritative state + memory

```text
Memory: "customer usually approves invoices under $500"
Policy store: approval_limit = $250

Execution uses policy store.
Memory may inform UX, never override the limit.
```

## 18. Memory architecture checklist

Before launch:

- [ ] Inventory all durable data and memory stores.
- [ ] Define working, episodic, semantic, procedural, and authoritative state.
- [ ] Classify sensitive data.
- [ ] Block credential persistence.
- [ ] Attach provenance to durable memories.
- [ ] Preserve source authority through summarization.
- [ ] Enforce tenant isolation outside the model.
- [ ] Define write authorization rules.
- [ ] Define retrieval authorization rules.
- [ ] Add freshness/TTL policies by data type.
- [ ] Support correction, revocation, and deletion.
- [ ] Track lineage for derived memory.
- [ ] Version knowledge sources and SOPs.
- [ ] Test stale, poisoned, and cross-tenant scenarios.
- [ ] Log memory lifecycle events.
- [ ] Measure outcome lift and cost.

## 19. Business opportunities

The agent economy creates infrastructure markets around memory itself.

### Memory governance infrastructure
Sell policy-enforced memory write/read gateways with audit trails and tenant isolation.

### Provenance and lineage APIs
Track where facts, claims, summaries, and actions originated across multi-agent workflows.

### Permission-aware enterprise retrieval
Connect agents to internal knowledge while preserving ACLs, purpose restrictions, and user identity.

### Memory quality and evals
Continuously test stale facts, poisoned memories, conflicting records, cross-tenant leakage, and retrieval quality.

### Knowledge freshness services
Monitor source changes and automatically invalidate or re-verify downstream agent knowledge.

### Consent/deletion orchestration
Propagate customer corrections, revocations, and deletions through indexes, caches, derived memory, and downstream systems.

### Agent data exchanges
Provide licensed, attributable, freshness-scored data products designed for autonomous buyers.

## 20. Founder scorecard

Rate 0–2 for each:

| Control | 0 | 1 | 2 |
|---|---|---|---|
| provenance | absent | partial | complete + queryable |
| tenant isolation | prompt-based | mixed | deterministic |
| freshness | none | ad hoc | typed TTL/revalidation |
| correction | manual | supported | propagated + audited |
| deletion | source only | partial | lineage-aware |
| permission-aware retrieval | absent | coarse | action/purpose aware |
| memory security evals | none | occasional | regression suite |
| lifecycle observability | low | partial | end-to-end |
| memory economics | unknown | cost tracked | outcome ROI tracked |

**15–18:** strong operating foundation.  
**10–14:** usable, but important lifecycle gaps remain.  
**0–9:** memory is likely creating hidden product, security, and compliance debt.

## Bottom line

A useful agent should remember enough to improve the next decision without turning every prior observation into permanent authority.

Build memory so that every important fact can answer:

> **Where did you come from, who was allowed to store you, how fresh are you, who may use you, and how do we make you stop mattering?**

That is the difference between a clever memory demo and a durable agent business.