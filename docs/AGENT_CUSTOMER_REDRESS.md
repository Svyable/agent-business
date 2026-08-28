# Agent Customer Complaints, Redress, and Human Escalation

Autonomous agents can produce outcomes that are technically successful yet still disputed, harmful, misleading, unauthorized, incorrectly billed, or inconsistent with customer expectations. Agent businesses therefore need a redress system that is separate from the agent's own execution authority.

Use this playbook to receive complaints, correlate them to evidence, route consequential cases to humans, approve remedies through explicit authority, verify remediation, and turn recurring complaints into product and operating improvements.

This is an operating framework, not legal advice.

## Core rules

1. **A complaint is not an incident, but it can reveal one.** Incident response is operator-triggered; complaints originate with customers or affected parties and may expose security, privacy, billing, transparency, fairness, contractual-scope, or service-quality failures.
2. **The agent that executed an action does not inherit authority to adjudicate the complaint about that action.** Execution authority and remedy authority are separate.
3. **Complaint status never grants financial, legal, deletion, communication, or transaction authority.** Refunds, credits, reversals, admissions, account changes, and data deletion require separately evidenced authority.
4. **Preserve allegation, fact, interpretation, and decision as separate fields.** Do not rewrite an allegation into an established fact or dismiss it because telemetry looks normal.
5. **Absence of complaints is not evidence of safety or satisfaction.** A hidden, inaccessible, or intimidating complaint channel can suppress the signal.
6. **High-severity uncertainty fails closed to human escalation.** Do not auto-close safety, security, privacy, unauthorized-action, or material financial complaints when key evidence is unresolved.

## Lifecycle

Use a lifecycle that preserves both investigation and appeal state:

`received -> acknowledged -> triaged -> investigating -> remediation_proposed -> awaiting_approval -> resolved | rejected_with_reason -> appealed -> closed`

Additional rules:

- `received` means the complaint is durably recorded, not merely accepted by a chat UI.
- `acknowledged` requires a customer-visible acknowledgement or equivalent delivery evidence.
- `triaged` requires an explicit category, severity, owner, and escalation decision.
- `resolved` means the approved remedy has been executed and verified, or an evidence-backed no-remedy decision has been communicated.
- `closed` is administrative finalization after required remediation, communication, preservation, and appeal handling are complete.
- an appeal reopens independent review; it must not be routed only to the original decision maker for consequential disputes.

## Minimum complaint record

A portable complaint record should include only disclosure-safe information:

- complaint ID;
- complainant-safe identifier or pseudonymous reference;
- affected tenant/account reference;
- received and acknowledgement timestamps;
- channel and accessibility/language needs;
- agent ID and release/version when known;
- disputed action or outcome ID;
- complaint category and severity;
- allegation summary;
- requested remedy;
- evidence references;
- investigation owner;
- status and status history;
- observed facts;
- operator interpretation;
- decision and decision rationale;
- decision authority and authority evidence;
- remediation actions and verification evidence;
- communication evidence;
- appeal state and independent reviewer when applicable;
- preservation/legal-hold state; and
- recurring root-cause or product-change linkage.

Do not copy credentials, raw prompts, payment credentials, private customer data, privileged legal advice, or sensitive evidence into a public record. Reference controlled evidence stores instead.

## Intake and channel design

A complaint mechanism is operational only if people can discover and use it.

Require:

- a clearly discoverable human escalation path;
- an acknowledgement target appropriate to the business and severity;
- accessible channel design;
- language/support handling appropriate to the customer population;
- a path for affected non-admin users when the product can materially affect them;
- minimal data collection; and
- a fallback when the agent itself is unavailable, compromised, or the subject of the complaint.

Never require a complainant to disclose unnecessary sensitive data to obtain review. Do not optimize complaint volume down by hiding the channel, adding avoidable friction, or silently deflecting cases back into self-service loops.

## Deterministic triage

Classify every complaint into one or more categories. At minimum support:

| Category | Examples | Default escalation signal |
|---|---|---|
| safety_security | harmful action, compromised agent, unsafe tool execution | human/security review |
| privacy | unwanted retention, disclosure, consent or deletion dispute | privacy workflow + human review |
| billing_financial | wrong charge, duplicate charge, disputed usage, refund request | billing evidence + explicit remedy authority |
| unauthorized_action | purchase, message, deletion, account change outside authority | freeze/reconcile + human review |
| transparency_deception | undisclosed AI interaction, misleading provenance or capability claim | transparency review |
| service_quality | incorrect result, missed SLA, failed delivery | service recovery |
| discrimination_fairness | alleged disparate or unfair treatment | independent human review |
| contractual_scope | work outside sold/approved scope | contract + implementation evidence review |
| other | material claim not captured above | human triage when consequential |

Severity must reflect potential impact, not customer sentiment alone. A calm report of an unauthorized funds transfer can be more severe than an angry report of a cosmetic defect.

## Correlate before deciding

Where available, link the complaint to existing operating evidence rather than creating a parallel truth system:

- audit-trail event and side-effect receipt;
- incident record;
- billing/metering event;
- privacy request;
- AI transparency/provenance record;
- platform-access authorization record;
- release/change-management record;
- tenant-operations record;
- customer implementation and success records; and
- external provider/tool evidence.

Correlation must be version-aware. A complaint about release `R17` cannot be dismissed using evidence only from the current `R22` configuration.

## Investigation discipline

Maintain four distinct statements:

- **Allegation:** what the complainant says happened.
- **Observed fact:** what current evidence directly supports.
- **Interpretation:** the operator's current explanation of those facts.
- **Decision:** the approved disposition and remedy.

For material cases, document contradictory evidence and unresolved uncertainty. Do not treat model-generated summaries as source evidence when original records are available.

If logs are incomplete, say so. Tamper-evident audit history can establish integrity of captured events but does not prove that every relevant event was captured.

## Independent remedy authority

Create a remedy authority matrix before automating resolution.

| Remedy | Example authority gate |
|---|---|
| explanation | support policy allows non-binding explanation |
| correction/re-performance | delivery authority within sold scope |
| service credit | explicit credit threshold and approver |
| refund | explicit financial threshold and refund approver |
| transaction reversal | verified reversible action + transaction authority |
| account/config change | account administrator or delegated operations authority |
| data correction/deletion | privacy workflow and required identity verification |
| legal admission/settlement | designated human/legal authority only |
| policy/product change | change-management approval |
| no-remedy decision | evidence-backed reviewer authority; appeal path where appropriate |

The agent may recommend a remedy without having authority to execute it. Record recommendation and approval separately.

## Consequential action rule

Before approving a consequential remedy, verify:

- the complaint maps to the correct tenant/account and disputed action;
- identity/standing checks required for the remedy are complete;
- the action is reversible or its downstream effects are understood;
- financial, legal, privacy, communication, and transaction authority are explicitly scoped;
- duplicate execution is prevented with idempotency/reconciliation controls;
- evidence is preserved before destructive remediation when required; and
- the complainant is told what was actually done, not merely what was requested.

## Human review and appeals

Require human review when:

- severity is high or critical;
- consequential financial or account actions are disputed;
- privacy, security, safety, discrimination/fairness, or legal issues are alleged;
- evidence conflicts or is materially incomplete;
- the agent's own behavior or authorization boundary is the subject of the complaint;
- the proposed remedy exceeds delegated authority; or
- policy requires independent review.

For appeals, preserve the original decision and route to an independent reviewer or authority tier when the outcome is consequential. An appeal is not satisfied by having the same agent restate the previous rationale.

## Remediation matrix

A complaint can end in one or more of these outcomes:

- explanation with evidence;
- correction or re-performance;
- refund or credit request;
- transaction reversal request;
- data correction/deletion handoff;
- service recovery;
- incident escalation;
- security containment;
- policy/configuration change;
- release rollback or fix;
- customer-success intervention;
- provider/platform escalation; or
- no-remedy decision with evidence-backed rationale.

For every executed remediation, require verification evidence. A queued refund is not a verified refund. A requested deletion is not verified deletion. A proposed configuration fix is not a deployed fix.

## Duplicate, abusive, and coordinated complaints

Handle duplicates by linking records, not deleting evidence. Preserve the earliest receipt time and any unique evidence from later submissions.

Abusive content can be rate-limited or moderated without silently dismissing the underlying claim. Separate behavior-policy enforcement from merits review. A hostile complainant can still report a valid unauthorized action.

For coordinated complaint spikes, use aggregate triage and incident correlation, but preserve individual remedy rights and tenant/account boundaries.

## Evidence preservation

Complaints can become security, regulatory, contractual, litigation, or incident evidence.

- preserve relevant audit and side-effect records before destructive remediation;
- honor active retention and legal-hold controls;
- record chain-of-custody references for exported evidence;
- limit evidence access by role and tenant;
- do not let the execution agent delete or rewrite complaint evidence about itself; and
- retain only what policy and applicable obligations require.

## Closure gate

Do not mark a complaint `closed` unless all applicable gates pass:

- acknowledgement occurred or a documented reason explains why it could not;
- category, severity, owner, and decision authority are recorded;
- material evidence has been correlated to the correct action/release;
- high-severity uncertainty has been escalated;
- required remediation is executed and verified;
- required customer communication is delivered or delivery failure is recorded;
- appeal requirements are satisfied;
- preservation/hold requirements are satisfied; and
- recurring root-cause follow-up is assigned when appropriate.

## Metrics that resist gaming

Track more than raw complaint count:

- complaints per successful customer outcome;
- acknowledgement time;
- median and tail resolution time;
- open high-severity complaints;
- reopen rate;
- appeal rate and appeal overturn rate;
- upheld complaint rate;
- refund/credit/reversal cost;
- incident-conversion rate;
- duplicate complaint rate;
- recurring root causes;
- percentage of remedies verified after execution; and
- percentage of consequential decisions receiving required human review.

Interpret falling complaint volume cautiously. Pair it with channel availability, usage, retention, outcome quality, and customer-success signals.

## Failure modes to test

At minimum exercise these scenarios:

1. complaint channel is hidden or only reachable through the disputed agent;
2. complaint is auto-closed because monitoring shows no incident;
3. executing agent self-approves a refund or transaction reversal;
4. current-release evidence is incorrectly used for an older disputed release;
5. complaint evidence is deleted while under hold;
6. privacy complaint intake over-collects identity or sensitive data;
7. high-severity security complaint remains in routine support queue;
8. appeal is routed to the same automated decision maker with no independent review;
9. duplicate handling discards unique evidence;
10. abusive-language moderation causes silent merits dismissal;
11. remediation is marked complete when only requested, queued, or proposed;
12. refund/reversal retries create duplicate economic side effects;
13. complaint closure occurs with an unresolved consequential action;
14. complaint absence is reported as proof of customer safety/satisfaction; and
15. an agent infers legal or financial authority from support-tool write access.

## Founder operating rhythm

### Daily

- review newly received high-severity complaints;
- verify acknowledgement backlog;
- inspect unresolved consequential side effects;
- check failed remediation executions and delivery failures.

### Weekly

- review aging complaints and appeals;
- inspect recurring categories and releases;
- reconcile refunds, credits, reversals, and other economic remedies;
- convert systemic complaints into incidents, evals, or product changes when warranted.

### Monthly

- review complaint rate per successful outcome and tail resolution time;
- test channel discoverability and accessibility;
- audit remedy authority thresholds;
- sample closed records for evidence and remediation fidelity;
- update failure-mode evals from real complaint patterns.

## Founder checklist

Before claiming customer redress is operational, confirm that you can answer:

- What was alleged?
- Which tenant, action, agent, and release did it concern?
- What facts were established, and which uncertainties remain?
- Who owned the investigation?
- Who had authority to approve the disposition and remedy?
- Was a human or independent appeal path available when required?
- What remediation was actually executed and verified?
- What evidence was preserved?
- What did the complainant receive?
- Did the complaint expose a recurring failure that should change the product, policy, eval suite, or operating system?

A trustworthy agent business does not merely make autonomous decisions quickly. It can also reconstruct, question, correct, and—when appropriate—reverse those decisions under explicit human and economic authority.
