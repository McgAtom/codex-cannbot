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


DEFAULT_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_REGISTRY = "adapter-registry.json"

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
ADAPTER_REQUIRED_SECTIONS = (
    "## Trigger Scope",
    "## Non Goals",
    "## State And Evidence",
    "## Skill Routing",
    "## Stages",
    "## Artifact Gates",
    "## Failure Routing",
    "## Acceptance Standard",
)
ADAPTER_MATURITIES = {"workflow-preview", "workflow-enterprise"}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AssertionError(f"invalid json {path}: {exc}") from exc


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError(f"missing YAML frontmatter: {path}")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("\"'")
    if "name" not in result:
        raise AssertionError(f"missing name in frontmatter: {path}")
    return result


def parse_name(path: Path) -> str:
    return parse_frontmatter(path)["name"]


def validate_adapter_registry(
    plugin_root: Path,
    skill_names: set[str],
    skill_files_by_name: dict[str, Path],
    frontmatter_by_name: dict[str, dict[str, str]],
) -> tuple[list[str], dict[str, int]]:
    findings: list[str] = []
    registry_path = plugin_root / ADAPTER_REGISTRY
    adapter_names = {
        name for name, frontmatter in frontmatter_by_name.items() if frontmatter.get("x-codex-adapter") == "true"
    }
    if adapter_names and not registry_path.exists():
        return [f"missing file: {ADAPTER_REGISTRY}"], {}
    if not registry_path.exists():
        return findings, {}

    try:
        registry = load_json(registry_path)
    except AssertionError as exc:
        return [str(exc)], {}

    if registry.get("plugin") != "cannbot":
        findings.append("adapter registry plugin must be cannbot")
    if registry.get("defaultRuntime") != "offline-no-local-npu":
        findings.append("adapter registry defaultRuntime must be offline-no-local-npu")

    scenarios = registry.get("scenarios", [])
    if not isinstance(scenarios, list):
        findings.append("adapter registry scenarios must be a list")
        scenarios = []

    registered_adapters: set[str] = set()
    maturity_counts: Counter[str] = Counter()
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            findings.append(f"adapter registry scenario {index} must be an object")
            continue
        scenario_id = scenario.get("id")
        adapter_skill = scenario.get("adapterSkill")
        maturity = scenario.get("maturity")
        state_path = scenario.get("statePath")
        evidence_path = scenario.get("evidencePath")
        referenced = scenario.get("referencedSkills", [])
        if not isinstance(scenario_id, str) or not scenario_id:
            findings.append(f"adapter registry scenario {index} must include string id")
            continue
        expected_state = f".cannbot/{scenario_id}/state.json"
        expected_evidence = f".cannbot/{scenario_id}/evidence/"
        if adapter_skill not in adapter_names:
            findings.append(f"adapter scenario {scenario_id} references missing Codex adapter skill: {adapter_skill}")
            continue
        registered_adapters.add(str(adapter_skill))
        if maturity not in ADAPTER_MATURITIES:
            findings.append(f"adapter scenario {scenario_id} has invalid maturity: {maturity}")
        else:
            maturity_counts[str(maturity)] += 1
        if state_path != expected_state:
            findings.append(f"adapter scenario {scenario_id} statePath must be {expected_state}")
        if evidence_path != expected_evidence:
            findings.append(f"adapter scenario {scenario_id} evidencePath must be {expected_evidence}")
        if not isinstance(referenced, list) or not all(isinstance(item, str) for item in referenced):
            findings.append(f"adapter scenario {scenario_id} referencedSkills must be a string list")
            referenced = []
        missing_refs = sorted(set(referenced) - skill_names)
        if missing_refs:
            findings.append(f"adapter scenario {scenario_id} references missing skills: {missing_refs}")

        text = skill_files_by_name[str(adapter_skill)].read_text(encoding="utf-8", errors="replace")
        for section in ADAPTER_REQUIRED_SECTIONS:
            if section not in text:
                findings.append(f"adapter skill {adapter_skill} missing required section: {section}")
        for token in [
            expected_state,
            expected_evidence,
            "offline-no-local-npu",
            "awaiting_external_npu_evidence",
        ]:
            if token not in text:
                findings.append(f"adapter skill {adapter_skill} missing required token: {token}")

    unregistered = sorted(adapter_names - registered_adapters)
    if unregistered:
        findings.append(f"Codex adapter skills missing from adapter registry: {unregistered}")
    return findings, dict(maturity_counts)


def validate_plugin(plugin_root: Path, expected_name: str) -> tuple[list[str], dict[str, object] | None]:
    plugin_root = plugin_root.resolve()
    skills_root = plugin_root / "skills"
    plugin_json = plugin_root / ".codex-plugin" / "plugin.json"
    manifest_json = plugin_root / "skills-manifest.json"
    compat_json = plugin_root / "codex-compatibility.json"
    findings: list[str] = []
    for path in [plugin_json, manifest_json, compat_json]:
        if not path.exists():
            findings.append(f"missing file: {rel(path, plugin_root)}")

    if findings:
        return findings, None

    try:
        plugin = load_json(plugin_json)
        manifest = load_json(manifest_json)
        compat = load_json(compat_json)
    except AssertionError as exc:
        return [str(exc)], None

    if plugin.get("name") != expected_name:
        findings.append(f"plugin name must be {expected_name}")
    if plugin.get("skills") != "./skills/":
        findings.append("plugin skills path must be ./skills/")

    skill_files = sorted(skills_root.rglob("SKILL.md"))
    names: list[str] = []
    skill_files_by_name: dict[str, Path] = {}
    frontmatter_by_name: dict[str, dict[str, str]] = {}
    for path in skill_files:
        try:
            frontmatter = parse_frontmatter(path)
            name = frontmatter["name"]
            names.append(name)
            skill_files_by_name[name] = path
            frontmatter_by_name[name] = frontmatter
        except AssertionError as exc:
            findings.append(str(exc))
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        findings.append(f"duplicate skill names: {duplicates}")

    manifest_items = manifest.get("skills", [])
    if not isinstance(manifest_items, list):
        findings.append("manifest skills must be a list")
        manifest_items = []
    manifest_names: list[str] = []
    for index, item in enumerate(manifest_items):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            findings.append(f"manifest skill item {index} must include a string name")
            continue
        manifest_names.append(item["name"])
    if sorted(names) != sorted(manifest_names):
        findings.append("manifest skill list does not match generated SKILL.md files")

    official = manifest.get("officialMarketplace", {})
    if not isinstance(official, dict) or not official.get("skillPackages"):
        findings.append("manifest must include official marketplace skillPackages coverage")

    for name in names:
        if name.startswith(FORBIDDEN_DEFAULT_SKILL_PREFIXES):
            findings.append(f"default bundle contains excluded workflow/experimental skill: {name}")

    for path in skills_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".sh", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_TEXT:
            if token in text:
                findings.append(f"non-Codex path token {token!r} remains in {rel(path, plugin_root)}")

    support_counts = compat.get("supportCounts", {})
    compat_items = compat.get("skills", [])
    if not isinstance(compat_items, list):
        findings.append("compatibility skills must be a list")
        compat_items = []
    computed_support_counts = Counter()
    compat_names: list[str] = []
    for index, item in enumerate(compat_items):
        if not isinstance(item, dict):
            findings.append(f"compatibility skill item {index} must be an object")
            continue
        name = item.get("name")
        support = item.get("codexSupport")
        if not isinstance(name, str):
            findings.append(f"compatibility skill item {index} must include a string name")
            continue
        compat_names.append(name)
        if isinstance(support, str):
            computed_support_counts[support] += 1
        else:
            findings.append(f"compatibility skill {name} must include codexSupport")
    if dict(computed_support_counts) != support_counts:
        findings.append(
            f"compatibility supportCounts do not match skills: expected {dict(computed_support_counts)}, got {support_counts}"
        )
    if sorted(compat_names) != sorted(names):
        findings.append("compatibility skill list does not match generated SKILL.md files")
    if support_counts.get("needs-review"):
        findings.append(f"compatibility contains needs-review skills: {support_counts}")

    adapter_findings, adapter_counts = validate_adapter_registry(
        plugin_root,
        set(names),
        skill_files_by_name,
        frontmatter_by_name,
    )
    findings.extend(adapter_findings)

    payload = {
        "plugin": plugin.get("name"),
        "version": plugin.get("version"),
        "skillFiles": len(skill_files),
        "uniqueSkillNames": len(set(names)),
        "supportCounts": support_counts,
        "adapterScenarios": adapter_counts,
        "unpackagedOfficialSkills": [
            item["name"]
            for item in manifest_items
            if isinstance(item, dict) and isinstance(item.get("name"), str) and not item.get("officialSkillPackages")
        ],
    }
    return findings, payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-name", default="codex-cannbot")
    parser.add_argument("--plugin-root", default=str(DEFAULT_PLUGIN_ROOT))
    args = parser.parse_args()

    findings, payload = validate_plugin(Path(args.plugin_root), args.expected_name)
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}")
        return 1

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
