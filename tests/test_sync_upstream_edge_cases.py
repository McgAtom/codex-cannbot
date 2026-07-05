import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_sync_module():
    sync_path = ROOT / "scripts" / "sync_upstream.py"
    spec = importlib.util.spec_from_file_location("sync_upstream_edge", sync_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def write_skill(base: Path, rel: str, name: str, extra_frontmatter: str = "", body: str = "") -> Path:
    skill = base / rel / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(
        f"---\nname: {name}\ndescription: Use when testing {name}.\n{extra_frontmatter}---\n\n# {name}\n{body}\n",
        encoding="utf-8",
    )
    return skill


class SyncUpstreamEdgeCaseTests(unittest.TestCase):
    def test_malformed_official_marketplace_has_actionable_error(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            upstream = Path(tmp) / "upstream"
            (upstream / ".claude-plugin").mkdir(parents=True)
            (upstream / ".claude-plugin" / "marketplace.json").write_text("{bad json", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid official marketplace"):
                module.load_official_marketplace(upstream)

    def test_apply_preserves_marked_adapter_and_removes_unmarked_stale_cannbot_skill(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            plugin = tmp_root / "plugin"
            upstream = tmp_root / "upstream"

            write_skill(plugin, "skills/cannbot-local-adapter", "cannbot-local-adapter", "x-codex-adapter: true\n")
            write_skill(plugin, "skills/cannbot-skill-reviewer", "cannbot-skill-reviewer")

            write_skill(upstream, "ops/pypto-op-perf-tune", "pypto-op-perf-tune")
            write_skill(upstream, "ops/pypto-op-perf-tune/perf-analyzer", "perf-analyzer")
            write_skill(upstream, "infra/cannbot-skill-reviewer", "cannbot-skill-reviewer")
            (upstream / ".claude-plugin").mkdir(parents=True)
            (upstream / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps(
                    {
                        "plugins": [
                            {
                                "name": "perf-package",
                                "category": "skills",
                                "source": "./ops",
                                "version": "test",
                                "skills": ["./ops/pypto-op-perf-tune", "./ops/pypto-op-perf-tune/perf-analyzer"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            old_globals = {
                "PLUGIN_ROOT": module.PLUGIN_ROOT,
                "SKILLS_ROOT": module.SKILLS_ROOT,
                "MANIFEST_JSON": module.MANIFEST_JSON,
                "COMPAT_JSON": module.COMPAT_JSON,
            }
            try:
                module.PLUGIN_ROOT = plugin
                module.SKILLS_ROOT = plugin / "skills"
                module.MANIFEST_JSON = plugin / "skills-manifest.json"
                module.COMPAT_JSON = plugin / "codex-compatibility.json"
                plan = module.build_sync_plan(upstream)
                patched = module.copy_upstream_skills(upstream, plan)
                module.write_metadata(plan, patched)
            finally:
                for key, value in old_globals.items():
                    setattr(module, key, value)

            manifest = json.loads((plugin / "skills-manifest.json").read_text(encoding="utf-8"))
            names = [item["name"] for item in manifest["skills"]]
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("cannbot-local-adapter", names)
            self.assertIn("cannbot-skill-reviewer", names)
            self.assertIn("pypto-op-perf-tune", names)
            self.assertIn("perf-analyzer", names)
            self.assertTrue((plugin / "skills" / "cannbot-local-adapter" / "SKILL.md").exists())
            self.assertTrue((plugin / "skills" / "pypto-op-perf-tune" / "perf-analyzer" / "SKILL.md").exists())

    def test_non_git_upstream_without_marketplace_still_builds_plan(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            upstream = Path(tmp) / "upstream"
            write_skill(upstream, "ops/alpha", "alpha")

            plan = module.build_sync_plan(upstream)

        self.assertEqual(plan["upstreamCommit"], "unknown")
        self.assertEqual(plan["supportCounts"], {"codex-ready": 1})
        self.assertEqual(plan["officialMarketplace"], {"skillPackages": {}, "developmentTeams": {}})

    def test_codex_community_plugin_layout_takes_precedence_over_stale_standalone_roots(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            upstream = Path(tmp) / "upstream"
            write_skill(upstream, "ops/stale-only", "stale-only")
            write_skill(upstream, "plugins-community/codex-cannbot/skills/alpha", "alpha")
            write_skill(upstream, "plugins-community/codex-cannbot/skills/group", "group")
            write_skill(upstream, "plugins-community/codex-cannbot/skills/group/nested", "nested")

            plan = module.build_sync_plan(upstream)
            names = [item["name"] for item in plan["skills"]]
            local_paths = [module.local_skill_path(item["sourcePath"]).as_posix() for item in plan["skills"]]

        self.assertEqual(plan["supportCounts"], {"codex-ready": 3})
        self.assertIn("alpha", names)
        self.assertIn("group", names)
        self.assertIn("nested", names)
        self.assertNotIn("stale-only", names)
        self.assertIn("alpha", local_paths)
        self.assertIn("group/nested", local_paths)


if __name__ == "__main__":
    unittest.main()
