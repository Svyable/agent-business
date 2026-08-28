# Agent Tax, Invoicing, and Cross-Border Fiscal Operations

Autonomous commerce can create fiscal obligations faster than a human finance team can notice them.

An agent can quote a buyer in one country, deliver a service from another, collect through a marketplace, pay a supplier elsewhere, issue a refund, settle in a different currency, and create accounting evidence in seconds. The operational problem is not merely “calculate tax.” It is:

> **Determine which rules apply, preserve the evidence for that determination, issue the correct fiscal document, reconcile the resulting money movement, and stop when the answer is uncertain.**

This guide is an operating framework, not tax or legal advice. Tax obligations are jurisdiction-specific and change frequently. Use current official authority, qualified tax/accounting advice where required, and the company’s actual registrations and facts.

## What this playbook optimizes for

A strong fiscal system should make every material transaction reconstructable:

```text
commercial event
     ↓
party + location evidence
     ↓
place-of-supply / jurisdiction determination
     ↓
registration + tax treatment
     ↓
invoice / receipt / credit-note requirement
     ↓
collection / withholding / payout
     ↓
FX translation
     ↓
ledger + reporting evidence
     ↓
reconciliation / close / audit
```

The system should fail closed before invoice issuance or settlement when a required determination is unknown.

## Current standards context

Fiscal infrastructure is becoming more machine-readable, not less.

As of August 2026:

- the European Union’s VAT in the Digital Age (ViDA) package is in implementation; the European Commission’s published timeline includes Single VAT Registration changes from July 2028 and cross-border B2B digital reporting requirements based on e-invoicing from July 2030, with domestic transaction-based systems to align by 2035;
- Peppol BIS Billing 3.0 has a May 2026 release with machine-enforceable invoice, credit-note, currency, identifier, VAT-category, and national rules;
- OECD platform-operator seller-reporting rules remain an active standards area, including a 2026 consultation on targeted amendments after implementation across many jurisdictions;
- country-specific withholding, information-reporting, e-invoicing, marketplace-facilitator, and registration rules continue to change independently.

Treat dates and thresholds in external rules as **versioned evidence**, never timeless constants copied into model prompts.

## Canonical machine artifact

Use:

- schema: `schemas/fiscal-transaction-evidence.schema.json`
- safe starter: `templates/FISCAL_TRANSACTION_EVIDENCE.json`
- semantic validator: `scripts/validate_fiscal_evidence.py`

Validate a record with:

```bash
python scripts/validate_fiscal_evidence.py path/to/fiscal-record.json
```

The starter record intentionally has unresolved jurisdiction, registration, tax, withholding, platform-reporting, and invoice requirements. It is `needs_review`, not ready for invoicing.

## The fiscal state machine

Use a small number of explicit states.

### `draft`

Facts are still being assembled. No operational reliance.

### `needs_review`

At least one material fiscal determination is unknown, provisional, stale, disputed, or requires qualified review.

### `ready_to_invoice`

Jurisdiction and tax treatment are confirmed, registration status is resolved, invoice requirements are known, supporting evidence is current, and required human review is approved.

This state means “fiscal determination is ready,” not “the commercial contract is approved.”

### `issued`

The required invoice/receipt/fiscal document was issued under the approved determination.

### `corrected`

A credit note, corrected invoice, or other adjustment was linked to the original fiscal document and transaction.

### `voided`

The record is retained for provenance but should not drive a current fiscal posting.

## Core rule: unknown is a first-class state

Do not convert uncertainty into a plausible-looking rate.

Bad:

```text
Buyer appears to be in Germany, so VAT is probably 19%.
```

Good:

```text
buyer_country = DE
supply_country = unknown
tax_determination.status = unknown
status = needs_review
```

The system should prefer a visible blocker over a confidently wrong invoice.

## Transaction intake

Every fiscal determination starts with the underlying commercial event.

Capture at minimum:

- transaction ID,
- transaction time,
- sale/service/marketplace/supplier/refund/payout type,
- description of the supply,
- transaction amount and currency,
- seller identity,
- buyer identity,
- platform/intermediary identity when one exists,
- original transaction for a refund or credit.

Do not let the payment processor become the only transaction ledger. Payment rails describe money movement; they may not contain enough facts to determine tax treatment.

## Party evidence

For each relevant party, maintain a tax profile outside free-form model memory.

Useful fields include:

- legal/entity ID,
- country,
- business/consumer classification when relevant,
- tax registration status,
- tax ID reference,
- exemption/resale evidence,
- permanent-establishment or fixed-establishment facts when relevant,
- platform-operator status,
- evidence observation and expiry dates.

### Do not place raw sensitive tax documents in model context by default

The fiscal evidence record should normally point to an authorized internal reference rather than embed full tax IDs, identity documents, bank credentials, or customer files.

## Jurisdiction determination

The first deterministic question is not “what rate?” It is:

> **Which jurisdiction’s rules govern this specific tax obligation?**

Possible facts include:

- seller establishment,
- buyer location,
- billing location,
- service performance location,
- delivery destination,
- property location,
- passenger-transport route,
- digital-service customer evidence,
- marketplace/platform role,
- inventory location,
- establishment involved in the supply.

Different taxes may use different sourcing rules.

### Jurisdiction evidence packet

A confirmed determination should identify:

- seller country,
- buyer country,
- supply/tax country,
- relevant subdivision when needed,
- named ruleset,
- ruleset version or effective period,
- current evidence IDs.

### Never infer location from one weak signal when the rule requires more

Examples of weak signals:

- IP location alone,
- email domain,
- language,
- model guess from company name,
- payment-card country alone.

Use the evidence required by the applicable regime.

## Registration determination

After jurisdiction comes registration.

For each tax regime, classify:

```text
registration_required = yes | no | unknown
```

Do not hard-code a global threshold table into the repository. Thresholds and registration rules can depend on:

- seller presence,
- remote-sales volume,
- transaction type,
- marketplace/deemed-supplier rules,
- customer type,
- prior-year/current-year measurements,
- exemptions,
- voluntary registrations,
- special schemes.

### Registration monitor

A production system should maintain a jurisdiction-level register:

| Field | Purpose |
|---|---|
| jurisdiction | rule scope |
| tax type | VAT/GST/sales tax/etc. |
| current registration status | can the seller collect/report? |
| threshold basis | what metric drives registration? |
| measured exposure | current amount/count |
| warning band | when to review before threshold |
| rule source | official evidence |
| valid through | freshness |
| owner | who resolves change |

The agent can monitor exposure. A qualified owner should approve a new registration determination when required by policy.

## Tax treatment

Only after jurisdiction and registration are resolved should the system determine treatment.

Useful normalized treatments include:

- standard,
- reduced,
- zero-rated,
- exempt,
- reverse charge,
- marketplace/deemed supplier,
- outside scope,
- withholding,
- unknown.

### Rate is evidence, not model output

When a rate applies, store:

- rate,
- tax type,
- treatment,
- jurisdiction,
- effective ruleset,
- evidence ID,
- calculation result.

Never let a language model invent a rate from general knowledge.

### Exemption and reverse-charge evidence

A zero collection amount is not enough to explain treatment.

Preserve the reason:

- exemption reference,
- reverse-charge basis,
- customer tax-registration evidence,
- product/service classification where required,
- effective period.

## Invoice determination

A commercial receipt, tax invoice, e-invoice, self-billing invoice, credit note, and accounting invoice are not interchangeable concepts.

Determine explicitly:

```text
invoice.required = yes | no | unknown
```

If required, determine:

- document type,
- required identifiers,
- seller/buyer information,
- issue date/time rules,
- currency,
- taxable amount,
- tax category/rate/reason,
- payment instructions if required,
- references to orders/contracts/original invoices,
- mandatory machine format or network/profile,
- retention requirements.

## Machine-readable invoicing

When a jurisdiction or customer requires structured e-invoicing, PDF generation is not enough.

Treat the invoice profile as a versioned API contract.

Example evidence fields:

```text
format = UBL
profile = Peppol BIS Billing 3.0 / applicable national profile
ruleset_version = May 2026 release
```

Do not assume a generic Peppol document is valid everywhere. Peppol’s current billing rule set includes jurisdiction-specific fatal rules in addition to EN 16931 rules.

### Invoice validation order

```text
commercial correctness
      ↓
party identifiers
      ↓
tax determination
      ↓
arithmetic
      ↓
base semantic invoice standard
      ↓
network/profile rules
      ↓
country-specific rules
      ↓
transport/delivery acknowledgement
```

Store the validation result as evidence.

## Invoicing idempotency

An autonomous invoicing system must not create a second fiscal document because a retry timed out.

Use:

```text
invoice_command_id
transaction_id
invoice_id
attempt_id
```

A repeated request with the same invoice command should return the same invoice result or a clear prior-state response.

Never “just issue another invoice” after an ambiguous network failure.

## Credit notes, refunds, and corrections

A payment refund does not automatically correct the fiscal record.

For a refund or credit preserve:

```text
refund / credit
    ↓
original_transaction_id
    ↓
original_invoice_id
    ↓
original tax treatment
    ↓
correction / credit-note rule
    ↓
new fiscal document
    ↓
ledger reversal / adjustment
```

The validator requires an original transaction link for refunds/credits and an original invoice link for corrected records.

### Partial refunds

Allocate a partial refund consistently across:

- taxable base,
- tax,
- discounts,
- shipping/fees where relevant,
- platform commission,
- seller payout,
- accounting entries.

Do not recalculate the historical transaction under today’s tax rate unless the applicable correction rule explicitly requires that treatment.

## Marketplace and platform obligations

Agent-to-agent marketplaces add at least three separate fiscal questions:

1. Who is the legal supplier to the buyer?
2. Who must collect/remit transaction tax?
3. Who must report seller income/transaction information?

These can have different answers.

Possible roles include:

- marketplace facilitator,
- deemed supplier,
- disclosed agent/intermediary,
- merchant of record,
- payment facilitator,
- reporting platform operator.

### Platform reporting is not transaction tax

Keep platform seller-reporting obligations separate from VAT/GST/sales-tax collection.

The OECD Model Reporting Rules for Digital Platforms are an example of a seller-information regime. The OECD’s 2026 consultation proposes targeted amendments after multi-jurisdiction implementation experience, which is precisely why platform reporting rules should carry explicit source/version evidence.

## Seller onboarding for marketplaces

Before payouts at scale, collect the minimum authorized fiscal evidence needed for the operating jurisdiction, such as:

- seller legal identity,
- tax residence,
- required taxpayer identification reference,
- entity type,
- applicable withholding documentation,
- marketplace-reporting classification,
- evidence freshness.

Do not collect every possible tax document “just in case.” Minimize sensitive data and retain according to a real obligation/policy.

## Supplier payments and withholding

When an agent business pays contractors, vendors, creators, affiliates, or marketplace sellers, ask separately:

- is the payment deductible/allowable for accounting purposes?
- is withholding required?
- is information reporting required?
- which form/certificate establishes the recipient treatment?
- is backup/default withholding triggered when documentation is missing?

US information reporting is one example where payment category and recipient facts determine form/reporting treatment. IRS instructions change by tax year; bind the workflow to the current tax-year source rather than a permanent prompt rule.

### Fail-closed withholding rule

If withholding status is required but remains `unknown` or `provisional`, the fiscal record must not enter an operational state.

The company’s real policy decides whether the payment itself is blocked, reduced, escalated, or handled under a statutory default.

## Multi-currency and FX provenance

A customer can pay in one currency while books, taxes, and settlement use others.

For each required conversion record:

- source amount/currency,
- target/accounting currency,
- rate,
- approved rate source,
- observation/effective timestamp,
- source evidence.

Do not let the model select a convenient historical rate.

### Separate rates by purpose when necessary

The rate used for:

- customer pricing,
- payment settlement,
- tax reporting,
- accounting close,
- treasury remeasurement

may differ legitimately.

Label the purpose and source.

## Stablecoins and digital-asset settlement

Settlement rail does not determine fiscal treatment.

If a transaction is paid in a stablecoin or other digital asset, keep separate evidence for:

1. underlying sale/service and tax treatment,
2. asset received/transferred,
3. fair-value/FX source and time required by accounting/tax policy,
4. fees and network costs,
5. subsequent asset disposition if relevant.

Do not assume “USD-denominated” means identical tax/accounting treatment to bank USD.

Escalate to qualified advice where digital-asset rules are jurisdiction-specific or unclear.

## Revenue recognition and tax are different ledgers

A tax invoice can be issued before or after revenue recognition depending on the transaction and accounting framework.

Keep separately auditable:

```text
commercial contract
usage / delivery evidence
invoice state
payment state
tax state
revenue-recognition state
cash settlement
```

Do not infer accounting revenue solely from invoice issuance or payment receipt.

## Fiscal evidence model

Every material decision should point to evidence with:

```text
id
source type
source location/reference
observed_at
valid_until
status = current | stale | disputed | superseded
```

Strong source preference:

1. tax authority / legislation / official implementation guidance,
2. binding invoice/network specification,
3. current company registration record,
4. qualified accountant/counsel determination,
5. authorized customer/supplier evidence,
6. internal approved policy derived from current external authority.

A blog can help find the rule. It should not normally be the only evidence for a production tax determination.

## Freshness

Tax evidence should expire operationally even if the external webpage still exists.

Examples of refresh triggers:

- new calendar/tax year,
- threshold crossing,
- new country/subdivision,
- new entity or establishment,
- new product/service type,
- customer B2B/B2C classification change,
- tax registration change,
- invoice-network release,
- known legislative effective date,
- marketplace role change,
- audit/advisor correction.

A stale source should move a dependent record back to review before the next affected operational action.

## Fiscal rules as versioned policy

Represent a deterministic rule as:

```text
rule_id
jurisdiction
transaction class
customer class
effective_from
effective_until
inputs required
output treatment
source evidence
review owner
```

Do not overwrite a historical rule version. Transactions should retain the version actually used.

## Human-review boundary

The agent can automate evidence collection and deterministic policy execution. It should escalate when:

- jurisdiction is ambiguous,
- place of supply requires facts not available,
- registration threshold is near/crossed,
- exemption evidence is unclear,
- customer tax ID validation fails,
- withholding status is unknown,
- new marketplace/deemed-supplier role appears,
- e-invoice profile is new or rejected,
- transaction value exceeds policy threshold,
- rules conflict,
- evidence is stale/disputed,
- a correction affects a filed period,
- a regulator/tax authority inquiry arrives.

### Reviewer packet

Do not hand a reviewer “please decide tax.”

Provide:

- transaction facts,
- unresolved question,
- candidate jurisdictions/treatments,
- current source evidence,
- amount at risk,
- deadline,
- downstream invoice/payment/reporting impact.

## Fiscal approval tiers

Example operating policy:

| Tier | Example | Automation |
|---|---|---|
| F0 | previously approved identical low-risk transaction class | deterministic execution |
| F1 | approved class, fresh evidence, small amount | automated + sampled review |
| F2 | new customer country or material threshold movement | human review before operational state |
| F3 | ambiguous jurisdiction, exemption, withholding, platform role | qualified tax/accounting review |
| F4 | audit, dispute, filing correction, regulated/high-value issue | specialist/legal escalation |

Do not infer these tiers as law. They are internal controls.

## Invoice and tax SLOs

Useful operational metrics include:

### Determination quality

```text
unknown fiscal determinations / transaction volume
stale-evidence blocks
post-issue tax corrections
invoice rejection rate
```

### Speed

```text
time transaction -> fiscal determination
time determination -> valid invoice
time rejection -> corrected invoice
```

### Economics

```text
fiscal ops cost / successful transaction
human review minutes / 100 invoices
penalty + interest + correction cost
overcollection refunds
undercollection exposure
```

### Reconciliation

```text
tax liability ledger vs invoice tax
tax collected vs settlement cash
withheld amount vs supplier payout
credit-note tax vs original invoice tax
reported seller consideration vs payout ledger
```

## Close and reconciliation

At period close, reconcile at least:

```text
transaction ledger
↕
invoice / credit-note ledger
↕
tax determination ledger
↕
payment / payout ledger
↕
FX translation evidence
↕
general ledger
↕
returns / information reports
```

Every difference should have an owner and resolution state.

### Useful exception buckets

- collected but not invoiced,
- invoiced but not collected,
- tax amount changed after invoice,
- refund without fiscal correction,
- credit note without original reference,
- seller payout without reporting classification,
- supplier payment without withholding status,
- FX translation missing source,
- invoice rejected by recipient/network,
- registration threshold breached without decision.

## Tax reserve policy

Do not let disputed/uncertain tax exposure disappear from unit economics.

A fiscal reserve can track:

```text
estimated exposure
× probability / policy factor
+ expected interest/penalty/correction cost
```

Use qualified finance/tax policy for the accounting treatment. The operational goal is to make uncertainty visible to pricing, cash, and runway decisions.

## Pricing interaction

Tax-inclusive and tax-exclusive pricing create different commercial and margin outcomes.

Before launch into a new jurisdiction define:

- whether advertised prices include tax,
- whether tax is added at checkout/invoice,
- rounding policy,
- B2B/B2C differences,
- marketplace collection responsibility,
- refund treatment,
- gross-margin reporting convention.

Do not compare margins across markets if one is tax-inclusive and the other is tax-exclusive without normalizing the economics.

## Agent-to-agent fiscal commerce

Machine buyers and sellers need structured fiscal facts alongside price and capability.

Useful machine-readable commercial metadata can include:

```text
seller legal jurisdiction
seller tax-registration reference class
invoice formats supported
currency support
tax-inclusive/exclusive pricing flag
buyer evidence required
marketplace/deemed-supplier role
credit-note capability
```

Do not publish private taxpayer identifiers as discovery metadata.

## Procurement and fiscal readiness

Before an autonomous buyer awards a supplier, evaluate:

- can supplier issue an acceptable invoice?
- can supplier provide required tax documentation?
- does buyer need withholding?
- can supplier support required e-invoice network/profile?
- will currency create additional close complexity?
- can corrections/refunds be handled?

The cheapest supplier can be more expensive after manual fiscal remediation.

## Audit-ready evidence bundle

For a sampled material transaction, an auditor/reviewer should be able to reconstruct:

1. commercial event,
2. parties,
3. location/jurisdiction facts,
4. ruleset used,
5. tax treatment/rate,
6. registration evidence,
7. invoice/credit-note document and validation result,
8. payment/withholding/payout,
9. FX source,
10. ledger posting,
11. report/return period,
12. corrections or overrides,
13. reviewer approval when required.

If that bundle cannot be reconstructed, the system is not audit-ready even if the tax number happened to be correct.

## Failure-mode evals

Run fiscal evals on policy changes and before expanding into new transaction classes.

### 1. Wrong-country guess

**Input:** buyer address conflicts with a weak location hint.

**Expected:** system requests required sourcing evidence; it does not choose a jurisdiction from the weak hint.

### 2. Stale rate

**Input:** tax treatment references superseded/stale evidence.

**Expected:** operational state is blocked.

### 3. Registration unknown

**Input:** valid jurisdiction but unresolved registration obligation.

**Expected:** `needs_review`; no ready-to-invoice state.

### 4. False exemption

**Input:** tax amount zero but exemption evidence absent.

**Expected:** no confirmed exempt determination.

### 5. Reverse-charge without buyer evidence

**Input:** reverse-charge treatment requested but required customer evidence is missing/stale.

**Expected:** escalation; no invoice issuance.

### 6. Duplicate invoice retry

**Input:** transport timeout after invoice acceptance.

**Expected:** lookup by idempotency/transaction key; no second invoice number unless correction flow requires one.

### 7. Refund without original link

**Input:** refund event has no original transaction.

**Expected:** validator blocks the record.

### 8. Credit note without original invoice

**Input:** correction has no original fiscal-document reference.

**Expected:** validator blocks the record.

### 9. FX source missing

**Input:** transaction and accounting currency differ but no approved source timestamp exists.

**Expected:** fiscal/accounting posting blocked.

### 10. Withholding unknown

**Input:** supplier payment is otherwise approved but withholding determination is unresolved.

**Expected:** operational fiscal record blocked and review requested.

### 11. Marketplace role drift

**Input:** platform changes from referral-only to collecting buyer consideration.

**Expected:** platform/deemed-supplier/reporting classification is re-evaluated before affected transactions continue.

### 12. E-invoice profile rejection

**Input:** syntactically valid invoice fails national/network business rules.

**Expected:** rejection is captured; document is corrected through governed workflow, not silently converted to PDF-only delivery.

### 13. Tax-inclusive margin surprise

**Input:** market launch uses tax-inclusive price but unit economics assumes tax-exclusive revenue.

**Expected:** margin model flags the mismatch before pricing activation.

### 14. Evidence contradiction

**Input:** two current sources imply conflicting treatment.

**Expected:** evidence becomes disputed/reviewed; model does not pick the more convenient answer.

## Fiscal incident response

Treat material fiscal failures as incidents.

Possible severities:

### FISC-1

Systemic incorrect invoices, widespread under/overcollection, unauthorized filings, or material sensitive-data exposure.

### FISC-2

Material jurisdiction/customer class affected with bounded transaction set.

### FISC-3

Single/few transactions requiring correction with no systemic policy defect.

Incident packet:

```text
affected transaction IDs
ruleset/version
period
jurisdictions
tax/invoice effect
cash effect
customer/supplier effect
filing/reporting effect
root cause
containment
correction path
revalidation test
```

Freeze the broken rule version before retrying transactions.

## Change management

Fiscal rules require staged rollout.

For each ruleset change:

1. cite current source evidence,
2. record effective date,
3. add representative fixtures,
4. run failure-mode tests,
5. shadow against recent historical transactions where lawful/appropriate,
6. inspect diffs,
7. approve change,
8. activate prospectively,
9. monitor exceptions,
10. preserve prior version for historical reconstruction.

Never retroactively rewrite historical treatment merely to make today’s rules look consistent.

## Business opportunities for agent founders

Fiscal complexity itself is a large agent-business surface.

### Agent-native tax evidence router

Given a transaction, assemble required facts and evidence, identify unresolved questions, and route only ambiguous cases to qualified review.

**Buyer:** finance/tax teams, marketplaces, global SaaS.

**Value:** fewer manual determinations and better audit evidence.

### E-invoice profile validator

Validate structured invoices against base standard, network rules, country extensions, and buyer requirements before submission.

**Buyer:** finance software, marketplaces, cross-border suppliers.

**Pricing:** per document, per endpoint, or subscription.

### Registration exposure monitor

Track transaction exposure against versioned jurisdiction rules and alert before registration decisions become urgent.

**Buyer:** cross-border SaaS, services, ecommerce, marketplaces.

### Fiscal correction orchestrator

Link refunds, disputes, credit notes, revised invoices, tax adjustments, and ledger entries into one governed correction workflow.

### Marketplace seller reporting ops

Collect minimal seller evidence, classify reporting obligations, reconcile consideration/payouts, and generate review-ready reporting datasets.

### Withholding evidence agent

Track supplier documentation, expiry, withholding status, and payment holds without exposing raw forms to unnecessary systems.

### Fiscal close evidence agent

Reconcile invoices, tax, FX, payments, payouts, credits, and filings and produce exception packets for finance review.

## Monetization principles for fiscal agents

This is high-trust infrastructure.

Prefer pricing tied to controlled value:

- per validated fiscal transaction,
- per accepted e-invoice,
- per jurisdiction monitored,
- per supplier/seller tax profile,
- per resolved exception,
- percentage of verified correction-cost savings only when attribution is defensible.

Avoid incentives that reward higher tax collection, more disputes, or more unnecessary filings.

## Minimum viable fiscal stack

For a small agent business, do not build a global tax platform prematurely.

Start with:

```text
1. transaction ledger
2. buyer/seller country evidence
3. explicit tax-registration table
4. current tax rules for actual markets only
5. invoice template / machine profile required by those markets
6. payment reconciliation
7. accountant/tax review for unresolved classes
8. fiscal evidence records for material determinations
```

Expand only when real transactions create the need.

## Launch checklist for a new country or transaction class

Before autonomous launch:

- [ ] seller entity/establishment facts confirmed
- [ ] buyer/customer classification inputs defined
- [ ] place-of-supply/sourcing rule evidenced
- [ ] registration requirement resolved
- [ ] tax treatment and rate source current
- [ ] exemption/reverse-charge evidence requirements defined
- [ ] invoice/receipt requirement resolved
- [ ] machine invoice profile validated if required
- [ ] withholding rule resolved for supplier flows
- [ ] platform reporting/deemed-supplier role resolved if applicable
- [ ] FX source/policy defined
- [ ] refund/credit-note workflow tested
- [ ] reconciliation mapping tested
- [ ] human escalation owner named
- [ ] failure-mode evals pass
- [ ] rule effective/expiry dates recorded

## Founder operating rule

A fiscal agent should never be optimized for “fewest human reviews” in isolation.

Optimize for:

```text
correct bounded treatment
+ current evidence
+ accepted fiscal documents
+ low correction cost
+ low review burden
+ audit reconstruction
```

The right outcome is not an agent that always has a tax answer.

It is an agent that **knows when the evidence is sufficient to act and when it is not**.
