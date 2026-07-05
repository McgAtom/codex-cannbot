#!/usr/bin/env python3
"""Sync the Codex CANNBot plugin from an upstream CANNBot checkout.

The script keeps this repository as a Codex distribution. It discovers
standalone upstream skills, reports what would be packaged, and can materialize
the skill tree plus metadata with --apply.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from json import JSONDecodeError
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
PLUGIN_JSON = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MANIFEST_JSON = PLUGIN_ROOT / "skills-manifest.json"
COMPAT_JSON = PLUGIN_ROOT / "codex-compatibility.json"
ADAPTER_MARKER_KEY = "x-codex-adapter"

DEFAULT_SOURCE_ROOTS = ("ops", "model", "graph", "infra", "runtime")
EXPERIMENTAL_ROOTS = ("ops-lab",)
CODEX_COMMUNITY_SKILLS_ROOT = Path("plugins-community/codex-cannbot/skills")
TEXT_EXTENSIONS = {".md", ".py", ".sh", ".txt", ".yaml", ".yml", ".json"}
FORBIDDEN_PATH_REPLACEMENTS = (
    (".opencode/skills/tilelang-env-check/", "<SKILL_DIR>/"),
    (".claude/skills/tilelang-env-check/", "<SKILL_DIR>/"),
    (".opencode/skills/ or .claude/skills/", "a tool-specific skill installation directory"),
    (
        "pypto/.agents/skills/pypto-pass-error-locator/references/ir-analysis-guide.md",
        "an optional external pypto-pass-error-locator reference, not packaged in this Codex plugin",
    ),
    (
        "python3 pypto/.agents/skills/pypto-pass-error-locator/scripts/get_op_info.py",
        "# Optional external helper not packaged in this Codex plugin:\n# python3 <pypto-pass-error-locator>/scripts/get_op_info.py",
    ),
    (
        "python3 pypto/.agents/skills/pypto-aicore-error-locator/scripts/locate_source_line.py",
        "# Optional external helper not packaged in this Codex plugin:\n# python3 <pypto-aicore-error-locator>/scripts/locate_source_line.py",
    ),
    (
        "pypto/.agents/skills/pypto-op-perf-tune/perf-analyzer/scripts/analyze_perf.py",
        "<SKILL_DIR>/scripts/analyze_perf.py",
    ),
    (
        "pypto/.agents/skills/pypto-op-perf-tune/tune-swimlane/",
        "<SKILL_DIR>/",
    ),
)


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def upstream_commit(upstream: Path) -> str:
    if not (upstream / ".git").exists():
        return "unknown"
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=upstream,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    key: str | None = None
    block: list[str] = []
    for raw in match.group(1).splitlines():
        if raw.startswith(" ") and key:
            block.append(raw.strip())
            continue
        if key and block:
            data[key] = " ".join(block).strip()
            block = []
        if ":" not in raw:
            continue
        k, v = raw.split(":", 1)
        k = k.strip()
        v = v.strip().strip("\"'")
        if v in {">", "|"}:
            key = k
            block = []
        else:
            data[k] = v
            key = None
    if key and block:
        data[key] = " ".join(block).strip()
    return data


def load_official_marketplace(upstream: Path) -> dict[str, object]:
    path = upstream / ".claude-plugin" / "marketplace.json"
    if not path.exists():
        return {"skillPackages": {}, "developmentTeams": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise ValueError(f"invalid official marketplace {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"invalid official marketplace {path}: root must be an object")
    skill_packages: dict[str, dict[str, object]] = {}
    development_teams: dict[str, dict[str, object]] = {}
    for entry in raw.get("plugins", []):
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        if entry.get("category") == "skills":
            skills = [
                str(item).lstrip("./").split("/")[-1]
                for item in entry.get("skills", [])
                if isinstance(item, str)
            ]
            skill_packages[name] = {
                "source": entry.get("source", ""),
                "version": entry.get("version", ""),
                "skills": sorted(skills),
            }
        elif entry.get("category") == "development":
            development_teams[name] = {
                "source": entry.get("source", ""),
                "version": entry.get("version", ""),
                "dependencies": entry.get("dependencies", []),
            }
    return {"skillPackages": skill_packages, "developmentTeams": development_teams}


def package_index(official: dict[str, object]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for pkg_name, pkg in dict(official.get("skillPackages", {})).items():
        if not isinstance(pkg, dict):
            continue
        for skill_name in pkg.get("skills", []):
            if isinstance(skill_name, str):
                result.setdefault(skill_name, []).append(str(pkg_name))
    return {name: sorted(values) for name, values in result.items()}


def iter_skill_dirs(upstream: Path, include_experimental: bool) -> list[Path]:
    codex_skills_root = upstream / CODEX_COMMUNITY_SKILLS_ROOT
    if codex_skills_root.exists() and any(codex_skills_root.rglob("SKILL.md")):
        return [skill_md.parent for skill_md in sorted(codex_skills_root.rglob("SKILL.md"))]

    roots = list(DEFAULT_SOURCE_ROOTS)
    if include_experimental:
        roots.extend(EXPERIMENTAL_ROOTS)
    found: list[Path] = []
    for root_name in roots:
        root = upstream / root_name
        if not root.exists():
            continue
        for skill_md in sorted(root.rglob("SKILL.md")):
            found.append(skill_md.parent)
    return found


def codex_patched_text(text: str) -> str:
    for old, repl in FORBIDDEN_PATH_REPLACEMENTS:
        text = text.replace(old, repl)
    return text


def classify(text: str, source_path: str) -> tuple[str, list[str]]:
    support = "codex-ready"
    notes: list[str] = []
    if source_path.startswith("ops-lab/"):
        support = "experimental"
        notes.append("upstream ops-lab experimental skill")
    if any(token in text for token in ["npu-smi", "msprof", "ASCEND_HOME_PATH", "torch_npu", "CANN"]):
        notes.append("requires matching Ascend/CANN environment for execution")
    if any(token in text for token in ["sudo", "curl ", "pip install", "apt install"]):
        notes.append("may install tools or access network; keep user confirmation for mutations")
    if "gitcode.com" in text or "GITCODE" in text:
        notes.append("GitCode API/network/token may be required")
    patched = codex_patched_text(text)
    if ".claude/skills" in patched or ".opencode/skills" in patched or "pypto/.agents/skills" in patched:
        support = "needs-review"
        notes.append("contains unresolved non-Codex path reference")
    return support, notes


def build_sync_plan(upstream: Path, include_experimental: bool = False) -> dict[str, object]:
    upstream = upstream.resolve()
    official = load_official_marketplace(upstream)
    packages = package_index(official)
    skills: list[dict[str, object]] = []
    counts: dict[str, int] = {}
    for src in iter_skill_dirs(upstream, include_experimental):
        skill_md = src / "SKILL.md"
        fm = parse_frontmatter(skill_md)
        name = fm.get("name", src.name)
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        source_path = str(src.relative_to(upstream))
        support, notes = classify(text, source_path)
        counts[support] = counts.get(support, 0) + 1
        skills.append(
            {
                "name": name,
                "description": fm.get("description", ""),
                "sourcePath": source_path,
                "officialSkillPackages": packages.get(name, []),
                "codexSupport": support,
                "notes": notes,
            }
        )
    skills.sort(key=lambda item: str(item["name"]))
    return {
        "upstreamCommit": upstream_commit(upstream),
        "includeExperimental": include_experimental,
        "officialMarketplace": official,
        "supportCounts": counts,
        "skills": skills,
    }


def preserve_local_adapters() -> dict[str, Path]:
    preserved: dict[str, Path] = {}
    if not SKILLS_ROOT.exists():
        return preserved
    temp_root = PLUGIN_ROOT / ".sync-preserve"
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir()
    for entry in SKILLS_ROOT.iterdir():
        skill_md = entry / "SKILL.md"
        if entry.is_dir() and skill_md.exists() and parse_frontmatter(skill_md).get(ADAPTER_MARKER_KEY) == "true":
            dst = temp_root / entry.name
            shutil.copytree(entry, dst)
            preserved[entry.name] = dst
    return preserved


def restore_local_adapters(preserved: dict[str, Path]) -> None:
    for name, src in preserved.items():
        dst = SKILLS_ROOT / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    if preserved:
        shutil.rmtree(next(iter(preserved.values())).parent)


def patch_text_files(root: Path) -> int:
    changed = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new = codex_patched_text(text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def local_skill_path(source_path: str) -> Path:
    path = Path(source_path)
    try:
        return path.relative_to(CODEX_COMMUNITY_SKILLS_ROOT)
    except ValueError:
        pass
    parts = path.parts
    if len(parts) <= 1:
        return Path(parts[0])
    return Path(*parts[1:])


def copy_upstream_skills(upstream: Path, plan: dict[str, object]) -> int:
    preserved = preserve_local_adapters()
    if SKILLS_ROOT.exists():
        shutil.rmtree(SKILLS_ROOT)
    SKILLS_ROOT.mkdir(parents=True)
    plan_items = sorted(plan["skills"], key=lambda item: (len(Path(str(item["sourcePath"])).parts), str(item["sourcePath"])))
    for item in plan_items:
        src = upstream / str(item["sourcePath"])
        dst = SKILLS_ROOT / local_skill_path(str(item["sourcePath"]))
        if dst.exists():
            continue
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", ".pytest_cache"))
    restore_local_adapters(preserved)
    return patch_text_files(SKILLS_ROOT)


def read_local_adapter_items() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        fm = parse_frontmatter(skill_md)
        if fm.get(ADAPTER_MARKER_KEY) != "true":
            continue
        name = fm.get("name", skill_md.parent.name)
        items.append(
            {
                "name": name,
                "description": fm.get("description", ""),
                "localPath": str(skill_md.parent.relative_to(PLUGIN_ROOT)),
                "sourcePath": f"local/{skill_md.parent.name}",
                "officialSkillPackages": [],
                "codexSupport": "codex-ready",
                "notes": ["Codex-native workflow adapter maintained in this repository"],
            }
        )
    return items


def write_metadata(plan: dict[str, object], text_files_patched: int) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    upstream_items = []
    for item in plan["skills"]:
        local_path = str(Path("skills") / local_skill_path(str(item["sourcePath"])))
        upstream_items.append({**item, "localPath": local_path})
    all_items = sorted(upstream_items + read_local_adapter_items(), key=lambda item: str(item["name"]))
    counts: dict[str, int] = {}
    for item in all_items:
        support = str(item["codexSupport"])
        counts[support] = counts.get(support, 0) + 1
    manifest = {
        "schemaVersion": 1,
        "plugin": "cannbot",
        "upstreamCommit": plan["upstreamCommit"],
        "generatedAt": generated_at,
        "includeExperimental": plan["includeExperimental"],
        "officialMarketplace": plan["officialMarketplace"],
        "skills": all_items,
        "upstreamCodexAdapterName": "codex-cannbot",
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    compat = {
        "upstreamCommit": plan["upstreamCommit"],
        "generatedAt": generated_at,
        "patchStats": {"textFilesPatched": text_files_patched},
        "supportCounts": counts,
        "skills": [
            {
                "name": item["name"],
                "sourcePath": item["sourcePath"],
                "officialSkillPackages": item["officialSkillPackages"],
                "codexSupport": item["codexSupport"],
                "notes": item["notes"],
            }
            for item in all_items
        ],
    }
    COMPAT_JSON.write_text(json.dumps(compat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", required=True, help="Path to a CANNBot upstream checkout")
    parser.add_argument("--include-experimental", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Materialize skills and metadata")
    args = parser.parse_args()
    upstream = Path(args.upstream).expanduser().resolve()
    plan = build_sync_plan(upstream, include_experimental=args.include_experimental)
    text_files_patched = 0
    if args.apply:
        text_files_patched = copy_upstream_skills(upstream, plan)
        write_metadata(plan, text_files_patched)
    print(json.dumps({**plan, "textFilesPatched": text_files_patched}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
