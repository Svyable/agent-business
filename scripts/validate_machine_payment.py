#!/usr/bin/env python3
"""Validate Agent Business machine-payment records without third-party packages."""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime
from pathlib import Path

PROHIBITED = {
    "password", "secret", "api_key", "access_token", "refresh_token",
    "authorization_header", "private_key", "seed_phrase", "card_number",
    "cvv", "bank_credentials", "bearer_token"
}
EXECUTED_STATES = {"submitted", "accepted", "pending_settlement", "settled", "disputed", "reversed", "reconciliation_break", "reconciled", "closed"}
SETTLED_STATES = {"settled", "disputed", "reversed", "reconciliation_break", "reconciled", "closed"}


def fail(message: str) -> None:
    raise SystemExit(f"machine-payment validation failed: {message}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path}: {exc}")
    if not isinstance(value, dict):
        fail("record must be a JSON object")
    return value


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        fail(f"{label} must be ISO-8601")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be ISO-8601")
    if parsed.tzinfo is None:
        fail(f"{label} must include timezone")
    return parsed


def scan(value: object, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PROHIBITED:
                fail(f"prohibited sensitive field: {path}.{key}")
            scan(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan(child, f"{path}[{index}]")


def evidence_map(items: object) -> dict[str, dict]:
    if not isinstance(items, list):
        fail("evidence must be a list")
    out: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            fail("evidence entries must be objects")
        evidence_id = item.get("id")
        if not isinstance(evidence_id, str) or not evidence_id:
            fail("evidence ids must be non-empty")
        if evidence_id in out:
            fail(f"duplicate evidence id: {evidence_id}")
        parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        if not isinstance(item.get("reference"), str) or not item.get("reference"):
            fail(f"evidence {evidence_id}.reference required")
        out[evidence_id] = item
    return out


def current_refs(label: str, refs: object, evidence: dict[str, dict], required: bool = False) -> None:
    if not isinstance(refs, list):
        fail(f"{label}.evidence_ids must be a list")
    if required and not refs:
        fail(f"{label} requires current evidence")
    for ref in refs:
        if ref not in evidence:
            fail(f"{label} references unknown evidence: {ref}")
        if evidence[ref].get("status") != "current":
            fail(f"{label} requires current evidence: {ref}")


def number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
        fail(f"{label} must be a finite non-negative number")
    return float(value)


def validate(record: dict) -> None:
    required = {
        "schema_version", "payment_id", "status", "updated_at", "commercial_obligation", "parties",
        "authorization", "execution", "settlement", "economics", "reconciliation", "dispute",
        "reversal", "authority", "evidence", "privacy"
    }
    missing = sorted(required - set(record))
    if missing:
        fail("missing required fields: " + ", ".join(missing))
    if record.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    parse_time(record.get("updated_at"), "updated_at")
    scan(record)

    status = record.get("status")
    valid_statuses = {"proposed", "authorized", "submitted", "accepted", "pending_settlement", "settled", "failed", "disputed", "reversed", "reconciliation_break", "reconciled", "closed"}
    if status not in valid_statuses:
        fail("status is invalid")

    obligation = record["commercial_obligation"]
    parties = record["parties"]
    auth = record["authorization"]
    execution = record["execution"]
    settlement = record["settlement"]
    economics = record["economics"]
    reconciliation = record["reconciliation"]
    dispute = record["dispute"]
    reversal = record["reversal"]
    authority = record["authority"]
    privacy = record["privacy"]
    evidence = evidence_map(record["evidence"])

    for label, value in (("commercial_obligation.reference", obligation.get("reference")), ("commercial_obligation.purpose", obligation.get("purpose")), ("parties.payer_agent_id", parties.get("payer_agent_id")), ("parties.payer_principal_ref", parties.get("payer_principal_ref")), ("parties.payee_ref", parties.get("payee_ref")), ("authorization.authority_ref", auth.get("authority_ref")), ("authorization.approved_payee_ref", auth.get("approved_payee_ref")), ("authorization.currency_or_asset", auth.get("currency_or_asset")), ("execution.currency_or_asset", execution.get("currency_or_asset")), ("execution.idempotency_key", execution.get("idempotency_key"))):
        if not isinstance(value, str) or not value:
            fail(f"{label} must be non-empty")

    valid_from = parse_time(auth.get("valid_from"), "authorization.valid_from")
    valid_until = parse_time(auth.get("valid_until"), "authorization.valid_until")
    if valid_until < valid_from:
        fail("authorization validity window is inverted")
    if parties.get("payee_ref") != auth.get("approved_payee_ref"):
        fail("payee does not match approved authorization counterparty")

    limit = number(auth.get("amount_limit"), "authorization.amount_limit")
    amount = number(execution.get("amount"), "execution.amount")
    if amount > limit:
        fail("execution amount exceeds authorized limit")
    if execution.get("currency_or_asset") != auth.get("currency_or_asset"):
        fail("execution currency/asset does not match authorization")
    if not isinstance(execution.get("attempt"), int) or execution.get("attempt") < 1:
        fail("execution.attempt must be a positive integer")

    current_refs("authorization", auth.get("evidence_ids"), evidence, required=True)
    current_refs("authority", authority.get("evidence_ids"), evidence, required=True)

    for key in ("contains_credentials", "contains_private_keys", "contains_card_data", "contains_bank_credentials", "contains_seed_phrases", "contains_bearer_tokens"):
        if privacy.get(key) is not False:
            fail(f"privacy.{key} must be false")
    if privacy.get("public_disclosure_confirmed") is not True:
        fail("privacy.public_disclosure_confirmed must be true")

    if status in EXECUTED_STATES:
        if authority.get("can_execute_payment") is not True:
            fail("executed payment state requires explicit payment execution authority")
        if execution.get("submitted_at") is None:
            fail("executed payment state requires submitted_at")
        submitted_at = parse_time(execution.get("submitted_at"), "execution.submitted_at")
        if submitted_at < valid_from or submitted_at > valid_until:
            fail("payment submission is outside authorization validity window")
        if not execution.get("transaction_ref"):
            fail("executed payment state requires transaction_ref")

    settlement_state = settlement.get("state")
    if settlement_state not in {"not_submitted", "submitted", "accepted", "pending", "settled", "failed", "reversed", "unknown"}:
        fail("settlement.state is invalid")
    if status in SETTLED_STATES:
        if settlement_state not in {"settled", "reversed"}:
            fail("settled-or-later record requires settled or reversed settlement state")
        if authority.get("can_declare_settled") is not True:
            fail("settled state requires independent settlement authority")
        if not settlement.get("finality_basis") or not settlement.get("confirmation_ref") or settlement.get("settled_at") is None:
            fail("settled state requires finality basis, confirmation, and settled_at")
        parse_time(settlement.get("settled_at"), "settlement.settled_at")
        current_refs("settlement", settlement.get("evidence_ids"), evidence, required=True)

    principal = number(economics.get("principal_amount"), "economics.principal_amount")
    fees = number(economics.get("fees"), "economics.fees")
    fx_cost = number(economics.get("fx_cost"), "economics.fx_cost")
    slippage = number(economics.get("slippage"), "economics.slippage")
    total = number(economics.get("total_cash_cost"), "economics.total_cash_cost")
    if not math.isclose(total, principal + fees + fx_cost + slippage, rel_tol=1e-9, abs_tol=1e-9):
        fail("economics.total_cash_cost must reconcile to principal + fees + fx_cost + slippage")
    if status in EXECUTED_STATES and not math.isclose(principal, amount, rel_tol=1e-9, abs_tol=1e-9):
        fail("economics.principal_amount must equal execution.amount")

    if reversal.get("executed") is True:
        if reversal.get("requested") is not True:
            fail("executed reversal must first be requested")
        if authority.get("can_reverse_or_refund") is not True:
            fail("executed reversal requires independent reversal/refund authority")
        if not reversal.get("idempotency_key"):
            fail("executed reversal requires its own idempotency key")
        number(reversal.get("amount"), "reversal.amount")
        current_refs("reversal", reversal.get("evidence_ids"), evidence, required=True)

    if dispute.get("active") is True:
        if not dispute.get("allegation"):
            fail("active dispute requires allegation")
        current_refs("dispute", dispute.get("evidence_ids"), evidence, required=True)

    reconciliation_status = reconciliation.get("status")
    if reconciliation_status not in {"not_started", "pending", "matched", "break", "waived_with_authority"}:
        fail("reconciliation.status is invalid")
    if status in {"reconciled", "closed"}:
        if reconciliation_status not in {"matched", "waived_with_authority"}:
            fail("reconciled/closed payment requires resolved reconciliation")
        current_refs("reconciliation", reconciliation.get("evidence_ids"), evidence, required=True)
        for key in ("invoice_or_usage_ref", "treasury_ref", "audit_ref"):
            if not reconciliation.get(key):
                fail(f"reconciled/closed payment requires reconciliation.{key}")
    if status == "closed":
        if authority.get("can_close") is not True:
            fail("closed payment requires explicit close authority")
        if dispute.get("active") is True:
            fail("closed payment cannot retain an active dispute")
        if settlement_state == "unknown":
            fail("closed payment cannot have unknown settlement state")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_machine_payment.py <record.json>")
    record = load(Path(sys.argv[1]))
    validate(record)
    print(f"machine-payment record valid: {record['payment_id']} ({record['status']})")


if __name__ == "__main__":
    main()
