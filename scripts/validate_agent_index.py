#!/usr/bin/env python3
"""Validate the machine-readable Agent Business repository index."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agent-index.json"

# Record templates that predate the machine_assets convention. New *_RECORD.json
# systems must be attached to a canonical resource instead of extending this set
# without an explicit index decision.
LEGACY_RECORD_TEMPLATES = {
    "templates/CUSTOMER_SUCCESS_RECORD.json",
    "templates/ENTITY_GOVERNANCE_RECORD.json",
    "templates/FOUNDER_OUTCOME_RECORD.json",
    "templates/IP_RIGHTS_RECORD.json",
    "templates/REVENUE_OPPORTUNITY_RECORD.json",
    "templates/VENDOR_READINESS_RECORD.json",
}


def fail(message: str) -> None:
    raise SystemExit(f"agent-index validation failed: {message}")


def validate_next_graph(resources: list[dict]) -> None:
    """Fail on cycles in canonical forward navigation."""
    graph = {resource["id"]: resource.get("next", []) for resource in resources}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            start = trail.index(node) if node in trail else 0
            fail(f"next graph contains cycle: {' -> '.join(trail[start:] + [node])}")
        if node in visited:
            return
        visiting.add(node)
        for child in graph.get(node, []):
            visit(child, trail + [node])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [])


def main() -> None:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    resources = data.get("resources")
    if not isinstance(resources, list) or not resources:
        fail("resources must be a non-empty list")

    ids: set[str] = set()
    stages: list[int] = []
    indexed_machine_assets: set[str] = set()

    for resource in resources:
        resource_id = resource.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            fail("every resource needs a non-empty string id")
        if resource_id in ids:
            fail(f"duplicate resource id: {resource_id}")
        ids.add(resource_id)

        path = resource.get("path")
        if not isinstance(path, str) or not path:
            fail(f"{resource_id}: path must be a non-empty string")
        if not (ROOT / path).is_file():
            fail(f"{resource_id}: indexed path does not exist: {path}")

        machine_assets = resource.get("machine_assets", [])
        if not isinstance(machine_assets, list) or any(not isinstance(item, str) or not item for item in machine_assets):
            fail(f"{resource_id}: machine_assets must be a list of repository paths")
        for asset in machine_assets:
            if asset in indexed_machine_assets:
                fail(f"machine asset is claimed by more than one resource: {asset}")
            if not (ROOT / asset).is_file():
                fail(f"{resource_id}: machine asset does not exist: {asset}")
            indexed_machine_assets.add(asset)

        if resource.get("type") == "founder_stage":
            stage = resource.get("stage")
            if not isinstance(stage, int) or stage < 1:
                fail(f"{resource_id}: founder_stage requires a positive integer stage")
            stages.append(stage)

        for field in ("prerequisites", "next"):
            refs = resource.get(field, [])
            if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
                fail(f"{resource_id}: {field} must be a list of resource ids")

        outputs = resource.get("outputs")
        if not isinstance(outputs, list) or not outputs or any(not isinstance(item, str) or not item for item in outputs):
            fail(f"{resource_id}: outputs must be a non-empty list of strings")

    if sorted(stages) != list(range(1, len(stages) + 1)):
        fail("founder stages must be unique and contiguous starting at 1")

    for resource in resources:
        resource_id = resource["id"]
        for field in ("prerequisites", "next"):
            for ref in resource.get(field, []):
                if ref not in ids:
                    fail(f"{resource_id}: {field} references unknown id {ref}")
                if ref == resource_id:
                    fail(f"{resource_id}: {field} cannot self-reference")

    validate_next_graph(resources)

    # Durable discoverability guard: a new portable operating-system record may
    # not silently land outside the canonical machine index. Legacy templates
    # are an explicit baseline; new ones must be claimed through machine_assets.
    record_templates = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "templates").glob("*_RECORD.json")
    }
    unclassified = sorted(record_templates - indexed_machine_assets - LEGACY_RECORD_TEMPLATES)
    if unclassified:
        fail(
            "record templates require a canonical index decision via machine_assets: "
            + ", ".join(unclassified)
        )

    for entrypoint in ("canonical_entrypoint", "human_entrypoint", "llm_entrypoint"):
        path = data.get(entrypoint)
        if not isinstance(path, str) or not path or not (ROOT / path).is_file():
            fail(f"{entrypoint} must point to an existing file")

    print(
        f"agent-index OK: {len(resources)} resources, "
        f"{len(stages)} contiguous founder stages, no broken paths/references, "
        f"{len(indexed_machine_assets)} indexed machine assets, no unclassified new record systems"
    )


if __name__ == "__main__":
    main()
