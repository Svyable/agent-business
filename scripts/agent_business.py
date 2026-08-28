#!/usr/bin/env python3
"""Zero-dependency command-line entrypoint for the Agent Business repository.

The CLI keeps GitHub as the product surface: it reads the checked-in machine index,
creates conservative founder packets, and resolves indexed next steps locally.
It performs no network requests and emits no telemetry.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "agent-index.json"
VALIDATOR_PATH = ROOT / "scripts" / "validate_launch_packet.py"


class CliError(ValueError):
    pass


def load_index() -> dict:
    value = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("resources"), list):
        raise CliError("agent-index.json is malformed")
    return value


def resource_map(index: dict) -> dict[str, dict]:
    return {
        item["id"]: item
        for item in index["resources"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def repo_path(value: str) -> Path:
    path = (ROOT / value).resolve()
    if path != ROOT and ROOT not in path.parents:
        raise CliError("path must stay inside the repository")
    return path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise CliError("business name must contain at least one letter or number")
    return slug[:64].rstrip("-")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_packet(name: str, packet_id: str | None = None) -> dict:
    slug = slugify(name)
    return {
        "schema_version": "1.0.0",
        "packet_id": packet_id or f"{slug}-001",
        "updated_at": now_iso(),
        "stage": "pick",
        "business": {
            "name": name,
            "hypothesis": "A narrow customer will pay for a measurable agent-delivered outcome.",
            "icp": "Define one buyer with a frequent, expensive problem.",
            "pain": "Quantify the cost, delay, risk, or missed revenue caused by the problem.",
            "offer": "Define the outcome, scope, proof, and delivery boundary.",
            "pricing": "Set a testable price tied to value and delivery economics.",
            "channel": "Name where the first 100 prospects can be reached.",
            "unit_economics": "Track revenue, variable delivery cost, human review, and contribution margin.",
            "stack": [],
        },
        "evidence": [],
        "decisions": [],
        "authority": {
            "can_contact_customers": False,
            "can_spend": False,
            "max_spend_usd": 0,
            "can_sign_contracts": False,
            "requires_human_approval_for": [
                "customer outreach",
                "spend",
                "contracts",
                "regulated actions",
                "production credential changes",
            ],
        },
        "experiments": [],
        "blockers": [],
        "next_actions": [
            {
                "id": "action-001",
                "resource_id": "pick",
                "description": "Choose one narrow customer/problem pair using docs/BUSINESS_MODELS.md.",
                "status": "todo",
                "requires_approval": False,
            }
        ],
    }


def resource_summary(resource: dict) -> dict:
    return {
        key: resource[key]
        for key in ("id", "type", "stage", "name", "goal", "path", "prerequisites", "outputs", "next")
        if key in resource
    }


def print_resource(resource: dict) -> None:
    print(f"{resource.get('id')}: {resource.get('name', resource.get('id'))}")
    if "stage" in resource:
        print(f"stage: {resource['stage']}")
    print(f"goal: {resource.get('goal', '')}")
    print(f"path: {resource.get('path', '')}")
    prerequisites = resource.get("prerequisites", [])
    outputs = resource.get("outputs", [])
    next_ids = resource.get("next", [])
    print("prerequisites: " + (", ".join(prerequisites) if prerequisites else "none"))
    print("outputs: " + ("; ".join(outputs) if outputs else "none"))
    print("next: " + (", ".join(next_ids) if next_ids else "none"))


def command_init(args: argparse.Namespace) -> int:
    output = repo_path(args.output)
    if output.exists() and not args.force:
        raise CliError(f"refusing to overwrite existing file: {output.relative_to(ROOT)} (use --force)")
    packet = build_packet(args.name, args.packet_id)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    relative = output.relative_to(ROOT)
    print(f"created {relative}")
    print(f"packet_id: {packet['packet_id']}")
    print("stage: pick")
    print("next resource: docs/BUSINESS_MODELS.md")
    print(f"validate: python scripts/agent_business.py validate {relative}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    packet = repo_path(args.packet)
    relative = packet.relative_to(ROOT)
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(relative), *( ["--allow-stale"] if args.allow_stale else [] )],
        cwd=ROOT,
        check=False,
    )
    return completed.returncode


def command_stage(args: argparse.Namespace) -> int:
    resources = resource_map(load_index())
    resource = resources.get(args.resource_id)
    if resource is None:
        raise CliError(f"unknown resource id: {args.resource_id}")
    if args.json:
        print(json.dumps(resource_summary(resource), indent=2))
    else:
        print_resource(resource)
    return 0


def command_next(args: argparse.Namespace) -> int:
    packet_path = repo_path(args.packet)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise CliError("founder packet must be a JSON object")
    stage_id = packet.get("stage")
    if not isinstance(stage_id, str):
        raise CliError("founder packet stage must be a string")
    resources = resource_map(load_index())
    current = resources.get(stage_id)
    if current is None:
        raise CliError(f"founder packet references unknown resource: {stage_id}")
    next_resources = [resources[item] for item in current.get("next", []) if item in resources]
    result = {
        "packet_id": packet.get("packet_id"),
        "current": resource_summary(current),
        "next": [resource_summary(item) for item in next_resources],
        "blockers": packet.get("blockers", []),
        "next_actions": packet.get("next_actions", []),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"packet: {packet.get('packet_id', '(unknown)')}")
        print(f"current: {current['id']} — {current.get('goal', '')}")
        print(f"resource: {current.get('path', '')}")
        blockers = packet.get("blockers", [])
        if blockers:
            print(f"blockers: {len(blockers)}")
        if next_resources:
            print("indexed next:")
            for resource in next_resources:
                print(f"- {resource['id']}: {resource.get('path', '')} — {resource.get('goal', '')}")
        else:
            print("indexed next: none")
        actions = packet.get("next_actions", [])
        if actions:
            print("packet next actions:")
            for action in actions:
                print(f"- [{action.get('status', 'unknown')}] {action.get('id', '?')}: {action.get('description', '')}")
    return 0


def command_catalog(args: argparse.Namespace) -> int:
    resources = [
        item
        for item in load_index()["resources"]
        if isinstance(item, dict) and (args.type is None or item.get("type") == args.type)
    ]
    if args.json:
        print(json.dumps([resource_summary(item) for item in resources], indent=2))
        return 0
    for item in resources:
        stage = f" stage={item['stage']}" if "stage" in item else ""
        print(f"{item.get('id')} type={item.get('type')}{stage} path={item.get('path')} — {item.get('goal', '')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GitHub-native bootstrap and navigation for Agent Business"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a conservative founder launch packet")
    init_parser.add_argument("--name", required=True, help="business/project name")
    init_parser.add_argument("--packet-id", help="explicit packet identifier")
    init_parser.add_argument("--output", default="founder-packet.json", help="repository-relative output path")
    init_parser.add_argument("--force", action="store_true", help="overwrite an existing output file")
    init_parser.set_defaults(handler=command_init)

    validate_parser = subparsers.add_parser("validate", help="run the founder-packet validator")
    validate_parser.add_argument("packet", help="repository-relative founder packet path")
    validate_parser.add_argument("--allow-stale", action="store_true")
    validate_parser.set_defaults(handler=command_validate)

    stage_parser = subparsers.add_parser("stage", help="inspect one indexed resource")
    stage_parser.add_argument("resource_id")
    stage_parser.add_argument("--json", action="store_true")
    stage_parser.set_defaults(handler=command_stage)

    next_parser = subparsers.add_parser("next", help="show current and next indexed resources for a packet")
    next_parser.add_argument("packet", help="repository-relative founder packet path")
    next_parser.add_argument("--json", action="store_true")
    next_parser.set_defaults(handler=command_next)

    catalog_parser = subparsers.add_parser("catalog", help="list indexed resources")
    catalog_parser.add_argument("--type", help="filter by resource type, e.g. founder_stage")
    catalog_parser.add_argument("--json", action="store_true")
    catalog_parser.set_defaults(handler=command_catalog)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (CliError, OSError, json.JSONDecodeError) as exc:
        print(f"agent-business: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
