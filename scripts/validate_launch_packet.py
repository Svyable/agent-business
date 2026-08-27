#!/usr/bin/env python3
"""Dependency-free semantic validation for Agent Business founder launch packets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"


def fail(message: str) -> None:
    raise SystemExit(f"launch-packet validation failed: {message}")


def parse_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        fail(f"{label} must be an ISO-8601 datetime")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", nargs="?", default="templates/FOUNDER_LAUNCH_PACKET.json")
    parser.add_argument("--allow-stale", action="store_true", help="permit expired evidence for archival validation")
    args = parser.parse_args()

    packet_path = (ROOT / args.packet).resolve()
    if ROOT not in packet_path.parents and packet_path != ROOT:
        fail("packet path must stay inside the repository")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    resource_ids = {item["id"] for item in index["resources"]}

    required = {"schema_version", "packet_id", "updated_at", "stage", "business", "evidence", "decisions", "authority", "experiments", "blockers", "next_actions"}
    missing = sorted(required - packet.keys())
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    if packet["schema_version"] != "1.0.0":
        fail("unsupported schema_version")
    if packet["stage"] not in resource_ids:
        fail(f"stage references unknown agent-index resource: {packet['stage']}")

    authority = packet["authority"]
    for field in ("can_contact_customers", "can_spend", "can_sign_contracts"):
        if not isinstance(authority.get(field), bool):
            fail(f"authority.{field} must be boolean")
    if not isinstance(authority.get("max_spend_usd"), (int, float)) or authority["max_spend_usd"] < 0:
        fail("authority.max_spend_usd must be non-negative")
    if not authority["can_spend"] and authority["max_spend_usd"] != 0:
        fail("max_spend_usd must be 0 when can_spend is false")

    evidence_ids: set[str] = set()
    now = datetime.now(timezone.utc)
    for item in packet["evidence"]:
        evidence_id = item.get("id")
        if not evidence_id or evidence_id in evidence_ids:
            fail(f"evidence ids must be non-empty and unique: {evidence_id!r}")
        evidence_ids.add(evidence_id)
        observed = parse_time(item.get("observed_at"), f"evidence {evidence_id}.observed_at")
        expires = parse_time(item.get("expires_at"), f"evidence {evidence_id}.expires_at")
        if expires <= observed:
            fail(f"evidence {evidence_id} expires_at must be after observed_at")
        if expires < now and not args.allow_stale:
            fail(f"evidence {evidence_id} is stale; refresh it or use --allow-stale for archival validation")

    decision_ids: set[str] = set()
    live_topics: set[str] = set()
    for decision in packet["decisions"]:
        decision_id = decision.get("id")
        if not decision_id or decision_id in decision_ids:
            fail(f"decision ids must be non-empty and unique: {decision_id!r}")
        decision_ids.add(decision_id)
        unknown = sorted(set(decision.get("evidence_ids", [])) - evidence_ids)
        if unknown:
            fail(f"decision {decision_id} references unknown evidence: {', '.join(unknown)}")
        if decision.get("status") == "approved":
            topic = decision.get("topic")
            if topic in live_topics:
                fail(f"contradictory state: multiple approved decisions for topic {topic!r}")
            live_topics.add(topic)

    action_ids: set[str] = set()
    for action in packet["next_actions"]:
        action_id = action.get("id")
        if not action_id or action_id in action_ids:
            fail(f"action ids must be non-empty and unique: {action_id!r}")
        action_ids.add(action_id)
        resource_id = action.get("resource_id")
        if resource_id not in resource_ids:
            fail(f"action {action_id} references unknown resource_id {resource_id!r}")
        if action.get("requires_approval") and not authority.get("requires_human_approval_for"):
            fail(f"action {action_id} requires approval but authority has no approval policy")

    critical = [b.get("id") for b in packet["blockers"] if b.get("severity") == "critical"]
    doing = [a.get("id") for a in packet["next_actions"] if a.get("status") == "doing"]
    if critical and doing:
        fail(f"critical blockers {critical} exist while actions are marked doing: {doing}")

    parse_time(packet["updated_at"], "updated_at")
    print(f"launch packet OK: {packet['packet_id']} at resource {packet['stage']} with {len(packet['evidence'])} evidence items, {len(packet['decisions'])} decisions, and {len(packet['next_actions'])} next actions")


if __name__ == "__main__":
    main()
