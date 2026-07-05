# CANNBot for Codex

Codex-native CANNBot plugin for Ascend NPU and CANN development workflows.

This repository packages the standalone CANNBot `SKILL.md` layer as a Codex
plugin. It is generated from the upstream CANNBot skills repository and keeps
source traceability in `skills-manifest.json` and `codex-compatibility.json`.

## Status

- Plugin ID: `cannbot`
- Version: `2026.07.05-codex.1`
- Upstream commit: `7def5becc576de40d0e13b0fddad8345e57540e0`
- Packaged skills: 93
- Codex compatibility: 93 `codex-ready`

## Scope

Included by default:

- Ascend C / CANN operator skills
- Catlass, PyPTO, TileLang, Triton Ascend skills
- torch.compile / npugraph_ex diagnostic skills
- model inference and model training diagnostic skills
- Runtime migration and GitCode collaboration skills

Excluded by default:

- official CANNBot team plugins under `plugins-official/*`
- community workflow applications under `plugins-community/*`
- experimental `ops-lab` workflows that need dedicated Codex workflow adapters

The official CANNBot team plugins include agents, workflows, hooks, and
tool-specific install scripts. They are not copied directly into this Codex
plugin because Codex needs a separate workflow adapter for those semantics.

## Install Locally

Add the parent directory as a local Codex marketplace and install the plugin:

```bash
codex plugin marketplace add local --source-type local --source "$HOME"
codex plugin add cannbot@local
codex plugin list
```

For this repository layout, the marketplace entry should point to
`./plugins/cannbot`.

## Validate

```bash
python3 scripts/validate_codex_plugin.py --expected-name cannbot
```

Expected result:

```json
{
  "plugin": "cannbot",
  "skillFiles": 93,
  "uniqueSkillNames": 93,
  "supportCounts": {
    "codex-ready": 93
  }
}
```

## Repository Layout

```text
.codex-plugin/plugin.json      # Codex plugin metadata
skills/                        # packaged CANNBot skills
skills-manifest.json           # generated source and marketplace traceability
codex-compatibility.json       # Codex compatibility report
docs/codex-adapter.md          # generated adapter report
docs/official-plugin-model.md  # official CANNBot model mapped to Codex
scripts/validate_codex_plugin.py
```

## Upstream

Canonical CANNBot source:

https://gitcode.com/cann/cannbot-skills

This repository is a Codex adapter/distribution of the standalone skill layer.
For full CANNBot team workflows, follow the upstream repository's official
installation path.

## License

This repository retains the upstream CANN Open Software License Agreement
Version 2.0. See `LICENSE` and `NOTICE`.
