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

    def test_enterprise_adapter_registry_contract(self):
        registry_path = ROOT / "adapter-registry.json"
        self.assertTrue(registry_path.exists(), "missing adapter registry")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(registry["plugin"], "cannbot")
        self.assertEqual(registry["defaultRuntime"], "offline-no-local-npu")

        scenarios = {item["id"]: item for item in registry["scenarios"]}
        self.assertIn("ops-direct-invoke", scenarios)
        scenario = scenarios["ops-direct-invoke"]
        self.assertEqual(scenario["adapterSkill"], "cannbot-ops-direct-invoke")
        self.assertEqual(scenario["maturity"], "workflow-enterprise")
        self.assertEqual(scenario["statePath"], ".cannbot/ops-direct-invoke/state.json")
        self.assertEqual(scenario["evidencePath"], ".cannbot/ops-direct-invoke/evidence/")
        self.assertIn("ascendc-runtime-debug", scenario["referencedSkills"])
        self.assertIn("ascendc-precision-debug", scenario["referencedSkills"])

    def test_enterprise_positioning_is_documented(self):
        required = [
            "adapter-registry.json",
            "offline-no-local-npu",
            "workflow-enterprise",
            "awaiting_external_npu_evidence",
        ]
        for path in [
            ROOT / "README.md",
            ROOT / "docs" / "codex-adapter.md",
            ROOT / "docs" / "official-plugin-comparison.md",
        ]:
            text = path.read_text(encoding="utf-8")
            for token in required:
                self.assertIn(token, text, str(path))

    def test_readme_is_bilingual_and_documents_compliance_boundary(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for token in [
            "## 中文说明",
            "## English Guide",
            "合规说明",
            "Compliance Notes",
            "not legal advice",
            "Huawei AI Processors",
            "CANN Open Software License Agreement Version 2.0",
        ]:
            self.assertIn(token, text)

    def test_validator_enforces_enterprise_adapter_contract(self):
        result = subprocess.run(
            [sys.executable, "scripts/validate_codex_plugin.py", "--expected-name", "cannbot"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["adapterScenarios"]["workflow-enterprise"], 1)

    def test_release_docs_match_current_plugin_metadata(self):
        plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        result = subprocess.run(
            [sys.executable, "scripts/validate_codex_plugin.py", "--expected-name", "cannbot"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## {plugin['version']}", changelog)

        expected_skill_count = str(payload["skillFiles"])
        for path in [
            ROOT / "README.md",
            ROOT / "docs" / "codex-adapter.md",
            ROOT / "docs" / "official-plugin-comparison.md",
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertIn(plugin["version"], text, str(path))
            self.assertIn(expected_skill_count, text, str(path))


if __name__ == "__main__":
    unittest.main()
