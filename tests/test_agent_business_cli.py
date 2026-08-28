#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "agent_business.py"
VALIDATOR = ROOT / "scripts" / "validate_launch_packet.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class AgentBusinessCliTests(unittest.TestCase):
    def test_init_creates_conservative_validator_compatible_packet(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            output = Path(directory) / "founder.json"
            relative = output.relative_to(ROOT)
            completed = run_cli("init", "--name", "Acme Agent", "--output", str(relative))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["packet_id"], "acme-agent-001")
            self.assertEqual(packet["stage"], "pick")
            self.assertFalse(packet["authority"]["can_contact_customers"])
            self.assertFalse(packet["authority"]["can_spend"])
            self.assertEqual(packet["authority"]["max_spend_usd"], 0)
            self.assertFalse(packet["authority"]["can_sign_contracts"])
            validation = subprocess.run(
                [sys.executable, str(VALIDATOR), str(relative)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)
            self.assertIn("launch packet OK", validation.stdout)

    def test_init_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            output = Path(directory) / "founder.json"
            relative = output.relative_to(ROOT)
            first = run_cli("init", "--name", "Acme", "--output", str(relative))
            second = run_cli("init", "--name", "Different", "--output", str(relative))
            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite", second.stderr)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["business"]["name"], "Acme")

    def test_init_rejects_path_outside_repository(self):
        completed = run_cli("init", "--name", "Acme", "--output", "../outside.json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("inside the repository", completed.stderr)

    def test_stage_returns_machine_readable_index_entry(self):
        completed = run_cli("stage", "pick", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        resource = json.loads(completed.stdout)
        self.assertEqual(resource["id"], "pick")
        self.assertEqual(resource["stage"], 1)
        self.assertEqual(resource["path"], "docs/BUSINESS_MODELS.md")
        self.assertEqual(resource["next"], ["validate"])

    def test_unknown_stage_fails_cleanly(self):
        completed = run_cli("stage", "does-not-exist")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown resource id", completed.stderr)

    def test_next_resolves_current_and_indexed_next_resource(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            output = Path(directory) / "founder.json"
            relative = output.relative_to(ROOT)
            init = run_cli("init", "--name", "Acme", "--output", str(relative))
            self.assertEqual(init.returncode, 0, init.stderr)
            completed = run_cli("next", str(relative), "--json")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(result["current"]["id"], "pick")
            self.assertEqual(result["next"][0]["id"], "validate")
            self.assertEqual(result["next_actions"][0]["resource_id"], "pick")

    def test_validate_command_delegates_to_existing_validator(self):
        completed = run_cli("validate", "templates/FOUNDER_LAUNCH_PACKET.json")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_catalog_can_filter_founder_stages(self):
        completed = run_cli("catalog", "--type", "founder_stage", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        resources = json.loads(completed.stdout)
        ids = {item["id"] for item in resources}
        self.assertIn("pick", ids)
        self.assertIn("defend", ids)
        self.assertNotIn("tool-directory", ids)


if __name__ == "__main__":
    unittest.main()
