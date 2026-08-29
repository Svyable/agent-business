# Agent Machine Payments — Operational Entry Point

Use this page as the stable navigation entry for autonomous payment operations. The full human-operable contract is in [`AGENT_MACHINE_PAYMENTS_SETTLEMENT.md`](AGENT_MACHINE_PAYMENTS_SETTLEMENT.md); the executable layer is intentionally separate so agents can validate transaction state without parsing prose.

## Start safely

1. Copy `templates/MACHINE_PAYMENT_RECORD.json` for each commercial obligation.
2. Keep execution, settlement, reversal/refund, and closure authority `false` until independently evidenced.
3. Bind the intended payee, amount limit, currency/asset, and validity window to current authorization evidence.
4. Preserve one stable `payment_id` and idempotency key across ambiguous retries; a timeout is not permission to pay again.
5. Never treat `submitted` or `accepted` as settlement. Record rail/provider finality evidence before claiming `settled`.
6. Reconcile principal, fees, FX/slippage, invoice or usage, treasury, and audit evidence before closure.
7. Treat every reversal/refund as a new consequential action with separate authority and idempotency.

Validate a record with:

```bash
python scripts/validate_machine_payment.py templates/MACHINE_PAYMENT_RECORD.json
```

The starter is deliberately zero-authority and zero-value. It is safe to copy, but it is not authorization to move funds.

## Machine assets

- Schema: `schemas/machine-payment-record.schema.json`
- Starter: `templates/MACHINE_PAYMENT_RECORD.json`
- Validator: `scripts/validate_machine_payment.py`
- Failure-mode tests: `tests/test_machine_payment.py`

## Non-negotiable boundaries

Payment API access, wallet access, signing capability, provider acceptance, and possession of funds are capabilities or observations; none independently proves current payment authority or settlement finality. Do not place card data, bank credentials, private keys, seed phrases, bearer tokens, signing secrets, or other payment credentials in portable/public records.

For lifecycle semantics, rail selection, exposure controls, disputes, reversals, true transaction economics, observability, and the complete failure-mode catalog, use the full [machine-payments settlement playbook](AGENT_MACHINE_PAYMENTS_SETTLEMENT.md).
