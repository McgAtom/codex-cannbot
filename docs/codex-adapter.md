# Codex Adapter Report

- Upstream commit: `7def5becc576de40d0e13b0fddad8345e57540e0`
- Adapter version: `2026.07.05-codex.2`
- Generated at: `2026-07-05T13:16:55.090501+00:00`
- Skills packaged: `95`
- Support counts: `{'codex-ready': 95}`
- Adapter registry: `adapter-registry.json`
- Default runtime: `offline-no-local-npu`
- Workflow adapters: `{'guided-workflow': 2}`
- Experimental included: `False`

## Default Scope

The default Codex plugin packages standalone skills from `ops/`, `model/`, `graph/`, `infra/`, and `runtime/`.
It intentionally excludes CANNBot Team/Agent workflow plugins and community application plugins.

## Runtime Contract

Codex-side workflows are off-board by default. Local NPU hardware is not
required and local board execution is not part of CI. Workflow adapters must
record missing board-side evidence as `awaiting_external_npu_evidence` instead
of treating absent NPU tools as a local failure.

User-provided NPU results belong under each scenario evidence directory, such
as `.cannbot/ops-direct-invoke/evidence/`. Adapters classify that evidence and
route it to the relevant skill only when the user asks for the domain or the
workflow needs specialized diagnosis, design, generation, review, or tuning.

## Support Levels

- `skill-ready`: packaged standalone skills, invoked on demand.
- `guided-workflow`: scenario is listed in `adapter-registry.json`; Codex uses
  it as lightweight routing guidance and invokes relevant skills on demand.
  State and evidence paths are suggested for long-running tasks.

Current `guided-workflow` scenarios: `ops-direct-invoke`, `ops-registry-invoke`.

## Official Marketplace Coverage

This report records the upstream `.claude-plugin/marketplace.json` skill packages and development team dependencies.
Each generated skill includes `officialSkillPackages` so Codex coverage can be audited against the official CANNBot product boundary.

## Excluded By Default

- `tilelang2ascend-*` (`ops-lab/tilelang-to-ascendc/skills`): ops-lab TileLang-to-AscendC is a multi-phase workflow with remote/container verification assumptions; package it only after a dedicated Codex workflow adapter exists.
- `plugins-official/*` (`plugins-official`): Official CANNBot teams contain agents/workflows, not standalone Codex skills.
- `plugins-community/*` (`plugins-community`): Community plugins are handled as separate applications and are not part of the default Codex core bundle.

## Update Contract

1. Run `make sync-upstream UPSTREAM=/path/to/cannbot-skills` after upstream skills change.
2. Run `make ci`.
3. Install locally with `codex plugin add cannbot@local` after adding the parent directory as a local marketplace.
