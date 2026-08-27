# Agent Treasury, Accounting & Financial Operations

Autonomous businesses can create thousands or millions of commercial events faster than a human finance team can inspect them. The financial system therefore has to do more than move money: it must preserve evidence, constrain authority, reconcile independent ledgers, explain cash, and surface exceptions before they become existential.

This guide is about **system design and operating discipline**, not jurisdiction-specific accounting, tax, banking, securities, or legal advice. Use qualified professionals for high-stakes treatment decisions.

## The objective

A founder should be able to answer, at any moment:

1. What did we sell or buy?
2. What was actually delivered?
3. What do we owe and what are we owed?
4. What cash has settled, where, and in what currency?
5. Which agent or human authorized each material action?
6. Which records disagree?
7. How much runway do we have under realistic scenarios?
8. Can an accountant, auditor, investor, or counterparty reproduce the answer from evidence?

The core chain is:

```text
Intent -> Contract -> Delivery -> Bill -> Payment -> Settlement -> Accounting evidence -> Reconciliation -> Close
```

Never collapse these stages into one mutable status field.

## 1. Separate the financial truths

An agent business usually needs at least four independently auditable truths.

### Commercial truth

What was agreed: order, quote, price, scope, quantity, refund rights, service level, currency, tax inputs, and counterparty.

### Delivery truth

What was actually delivered: workflow completion, accepted result, usage units, verification evidence, failure, cancellation, or dispute.

### Cash truth

What money moved: authorization, capture, transfer, payout, bank settlement, wallet transfer, fee, refund, reversal, chargeback, FX conversion, or failed settlement.

### Accounting truth

How finance professionals classify the economic activity in the books.

These truths are related but are not interchangeable. A successful payment does not prove revenue was earned. An invoice does not prove cash settled. A model-generated ledger entry does not prove the underlying commercial event existed.

## 2. Build a canonical financial event model

Every material event should be immutable, uniquely identified, time-stamped, and linked to its source evidence.

A useful base envelope:

```json
{
  "event_id": "fev_01J...",
  "event_type": "payment_settled",
  "occurred_at": "2026-08-27T12:00:00Z",
  "recorded_at": "2026-08-27T12:00:02Z",
  "entity_id": "company_123",
  "counterparty_id": "vendor_456",
  "commercial_object_id": "order_789",
  "currency": "USD",
  "amount_minor": 125000,
  "source_system": "processor_x",
  "source_reference": "txn_abc",
  "authority_id": "mandate_42",
  "evidence_refs": ["receipt_1", "invoice_2"],
  "schema_version": "1.0"
}
```

Recommended event families:

- quote created, accepted, expired;
- order authorized, amended, cancelled;
- delivery started, completed, accepted, rejected;
- usage measured and corrected;
- invoice issued, credited, voided;
- payment authorized, captured, failed, refunded, disputed;
- payout initiated, settled, reversed;
- vendor bill received, approved, paid;
- bank or wallet transaction posted;
- fee assessed;
- FX conversion executed;
- accounting entry proposed, approved, posted, reversed;
- reconciliation match, break, resolution;
- tax/document classification added or corrected.

Do not overwrite a bad event. Append a correction or reversal linked to the original.

## 3. Use stable identifiers across systems

The fastest way to create unreconcilable finance operations is to let billing, payments, bank records, and accounting systems invent unrelated identifiers.

Carry durable references across the chain:

```text
customer -> contract -> order -> delivery -> usage -> invoice -> payment -> settlement -> journal evidence
```

For each hop, record both your canonical identifier and the external system identifier. Store the mapping as data, not tribal knowledge.

## 4. Treat authority as financial data

Every autonomous financial action should be traceable to a mandate.

A mandate should define:

- principal;
- agent identity;
- permitted action types;
- counterparties or categories;
- per-transaction limit;
- daily/weekly/monthly aggregate limit;
- currency restrictions;
- prohibited categories;
- approval thresholds;
- expiration;
- revocation method;
- required evidence;
- fallback behavior when uncertain.

Example policy:

```yaml
agent: procurement-agent
allowed:
  - vendor_invoice_payment
currency: USD
per_transaction_limit: 1000
monthly_limit: 10000
vendors:
  allow: [hosting_vendor, data_vendor]
require_human_approval_above: 500
prohibited:
  - cash_advance
  - new_bank_account
  - securities_trade
expires_at: 2026-12-31T23:59:59Z
```

Enforce limits outside the model. The model may recommend an action; deterministic controls decide whether the action is allowed.

## 5. Design treasury around survival, not idle optimization

The treasury function exists first to keep the company solvent.

Track at minimum:

- unrestricted cash;
- restricted or reserved cash;
- receivables likely to settle;
- committed payables;
- payroll/contractor obligations;
- taxes or statutory reserves where applicable;
- processor reserves and payout delays;
- debt service;
- recurring infrastructure commitments;
- refunds/chargeback exposure;
- currency exposure;
- stablecoin or digital-asset exposure if used.

Do not present one bank balance as “cash available.”

## 6. Maintain a cash runway model

Use multiple scenarios rather than one deterministic forecast.

A basic runway calculation:

```text
runway_months = unrestricted_cash / monthly_net_cash_burn
```

But autonomous businesses need a more operational model:

```text
ending_cash(t) = starting_cash
               + expected_collections(t)
               - committed_payments(t)
               - variable_delivery_spend(t)
               - refunds_and_disputes(t)
               - taxes_and_reserves(t)
```

Maintain at least:

- base case;
- downside case;
- growth case;
- settlement-delay stress case;
- provider-cost spike case.

Trigger alerts on thresholds such as 12, 9, 6, and 3 months of runway, adjusted to the business.

## 7. Model working capital explicitly

Fast revenue growth can consume cash.

Track:

- days sales outstanding;
- days payable outstanding;
- invoice-to-cash latency;
- failed payment rate;
- processor settlement latency;
- refund lag;
- dispute reserves;
- vendor prepayment requirements;
- prepaid customer liabilities where relevant.

A business with positive unit economics can still fail if cash leaves faster than it arrives.

## 8. Accounts receivable for agent customers

Machine buyers may expect machine-readable collection states.

Useful invoice states:

```text
draft -> issued -> acknowledged -> due -> paid
                         |         |
                         v         v
                     disputed   overdue
```

Expose structured fields for:

- amount due;
- currency;
- due date;
- purchase-order or mandate reference;
- accepted payment rails;
- delivery evidence;
- dispute endpoint;
- late-payment policy;
- payment receipt.

Collections automation should prioritize based on expected recovery value, customer relationship, amount, age, and dispute context—not send infinite reminders.

## 9. Machine-readable dunning

A safe dunning policy might be:

```yaml
on_due_date:
  action: notify
7_days_overdue:
  action: notify_and_request_status
14_days_overdue:
  action: restrict_new_unpaid_usage
30_days_overdue:
  action: escalate_to_human
never:
  - fabricate_legal_threats
  - impersonate_a_human
  - contact_unapproved_recipients
```

Measure recovery per intervention and customer harm, not merely message volume.

## 10. Accounts payable needs evidence before speed

For every vendor bill, capture:

- vendor identity;
- invoice identifier;
- invoice date and due date;
- amount and currency;
- purchase authorization;
- goods/service receipt evidence;
- account/category suggestion;
- payment rail and beneficiary;
- duplicate fingerprint;
- approvals;
- final settlement reference.

Where appropriate, reconcile three independent facts:

```text
purchase intent <-> vendor invoice <-> receipt/delivery evidence
```

Do not allow a model to create a new beneficiary and immediately pay it without independent controls.

## 11. Duplicate-payment controls

High-volume autonomous systems should detect duplicates using more than invoice number.

Useful signals:

- normalized vendor identity;
- amount;
- currency;
- invoice number;
- invoice date;
- purchase-order reference;
- line-item similarity;
- beneficiary account/wallet;
- file/content hash;
- temporal proximity.

When confidence is uncertain, hold for review rather than silently paying twice.

## 12. Separate approval from execution

A robust pattern:

```text
request -> policy check -> approval -> execution -> settlement verification
```

Different credentials should authorize different stages where practical.

Examples of actions that usually deserve stronger controls:

- first payment to a new beneficiary;
- changing bank or wallet destination;
- increasing limits;
- issuing large refunds;
- moving treasury reserves;
- opening financial accounts;
- borrowing;
- buying financial instruments;
- converting large currency balances.

## 13. Reconciliation is the control plane

Reconciliation asks whether independent records that should agree actually agree.

Core reconciliations can include:

```text
usage ledger <-> invoice ledger
invoice ledger <-> payment ledger
payment ledger <-> processor settlement
processor settlement <-> bank/wallet
vendor bills <-> outgoing payments
cash ledger <-> bank/wallet statements
accounting subledgers <-> general ledger
```

Every reconciliation should produce:

- scope;
- source snapshots;
- matching rule version;
- matched count/value;
- unmatched count/value;
- aging of breaks;
- materiality;
- owner;
- resolution evidence.

## 14. Never let one system reconcile itself

If the same mutable database generates both sides of a reconciliation, the control proves little.

Prefer independently sourced evidence. For example, reconcile your internal payment ledger against processor settlement data and then against bank data.

## 15. Tolerances must be explicit

Not every mismatch is an incident.

Define tolerances for:

- timing differences;
- FX rounding;
- processor fees;
- minimum materiality;
- settlement batching;
- tax rounding;
- expected partial payments.

A tolerance is a documented policy, not “the number looked close enough.”

## 16. Break management

Each reconciliation break should have a state:

```text
new -> classified -> assigned -> investigating -> resolved -> verified
```

Classifications can include:

- timing;
- missing event;
- duplicate event;
- wrong amount;
- wrong currency;
- wrong counterparty;
- fee mismatch;
- settlement failure;
- configuration drift;
- suspected fraud;
- accounting classification issue.

Track both count and value. Ten thousand one-cent breaks may indicate a systemic defect.

## 17. Build a close process agents can execute safely

A high-level month-end close runbook:

1. freeze or version the close period snapshot;
2. verify all source feeds completed;
3. reconcile cash accounts;
4. reconcile processor settlements;
5. reconcile receivables and payables;
6. resolve material usage/billing breaks;
7. identify refunds, credits, disputes, and reversals;
8. validate accrual inputs where applicable;
9. review unusual entries and overrides;
10. obtain required human/professional approvals;
11. lock the period according to policy;
12. generate a close evidence package;
13. record late adjustments separately.

The agent can gather, match, propose, and explain. Material judgment should follow the company’s accounting policy and qualified-professional requirements.

## 18. Make every proposed journal entry explainable

For each proposed entry, store:

- source events;
- calculation;
- account mapping version;
- dimensions;
- policy/rule reference;
- confidence;
- preparer agent;
- approver if required;
- posting timestamp;
- reversal relationship where applicable.

Never accept “the model inferred this” as sufficient evidence.

## 19. Chart-of-accounts design for autonomous operations

Avoid creating a unique account for every agent or product variation. Use dimensions for analytical detail.

Common dimensions:

- product/capability;
- customer;
- vendor;
- agent/service identity;
- region;
- legal entity;
- project;
- contract;
- channel;
- model/provider;
- environment.

This lets founders ask questions such as “gross margin by capability and model provider” without destroying the general ledger structure.

## 20. Revenue-recognition evidence boundaries

The system should preserve evidence needed for the company’s chosen accounting policy without pretending to decide universal treatment.

Potential evidence includes:

- enforceable agreement;
- price and pricing version;
- delivery obligations;
- acceptance or verification event;
- usage period;
- refund rights;
- credits;
- contract modification history;
- collection status.

The classification and timing of revenue can depend on jurisdiction, contract terms, standards, and facts. Route high-stakes conclusions to qualified accountants.

## 21. Tax-ready provenance

Even when tax treatment is outsourced, the operating system should preserve structured facts:

- legal entities;
- customer/vendor jurisdiction fields;
- invoice addresses;
- tax identifiers where lawfully collected;
- product/service classification inputs;
- transaction date/time;
- currency and FX source;
- gross/net/tax components;
- exemption evidence;
- receipts/invoices;
- payment and refund references;
- retention policy.

Do not let an LLM invent tax rates or classifications to make an invoice balance.

## 22. Multi-currency operations

For every monetary event, preserve:

- transaction currency;
- functional/reporting currency where relevant;
- FX rate;
- rate source;
- rate timestamp/date;
- converted amount;
- fees/spread;
- realized/unrealized classification inputs if applicable.

Avoid recomputing historical amounts from today’s rate.

## 23. Stablecoins and digital assets

If the business uses stablecoins or other digital assets, treat the additional operational risks explicitly:

- wallet/beneficiary verification;
- key management;
- chain/network selection;
- finality expectations;
- fee volatility;
- token/issuer risk;
- depeg risk;
- bridge risk;
- sanctions/compliance requirements;
- valuation source;
- transaction provenance;
- accounting/tax treatment uncertainty.

A token labeled “USD” is not operationally identical to cash in a bank account.

## 24. Treasury allocation policy

A small agent business can use a simple policy:

```text
operating cash: enough for near-term obligations
reserve cash: protected runway buffer
processor/wallet balances: minimized to operational need
speculative assets: zero unless explicitly authorized
```

Optimize for survivability and access before yield.

## 25. Financial anomaly detection

Create deterministic and statistical alerts for:

- duplicate payments;
- unusual beneficiary changes;
- spend spikes by agent/vendor/category;
- transactions just below approval thresholds;
- abnormal refund rate;
- chargeback spikes;
- negative-margin customers;
- revenue leakage;
- settlement delays;
- unexplained cash variance;
- stale unreconciled balances;
- repeated manual overrides;
- unusual FX conversion patterns.

Anomaly detection should create a review task, not automatically accuse a counterparty of fraud.

## 26. Revenue leakage checks

Look for delivered value that never becomes collectible revenue.

Examples:

- usage events not rated;
- rated events not invoiced;
- expired credits applied incorrectly;
- entitlement overages delivered for free;
- pricing-version mismatch;
- failed payment followed by continued paid usage;
- refunds larger than original captured value;
- settled payment missing from receivables.

A useful metric:

```text
revenue_leakage_rate = unrecovered_billable_value / total_billable_value
```

## 27. Spend leakage checks

Look for spend that does not produce approved value.

Examples:

- abandoned retries;
- duplicate API calls;
- unused subscriptions;
- orphaned infrastructure;
- duplicate vendor bills;
- over-provisioned capacity;
- agent purchases outside mandate;
- fees caused by avoidable routing choices.

Tie spend to workflow, customer, and outcome whenever possible.

## 28. Financial operations SLOs

Useful SLOs include:

- bank/processor feed freshness;
- reconciliation completion time;
- unresolved material break age;
- invoice generation latency;
- payment posting latency;
- collections response latency;
- close completion time;
- percentage of transactions with complete provenance;
- percentage of autonomous financial actions with valid mandate evidence.

Example:

```text
99.9% of settled payment events appear in the canonical cash ledger within 10 minutes.
100% of material reconciliation breaks receive an owner within 4 hours.
99% of invoices trace to versioned delivery and pricing evidence.
```

## 29. Close metrics

Track:

- days to close;
- automatic match rate;
- manual journal count/value;
- late adjustment count/value;
- unresolved break value at close;
- close tasks completed on time;
- number of control overrides;
- re-opened periods;
- evidence completeness.

Faster close is good only if control quality remains intact.

## 30. Cash dashboard

A founder-facing cash dashboard should show:

- unrestricted cash by account/currency;
- expected 7/30/90-day inflows;
- committed 7/30/90-day outflows;
- runway scenarios;
- receivables aging;
- payables aging;
- processor reserves;
- settlement delays;
- top spend categories;
- current reconciliation breaks;
- alerts requiring approval.

Avoid vanity graphs that cannot be traced to source records.

## 31. Agent-specific financial controls

Autonomous agents create unusual scaling risks. Add controls for:

### Recursive spend

An agent delegates to another agent which delegates again, multiplying spend. Propagate the parent budget downward and prevent child mandates from exceeding remaining authority.

### Retry amplification

A failed paid action triggers retries that each incur cost. Use retry budgets and idempotency keys.

### Microtransaction explosion

Tiny purchases become material in aggregate. Enforce cumulative budgets and rate limits, not only per-transaction caps.

### Price drift

A supplier’s price changes between discovery and execution. Require quote expiration and maximum price/slippage bounds.

### Beneficiary substitution

An agent receives a new payment destination from untrusted content. Treat beneficiary changes as high-risk state changes.

### Currency confusion

A model mistakes dollars, cents, tokens, or foreign currency. Use integer minor units, explicit currency codes, and typed schemas.

## 32. Idempotent financial actions

Every money-moving request should have a stable idempotency identifier linked to business intent.

```text
same intent + same idempotency key -> same economic action
```

Do not generate a fresh payment identity merely because a network call timed out.

## 33. Reversals, refunds, and corrections

Financial history should be append-only.

Instead of mutating a settled payment from 100 to 80, record:

```text
payment +100
refund -20
```

Instead of deleting an incorrect journal proposal, record its rejection or reversal.

This preserves the evidence chain.

## 34. Segregation of duties

As the business grows, avoid allowing one autonomous identity to:

- create a vendor;
- change its beneficiary;
- approve a bill;
- execute the payment;
- reconcile the payment;
- delete the evidence.

Perfect segregation may be unrealistic for a solo founder, but sensitive actions should still require independent controls or explicit human approval.

## 35. Credential isolation

Never give a general-purpose agent unrestricted bank, payment, accounting, and admin credentials.

Prefer scoped service credentials, policy-enforced gateways, short-lived tokens, transaction signing, allowlists, and explicit approval boundaries.

## 36. Immutable evidence packages

For material transactions, be able to produce a package containing:

```text
commercial intent
+ authority/approval
+ delivery evidence
+ invoice/bill
+ payment request
+ settlement evidence
+ reconciliation result
+ accounting mapping
+ corrections/reversals
```

Hash or sign evidence where that improves tamper detection, while keeping privacy and retention requirements in mind.

## 37. Financial data retention

Define retention by record class, jurisdiction, contractual requirements, and operational need.

Include deletion/archival policies for:

- invoices;
- receipts;
- bank/processor data;
- accounting records;
- contracts;
- tax records;
- agent traces;
- approval evidence;
- customer data embedded in financial records.

Do not treat “keep every agent trace forever” as a finance policy.

## 38. Privacy boundaries

Finance systems often hold sensitive personal and commercial data. Minimize what agents receive.

A collections agent may need invoice status and approved contact data, but not full bank credentials or unrelated customer records.

## 39. Finance incident response

Treat certain finance events as incidents:

- unauthorized payment;
- compromised beneficiary;
- duplicate-payment burst;
- reconciliation source corruption;
- accounting integration failure;
- material revenue leakage;
- large settlement delay;
- wallet/key compromise;
- unexpected negative cash balance;
- material reporting error.

A runbook should define:

1. containment;
2. freeze/limit changes;
3. evidence preservation;
4. affected transaction identification;
5. counterparty/provider contact;
6. correction/reversal process;
7. professional/legal escalation where required;
8. root cause;
9. control update;
10. replay/reconciliation verification.

## 40. Build a finance control ledger

Track every sensitive control decision:

```json
{
  "decision_id": "ctl_123",
  "action": "pay_vendor_invoice",
  "actor": "ap_agent",
  "mandate": "mandate_42",
  "policy_version": "treasury-7",
  "result": "requires_human_approval",
  "reason_codes": ["new_beneficiary", "amount_over_500"],
  "evidence_refs": ["invoice_9", "po_12"],
  "timestamp": "2026-08-27T12:00:00Z"
}
```

This makes autonomous finance behavior explainable after the fact.

## 41. Test the financial system with evals

Create deterministic test cases before agents can move real money.

### Treasury evals

- spend within mandate succeeds;
- spend over limit fails;
- expired mandate fails;
- child-agent spend consumes parent budget;
- new beneficiary triggers stronger approval;
- unsupported currency fails safely.

### AP evals

- duplicate invoice is held;
- invoice without purchase evidence escalates;
- beneficiary-change attack is rejected;
- approved bill executes once despite retry.

### AR evals

- corrected usage produces corrected invoice evidence;
- payment posts to correct customer/invoice;
- refund cannot exceed captured amount without explicit exception;
- disputed invoice suppresses inappropriate dunning.

### Reconciliation evals

- timing break clears when settlement arrives;
- true amount mismatch remains open;
- duplicate event is detected;
- missing source feed blocks close completion.

### Close evals

- material unresolved break blocks period lock;
- late adjustment is preserved as a new event;
- evidence package reproduces posted amount.

## 42. Shadow mode before autonomy

Before allowing an agent to execute finance actions:

1. run it in observe-only mode;
2. compare recommendations with existing decisions;
3. measure false positives/negatives;
4. allow low-risk actions with hard limits;
5. expand authority only from evidence.

Earn autonomy rather than granting it by default.

## 43. Financial operations scorecard

A weekly founder scorecard can include:

| Metric | Why it matters |
|---|---|
| Unrestricted cash | immediate survival |
| Base/downside runway | planning horizon |
| Net cash burn | cash velocity |
| DSO / overdue AR | collection quality |
| AP due next 30 days | committed cash need |
| Revenue leakage rate | lost monetization |
| Reconciliation break value | financial-data integrity |
| Auto-match rate | operational efficiency |
| Unauthorized/blocked spend | control effectiveness |
| Close duration | finance maturity |
| Cash forecast error | planning quality |

## 44. Financial operations architecture

A practical architecture can look like:

```text
Commerce / Procurement / Billing / Payments
                  |
                  v
        Canonical financial event log
                  |
        +---------+----------+
        |                    |
        v                    v
 Treasury/control       Finance subledgers
        |                    |
        v                    v
 Banks/wallets          Accounting system
        |                    |
        +----------+---------+
                   v
             Reconciliation
                   |
                   v
             Close + reporting
```

Agents can operate each layer, but the control boundaries should remain explicit.

## 45. Minimal version for a new founder

Do not build enterprise finance infrastructure before revenue.

At very small scale, the minimum is:

- one business bank/payment setup appropriate to the entity;
- simple bookkeeping/accounting system;
- unique invoice/order identifiers;
- receipt/invoice storage;
- weekly cash and runway review;
- basic receivables/payables list;
- explicit agent spend limits;
- monthly bank/payment reconciliation;
- accountant/professional handoff for required filings and treatment decisions.

Add automation only when transaction volume or complexity creates repeated work or risk.

## 46. Scale triggers

Add more infrastructure when measurable thresholds appear:

- reconciliation takes multiple hours per week;
- transaction volume makes manual matching unreliable;
- multiple currencies/entities/payment rails appear;
- autonomous spend becomes material;
- enterprise customers require audit evidence;
- close repeatedly slips;
- collections become a meaningful cash constraint;
- finance errors cause customer or vendor incidents.

## 47. Opportunities for agent founders

The financial operating layer itself creates businesses.

### Agent-native reconciliation

Continuously match commerce, billing, payment, bank, and accounting events and explain breaks with source evidence.

### Autonomous collections infrastructure

Machine-readable dunning, negotiation of payment plans inside policy, dispute routing, and collection analytics.

### Agent treasury control plane

Mandates, budget propagation, beneficiary controls, spend approvals, and multi-rail execution for agent fleets.

### Revenue-assurance agents

Detect billable delivery that did not become invoiced/collected revenue.

### Agent AP control

Extract bills, verify purchase/delivery evidence, detect duplicates, route approvals, and execute bounded payments.

### Close evidence automation

Collect reconciliations, source evidence, approvals, explanations, and late-adjustment logs into reproducible close packages.

### Agent financial observability

Trace economic events across agents: customer revenue, provider cost, delegated spend, settlement, margin, and cash impact.

### Agent transaction provenance

Portable evidence that connects authorization, delivery, payment, and settlement across organizations.

## 48. Pricing financial infrastructure

Potential models:

- per reconciled transaction;
- per active financial account;
- usage tier;
- percentage of recovered leakage or collections, where appropriate;
- monthly platform fee;
- enterprise control/audit tier;
- implementation plus recurring subscription.

Avoid incentives that encourage unnecessary money movement, aggressive collections, or artificial transaction volume.

## 49. Trust is the product

Financial automation wins when customers can answer:

- what happened;
- why;
- under whose authority;
- using which policy;
- with which evidence;
- whether it reconciled;
- how to reverse or correct it.

“AI-powered finance” without those answers is a demo, not financial infrastructure.

## 50. Launch checklist

Before allowing meaningful autonomous finance actions:

- [ ] Define canonical financial event types.
- [ ] Keep commercial, delivery, cash, and accounting truths distinct.
- [ ] Carry stable identifiers across systems.
- [ ] Define agent mandates and aggregate spend limits.
- [ ] Require stronger controls for new beneficiaries and limit changes.
- [ ] Implement idempotency for money movement.
- [ ] Maintain base/downside cash forecasts.
- [ ] Reconcile internal ledgers to independent settlement/bank evidence.
- [ ] Define reconciliation tolerances and break ownership.
- [ ] Preserve append-only corrections and reversals.
- [ ] Test duplicate invoices, retries, stale mandates, and beneficiary substitution.
- [ ] Restrict finance credentials by role and action.
- [ ] Create finance incident runbooks.
- [ ] Measure revenue leakage and spend leakage.
- [ ] Produce transaction and close evidence packages.
- [ ] Route jurisdiction-specific accounting, tax, banking, legal, and regulatory decisions to qualified professionals.

## Founder rule

**An autonomous business is not financially mature because it can move money without humans. It is mature when every material dollar has bounded authority, durable evidence, independent reconciliation, explainable treatment, and a clear effect on cash and runway.**
