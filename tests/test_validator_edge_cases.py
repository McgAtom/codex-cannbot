import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_skill(root: Path, dirname: str, name: str, description: str = "Use when testing.") -> Path:
    skill = root / "skills" / dirname / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n", encoding="utf-8")
    return skill


def write_plugin_fixture(root: Path, skills: list, support_counts: Optional[dict] = None) -> None:
    write_json(
        root / ".codex-plugin" / "plugin.json",
        {
            "name": "cannbot",
            "version": "test",
            "description": "test",
            "skills": "./skills/",
        },
    )
    write_json(
        root / "skills-manifest.json",
        {
            "schemaVersion": 1,
            "plugin": "cannbot",
            "officialMarketplace": {
                "skillPackages": {
                    "test-package": {
                        "source": "./ops",
                        "version": "test",
                        "skills": [item["name"] for item in skills if item.get("officialSkillPackages")],
                    }
                }
            },
            "skills": skills,
        },
    )
    write_json(
        root / "codex-compatibility.json",
        {
            "supportCounts": support_counts or {"codex-ready": len(skills)},
            "skills": [
                {
                    "name": item["name"],
                    "sourcePath": item.get("sourcePath", f"ops/{item['name']}"),
                    "officialSkillPackages": item.get("officialSkillPackages", []),
                    "codexSupport": item.get("codexSupport", "codex-ready"),
                    "notes": item.get("notes", []),
                }
                for item in skills
            ],
        },
    )


def run_validator(plugin_root: Path, expected_name: str = "cannbot") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/validate_codex_plugin.py",
            "--plugin-root",
            str(plugin_root),
            "--expected-name",
            expected_name,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ValidatorEdgeCaseTests(unittest.TestCase):
    def test_validator_accepts_isolated_valid_plugin_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            write_skill(plugin, "alpha", "alpha")
            write_plugin_fixture(
                plugin,
                [
                    {
                        "name": "alpha",
                        "description": "Use when testing alpha.",
                        "localPath": "skills/alpha",
                        "sourcePath": "ops/alpha",
                        "officialSkillPackages": ["test-package"],
                        "codexSupport": "codex-ready",
                        "notes": [],
                    }
                ],
            )

            result = run_validator(plugin)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["skillFiles"], 1)
        self.assertEqual(payload["supportCounts"], {"codex-ready": 1})

    def test_validator_reports_duplicate_skill_names_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            write_skill(plugin, "alpha", "same-name")
            write_skill(plugin, "beta", "same-name")
            write_plugin_fixture(
                plugin,
                [
                    {
                        "name": "same-name",
                        "description": "Use when testing.",
                        "localPath": "skills/alpha",
                        "sourcePath": "ops/alpha",
                        "officialSkillPackages": ["test-package"],
                        "codexSupport": "codex-ready",
                        "notes": [],
                    }
                ],
            )

            result = run_validator(plugin)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate skill names", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_reports_bad_skill_frontmatter_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            bad = plugin / "skills" / "bad" / "SKILL.md"
            bad.parent.mkdir(parents=True)
            bad.write_text("# Missing frontmatter\n", encoding="utf-8")
            write_plugin_fixture(plugin, [])

            result = run_validator(plugin)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing YAML frontmatter", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_validator_rejects_support_count_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            write_skill(plugin, "alpha", "alpha")
            write_plugin_fixture(
                plugin,
                [
                    {
                        "name": "alpha",
                        "description": "Use when testing alpha.",
                        "localPath": "skills/alpha",
                        "sourcePath": "ops/alpha",
                        "officialSkillPackages": ["test-package"],
                        "codexSupport": "codex-ready",
                        "notes": [],
                    }
                ],
                support_counts={"codex-ready": 99},
            )

            result = run_validator(plugin)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compatibility supportCounts do not match skills", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
