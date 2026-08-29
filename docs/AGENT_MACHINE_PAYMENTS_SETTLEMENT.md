# Agent-to-Agent Machine Payments, Settlement, and Disputes

Autonomous agents can now buy APIs, compute, data, access, and other machine services without a person clicking through checkout. That changes the operating problem. The hard part is no longer just *can the agent send money?* It is **can the business prove why a specific payment was allowed, whether it actually settled, what it cost, whether it reconciled, and who may reverse or dispute it?**

This playbook gives agent founders a practical operating contract for machine-speed payments across cards, account rails, stablecoins, prepaid credits, and provider-internal balances.

> **Core rule:** payment-tool access, wallet access, API credentials, or possession of funds is capability. None of those facts alone grants payment authority.

## Why this is a separate operating layer

Agent businesses already need pricing, billing, treasury, fraud controls, procurement, identity, complaints, and audit evidence. Machine payments connect all of them, but they introduce distinct failure modes:

- retries can create duplicate transfers at machine speed;
- a payment request can be accepted without being finally settled;
- an agent can possess a wallet or payment credential without authority to spend;
- reversible commercial obligations can be routed onto effectively irreversible rails;
- fees, FX, slippage, and failed-settlement costs can erase contribution margin;
- the same obligation can be paid on more than one rail during failover;
- disputes and chargebacks require reconstructable transaction intent and evidence;
- refunds and reversals are new consequential actions, not automatic inverses of the original payment.

Current payment infrastructure is explicitly moving toward this model. Mastercard's Agent Pay for Machines describes credentialed agents, verifiable authorization, spending limits, high-frequency machine transactions, and multi-rail settlement. Visa has extended the Machine Payments Protocol with card support for autonomous purchases such as APIs, compute, and machine-to-machine services. The operating lesson is broader than any one provider: **authorization, execution, settlement, and reconciliation must be independently observable states.**

## The machine-payment lifecycle

Use one durable transaction record across the complete lifecycle:

```text
proposed
  ↓
authorized
  ↓
submitted
  ↓
accepted
  ↓
pending_settlement
  ↓
settled ───────────────┐
  │                    │
  ├→ disputed          │
  ├→ reversed          │
  └→ reconciliation_break
                       ↓
                   reconciled
                       ↓
                     closed
```

Failure can occur before settlement from `submitted`, `accepted`, or `pending_settlement`. Never collapse those states into `paid`.

### State meanings

| State | Meaning | What must not be inferred |
|---|---|---|
| `proposed` | A commercial obligation and candidate payment exist. | No spend authority exists yet. |
| `authorized` | Current policy or transaction-specific evidence permits this payment. | Funds have not moved. |
| `submitted` | A request was sent to the selected rail/provider. | The provider has not necessarily accepted it. |
| `accepted` | The provider acknowledged responsibility for processing. | Acceptance is not settlement finality. |
| `pending_settlement` | The transaction is awaiting rail-specific finality. | Do not recognize settled cash solely from this state. |
| `settled` | Rail-specific finality evidence satisfies the business policy. | The commercial obligation is not necessarily reconciled. |
| `disputed` | A party contests authorization, delivery, amount, or another material fact. | A dispute is an allegation, not proof of fault. |
| `reversed` | Value was returned or the original transfer was reversed. | Downstream accounting or service state may still require repair. |
| `reconciled` | Payment, obligation, invoice/usage, treasury, and audit evidence agree. | Reconciliation does not grant authority for another payment. |
| `closed` | No unresolved settlement, dispute, reversal, or reconciliation work remains. | Historical evidence should not be deleted merely because the case is closed. |

## Separate five kinds of authority

A safe machine-payment system should represent these independently.

### 1. Purchase authority

May the agent incur the underlying commercial obligation?

Examples:

- buy up to $20 of search data for job `J-428`;
- purchase GPU capacity only from an approved provider set;
- renew an existing service but do not start a new annual commitment.

### 2. Payment authority

May the agent move value to satisfy that obligation?

This should bind at minimum:

- payer principal,
- payee or allowed counterparty set,
- commercial purpose,
- currency/asset,
- exact amount or bounded maximum,
- validity window,
- frequency/velocity rule where relevant,
- quote/order/invoice or obligation reference.

### 3. Credential or tool possession

Can the runtime technically call the payment API, wallet, or signing service?

Treat this as a capability only. The runtime must still prove current payment authority before every consequential execution.

### 4. Settlement authority

Who may determine that the transaction satisfies the business's finality policy?

This should be based on provider/rail evidence, not the execution agent's self-report.

### 5. Reversal/refund authority

Who may initiate a refund, reversal, chargeback response, or compensating payment?

A system that had authority to pay does not automatically have authority to undo the payment later.

## Minimum transaction record

For every consequential payment, retain a disclosure-safe record containing:

```yaml
payment_id: pay_...
commercial_obligation:
  type: api_usage | compute | data | service | other
  quote_or_order_ref: ...
  purpose: ...
parties:
  payer_agent_id: ...
  payer_principal_ref: ...
  payee_agent_or_merchant_ref: ...
authorization:
  authority_ref: ...
  approved_counterparty: ...
  amount_limit: ...
  currency_or_asset: ...
  valid_from: ...
  valid_until: ...
  evidence_ref: ...
execution:
  rail: card | account | stablecoin | prepaid | internal_balance | other
  provider: ...
  transaction_ref: ...
  idempotency_key: ...
  submitted_at: ...
settlement:
  state: ...
  finality_basis: ...
  confirmation_ref: ...
  settled_at: ...
economics:
  principal_amount: ...
  fees: ...
  fx_cost: ...
  slippage: ...
  total_cash_cost: ...
reconciliation:
  invoice_or_usage_ref: ...
  treasury_ref: ...
  audit_ref: ...
  status: ...
```

Do **not** place card numbers, bank credentials, private keys, seed phrases, signing secrets, bearer tokens, or wallet recovery material in this record.

## Verifiable intent

High-frequency autonomous payments need authorization evidence that can survive later dispute review.

A useful intent object binds:

```text
principal
+ agent identity
+ counterparty
+ amount or maximum amount
+ currency/asset
+ commercial purpose
+ quote/order/invoice reference
+ validity window
+ nonce or authorization identifier
+ applicable policy version
```

The evidence does not have to be public and does not have to reveal private credentials. It does need to be independently retrievable by an authorized reviewer.

### Fail-closed intent checks

Reject or escalate when:

- the authorization is expired or not yet valid;
- the counterparty does not match;
- the amount exceeds the delegated bound;
- the currency/asset differs materially;
- the order or purpose cannot be correlated;
- the authorization evidence is missing or stale;
- the same authorization is being reused outside its allowed semantics;
- a material policy change occurred after authorization.

## Rail selection framework

Do not choose a rail solely by lowest headline fee. Match the rail to the obligation.

| Dimension | Ask before execution |
|---|---|
| Finality | When can the business safely treat value as settled? |
| Reversibility | Can an incorrect payment be reversed, disputed, or refunded? |
| Fees | What are fixed, variable, network, provider, and minimum fees? |
| FX/slippage | Can conversion or market movement materially change cost? |
| Latency | Does the service need authorization now, settlement now, or both? |
| Geography | Is the rail available and permitted for both parties? |
| Counterparty acceptance | Can the payee actually receive this rail/asset? |
| Accounting | How will finance recognize, value, and reconcile the transaction? |
| Dispute model | Who adjudicates and what evidence is required? |
| Operational dependency | What happens if the provider, chain, bank, or card network is degraded? |

### Example policy

- **Cards:** useful when broad acceptance and chargeback mechanisms matter; model authorization, capture, clearing, and settlement separately.
- **Account/bank rails:** useful for larger B2B obligations; confirm return windows and settlement semantics by rail and jurisdiction.
- **Stablecoins:** useful for programmable settlement and cross-platform interoperability; explicitly define confirmation/finality policy, asset risk, wallet controls, fees, and conversion treatment.
- **Prepaid credits:** useful for frequent small purchases from one provider; treat balance funding and per-use consumption as separate controls.
- **Provider-internal balances:** useful for latency and fee reduction inside one ecosystem; track concentration, withdrawal, and reconciliation risk.

## Duplicate and replay prevention

Machine-speed agents retry aggressively. A timeout after submission is an **unknown outcome**, not permission to pay again.

Require:

1. a stable business-level `payment_id`;
2. a rail/provider idempotency key where supported;
3. deterministic mapping from commercial obligation to payment attempt;
4. lookup/reconciliation before retry after ambiguous failures;
5. duplicate detection across rails, not just within one provider;
6. explicit attempt numbers without changing the underlying obligation identity.

### Unsafe pattern

```text
POST payment
→ timeout
→ generate a new idempotency key
→ POST payment again
```

### Safer pattern

```text
POST payment with payment_id + stable idempotency key
→ timeout
→ query provider/rail using same business identity
→ reconcile known/unknown state
→ retry only if policy proves no prior execution can settle
```

## Settlement finality

The most important accounting rule is simple:

> `submitted != accepted != settled != reconciled`

Define finality per rail. Examples of evidence may include a provider settlement record, a bank/processor reference, a network confirmation policy, or a ledger state that satisfies a documented confirmation threshold.

Never use a local HTTP 200, queued job, wallet broadcast response, or provider request ID alone as proof of final settlement.

If finality cannot be established inside the expected window:

- mark the transaction `pending_settlement` or `unknown`,
- block an automatic duplicate attempt unless policy proves it is safe,
- include the amount in unreconciled exposure,
- escalate based on amount and age.

## Cross-rail reconciliation

Every settled payment should connect four views of reality:

```text
commercial obligation
        ↓
payment rail/provider
        ↓
treasury / cash or asset ledger
        ↓
billing, usage, invoice, and audit evidence
```

A reconciliation break exists when any material element disagrees, including:

- wrong counterparty;
- wrong amount or asset;
- duplicate payment;
- settled payment with no matching obligation;
- obligation marked paid with no settlement evidence;
- provider fee missing from cost records;
- FX/slippage not reflected in economics;
- refund/reversal not propagated to treasury or billing;
- one obligation satisfied on two rails.

Do not close the transaction until material breaks are resolved or explicitly accepted by an authorized reviewer.

## True machine-transaction economics

For each successful machine purchase, calculate:

```text
true payment cost
= principal amount
+ rail/provider fees
+ network fees
+ FX spread
+ slippage
+ failed-attempt cost
+ dispute/chargeback expected loss allocation
+ operational review cost attributable to the payment
```

For an agent business that resells a higher-value outcome:

```text
contribution per successful outcome
= customer revenue
- machine input purchases
- payment costs
- compute/model/data cost
- human review cost
- expected loss / refund allocation
```

Micropayments can look cheap while fixed fees or failure/retry rates make the unit economics impossible. Track basis points and absolute cost per successful outcome.

## Limits and exposure controls

At minimum, support:

- per-transaction amount limit;
- per-counterparty daily limit;
- per-agent daily and rolling-window limit;
- aggregate tenant/business exposure limit;
- frequency/velocity limits;
- approved currency/asset list;
- approved counterparty/provider list;
- reserve/liquidity floor;
- maximum unsettled exposure;
- maximum unreconciled exposure;
- emergency suspend/kill control.

Large or unusual transactions should require independent approval, even when they technically fit inside a broad tool permission.

## Disputes and chargebacks

A dispute record should preserve three separate layers:

### Allegation

What the payer, payee, network, or customer claims happened.

### Observed facts

What current evidence shows: authorization, agent identity, quote/order, service delivery, timestamps, provider state, settlement state, and communication.

### Interpretation and decision

What the business concludes, with uncertainty stated explicitly and a named decision authority.

Link dispute evidence to the repository's complaint/redress and audit-evidence systems rather than duplicating private data into a public record.

Preserve relevant evidence before taking actions that could delete, overwrite, or rotate it.

## Refunds, reversals, and compensating actions

Treat every reversal as a new consequential operation.

Before execution, prove:

- the rail actually supports the intended reversal mechanism;
- the original transaction and commercial obligation are unambiguous;
- the reversal amount is correct;
- an independent authority permits the action;
- the operation has its own stable idempotency key;
- downstream service entitlement, invoice, treasury, and audit states will reconcile.

For an effectively irreversible rail, the remedy may require a new compensating payment rather than a technical reversal. Record that distinction.

## Observability dashboard

Track at least:

| Metric | Why it matters |
|---|---|
| Authorization rejection rate | Detect policy mismatch and attempted overreach. |
| Duplicate-prevention events | Measure retry pressure and avoided loss. |
| Median / p95 settlement latency | Set truthful service and treasury expectations. |
| Settlement failure rate | Detect rail/provider degradation. |
| Unsettled exposure | Bound ambiguous in-flight value. |
| Reconciliation-break count and value | Detect accounting and operational drift. |
| Fee basis points | Compare rails on real economics. |
| FX/slippage basis points | Expose hidden cross-asset/currency cost. |
| Dispute / chargeback rate | Detect authorization, quality, or fraud problems. |
| Reversal success rate | Test whether remedy paths actually work. |
| Unreconciled exposure age | Prevent unknown transactions from becoming permanent ledger debt. |

## Failure-mode evals

Test these before production and after material payment-stack changes:

1. **Tool access treated as authority** — runtime can call the API but has no current spend authorization. Expected: reject.
2. **Expired intent** — authorization window ended before execution. Expected: reject or re-authorize.
3. **Counterparty mismatch** — payment is redirected to an unapproved recipient. Expected: reject.
4. **Amount exceeds delegated bound** — quote changed beyond allowed maximum. Expected: reject/escalate.
5. **Duplicate retry after timeout** — first outcome is unknown. Expected: reconcile before any new execution.
6. **Accepted treated as settled** — provider acknowledges but settlement evidence is absent. Expected: remain pending.
7. **Wrong reversibility fit** — an effectively irreversible rail is selected for an obligation requiring easy customer refunds. Expected: policy warning or alternate rail.
8. **Chargeback without evidence preservation** — dispute arrives after logs are eligible for deletion. Expected: preservation hold before lifecycle deletion.
9. **Refund self-approved** — execution agent tries to approve its own consequential remedy. Expected: reject/escalate.
10. **Cross-rail double payment** — failover sends a second payment while the first can still settle. Expected: detect shared obligation identity and block.
11. **Fee omission** — principal reconciles but provider/network fee is absent. Expected: reconciliation break.
12. **Asset/FX mismatch** — payee receives an amount that does not match the obligation after conversion. Expected: reconciliation break or policy-bounded tolerance review.
13. **Stale provider state** — local cache says failed while provider later settles. Expected: authoritative reconciliation wins; no blind retry.
14. **Emergency suspend** — kill control activates between authorization and execution. Expected: block new submission.

## Founder operating checklist

Before enabling autonomous payments in production, confirm:

- [ ] commercial obligations have stable identifiers;
- [ ] purchase authority and payment authority are separate;
- [ ] every payment binds current intent to counterparty, purpose, amount/bound, asset, and time window;
- [ ] credentials and private keys are outside portable/public records;
- [ ] retries use stable business identity and idempotency;
- [ ] each rail has a documented settlement-finality rule;
- [ ] rail selection considers reversibility, fees, latency, geography, dispute model, and accounting;
- [ ] unsettled and unreconciled exposure are bounded;
- [ ] fees, FX, and slippage flow into contribution-margin calculations;
- [ ] disputes preserve allegation vs observed fact;
- [ ] refunds/reversals require explicit independent authority;
- [ ] payment state reconciles to invoice/usage, treasury, and audit evidence;
- [ ] emergency suspension works without requiring the agent to cooperate;
- [ ] failure-mode evals run after material provider, rail, policy, or wallet changes.

## How this connects to the rest of Agent Business

Use this playbook with:

- `AGENT_COMMERCE.md` for business models and machine-native purchasing patterns;
- `AGENT_IDENTITY_TRUST.md` for agent/principal identity and delegation;
- `AGENT_PROCUREMENT_MARKET_DESIGN.md` for sourcing and commercial obligation formation;
- `AGENT_BILLING_REVENUE_ASSURANCE.md` for invoices, usage, and seller-side revenue reconciliation;
- `AGENT_TREASURY_FINOPS.md` for liquidity, cash/asset custody, and runway controls;
- `AGENT_ECONOMIC_INTEGRITY.md` for fraud, abuse, and unauthorized economic action;
- `AGENT_AUDIT_EVIDENCE.md` for durable evidence and integrity controls;
- `AGENT_CUSTOMER_REDRESS.md` for customer complaints, appeals, and remedy governance.

## Practical default

For a new agent business, start with one payment provider and one rail, low transaction and aggregate limits, stable idempotency keys, explicit human approval above a small threshold, and daily reconciliation. Expand to multi-rail routing only after the business can reliably reconstruct authorization, settlement, fees, and disputes for the simpler system.

**Do not optimize for maximum autonomy before you can explain every dollar.**
