#!/usr/bin/env python3
# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2026 Huawei Technologies Co., Ltd.
# This program is free software, you can redistribute it and/or modify it under the terms and conditions of
# CANN Open Software License Agreement Version 2.0 (the "License").
# Please refer to the License for details. You may not use this file except in compliance with the License.
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE.
# See LICENSE in the root of the software repository for the full text of the License.
# ----------------------------------------------------------------------------------------------------------
"""Validate the generated Codex CANNBot plugin."""

from __future__ import annotations

import json
import re
import sys
import argparse
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PLUGIN_ROOT / "skills"
PLUGIN_JSON = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MANIFEST_JSON = PLUGIN_ROOT / "skills-manifest.json"
COMPAT_JSON = PLUGIN_ROOT / "codex-compatibility.json"

FORBIDDEN_DEFAULT_SKILL_PREFIXES = (
    "tilelang2ascend-",
    "ops-direct-invoke-flash",
    "ops-registry-invoke-workflow",
)
FORBIDDEN_TEXT = (
    ".claude/skills",
    ".opencode/skills",
    "pypto/.agents/skills",
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AssertionError(f"invalid json {path}: {exc}") from exc


def parse_name(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError(f"missing YAML frontmatter: {path}")
    for line in match.group(1).splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    raise AssertionError(f"missing name in frontmatter: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-name", default="codex-cannbot")
    args = parser.parse_args()

    findings: list[str] = []
    for path in [PLUGIN_JSON, MANIFEST_JSON, COMPAT_JSON]:
        if not path.exists():
            findings.append(f"missing file: {path.relative_to(REPO_ROOT)}")

    if findings:
        for finding in findings:
            print(f"ERROR: {finding}")
        return 1

    plugin = load_json(PLUGIN_JSON)
    manifest = load_json(MANIFEST_JSON)
    compat = load_json(COMPAT_JSON)

    if plugin.get("name") != args.expected_name:
        findings.append(f"plugin name must be {args.expected_name}")
    if plugin.get("skills") != "./skills/":
        findings.append("plugin skills path must be ./skills/")

    skill_files = sorted(SKILLS_ROOT.rglob("SKILL.md"))
    names = [parse_name(path) for path in skill_files]
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        findings.append(f"duplicate skill names: {duplicates}")

    manifest_names = sorted(item["name"] for item in manifest.get("skills", []))
    if sorted(names) != manifest_names:
        findings.append("manifest skill list does not match generated SKILL.md files")

    official = manifest.get("officialMarketplace", {})
    if not isinstance(official, dict) or not official.get("skillPackages"):
        findings.append("manifest must include official marketplace skillPackages coverage")

    for name in names:
        if name.startswith(FORBIDDEN_DEFAULT_SKILL_PREFIXES):
            findings.append(f"default bundle contains excluded workflow/experimental skill: {name}")

    for path in SKILLS_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".sh", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_TEXT:
            if token in text:
                findings.append(f"non-Codex path token {token!r} remains in {path.relative_to(REPO_ROOT)}")

    support_counts = compat.get("supportCounts", {})
    if support_counts.get("needs-review"):
        findings.append(f"compatibility contains needs-review skills: {support_counts}")

    if findings:
        for finding in findings:
            print(f"ERROR: {finding}")
        return 1

    print(json.dumps({
        "plugin": plugin["name"],
        "version": plugin.get("version"),
        "skillFiles": len(skill_files),
        "uniqueSkillNames": len(set(names)),
        "supportCounts": support_counts,
        "unpackagedOfficialSkills": [
            item["name"]
            for item in manifest.get("skills", [])
            if not item.get("officialSkillPackages")
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
