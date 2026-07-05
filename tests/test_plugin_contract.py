import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def test_validator_accepts_current_plugin(self):
        result = subprocess.run(
            [sys.executable, "scripts/validate_codex_plugin.py", "--expected-name", "cannbot"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(payload["skillFiles"], 93)
        self.assertEqual(payload["skillFiles"], payload["uniqueSkillNames"])
        self.assertEqual(payload["supportCounts"].get("codex-ready"), payload["skillFiles"])

    def test_sync_upstream_dry_run_reports_expected_plan(self):
        sync_path = ROOT / "scripts" / "sync_upstream.py"
        spec = importlib.util.spec_from_file_location("sync_upstream", sync_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        with tempfile.TemporaryDirectory() as tmp:
            upstream = Path(tmp) / "upstream"
            (upstream / "ops" / "alpha").mkdir(parents=True)
            (upstream / "ops" / "alpha" / "SKILL.md").write_text(
                "---\nname: alpha\ndescription: Use when testing alpha.\n---\n\n# Alpha\n",
                encoding="utf-8",
            )
            (upstream / "ops-lab" / "experimental").mkdir(parents=True)
            (upstream / "ops-lab" / "experimental" / "SKILL.md").write_text(
                "---\nname: experimental\ndescription: Use when testing experimental.\n---\n\n# Experimental\n",
                encoding="utf-8",
            )
            plan = module.build_sync_plan(upstream, include_experimental=False)

        names = [item["name"] for item in plan["skills"]]
        self.assertIn("alpha", names)
        self.assertNotIn("experimental", names)
        self.assertEqual(plan["supportCounts"], {"codex-ready": 1})

    def test_ops_direct_invoke_adapter_contract(self):
        skill = ROOT / "skills" / "cannbot-ops-direct-invoke" / "SKILL.md"
        self.assertTrue(skill.exists(), "missing Codex-native ops direct invoke adapter")
        text = skill.read_text(encoding="utf-8")
        for required in [
            "name: cannbot-ops-direct-invoke",
            "x-codex-adapter: true",
            ".cannbot/ops-direct-invoke/state.json",
            "environment.md",
            "DESIGN.md",
            "PLAN.md",
            "REVIEW.md",
            "ascendc-env-check",
            "ascendc-direct-invoke-template",
        ]:
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
