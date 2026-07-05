# Codex Adapter Report

- Upstream commit: `7def5becc576de40d0e13b0fddad8345e57540e0`
- Generated at: `2026-07-05T09:40:19.812362+00:00`
- Skills packaged: `93`
- Support counts: `{'codex-ready': 93}`
- Experimental included: `False`

## Default Scope

The default Codex plugin packages standalone skills from `ops/`, `model/`, `graph/`, `infra/`, and `runtime/`.
It intentionally excludes CANNBot Team/Agent workflow plugins and community application plugins.

## Official Marketplace Coverage

This report records the upstream `.claude-plugin/marketplace.json` skill packages and development team dependencies.
Each generated skill includes `officialSkillPackages` so Codex coverage can be audited against the official CANNBot product boundary.

## Excluded By Default

- `tilelang2ascend-*` (`ops-lab/tilelang-to-ascendc/skills`): ops-lab TileLang-to-AscendC is a multi-phase workflow with remote/container verification assumptions; package it only after a dedicated Codex workflow adapter exists.
- `plugins-official/*` (`plugins-official`): Official CANNBot teams contain agents/workflows, not standalone Codex skills.
- `plugins-community/*` (`plugins-community`): Community plugins are handled as separate applications and are not part of the default Codex core bundle.

## Update Contract

1. Run `python3 plugins-community/codex-cannbot/scripts/build_codex_plugin.py` after upstream skills change.
2. Run `python3 plugins-community/codex-cannbot/scripts/validate_codex_plugin.py`.
3. Install locally with `codex plugin add codex-cannbot --marketplace cannbot-local` after adding this repository as a local marketplace.
