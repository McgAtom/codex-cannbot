# Official CANNBot Plugin Comparison

This document compares the official CANNBot plugins with this Codex adapter.

## Baseline

- Official upstream: `https://gitcode.com/cann/cannbot-skills`
- Compared upstream commit: `7def5becc576de40d0e13b0fddad8345e57540e0`
- This adapter version: `2026.07.05-codex.2`
- This adapter packages: 95 skills total, including 93 upstream standalone
  skills and 2 local Codex workflow adapters
- Adapter registry: `adapter-registry.json`
- Default runtime: `offline-no-local-npu`
- Enterprise support level: `workflow-enterprise`

## What Official Plugins Do Well

Official CANNBot plugins are productized workflow applications, not just skill
bundles. A typical official plugin contains:

- `.claude-plugin/plugin.json` with name, version, dependencies, and agents.
- `AGENTS.md` as the primary orchestration contract.
- `agents/*.md` for specialist subagents.
- `workflows/*.md` or workflow skills for stage definitions and prompt
  templates.
- `hooks/` for session startup, tool-use guards, progress reminders, and
  subagent lifecycle checks.
- `init.sh` for tool-specific installation, skill whitelisting, symlink setup,
  manifest writing, and dependency bootstrap.
- `quickstart.md` for task-level entry points.

The strongest official design pattern is the separation of responsibilities:

1. Primary agent owns the workflow and state.
2. Subagents execute specialist work.
3. Skills provide reusable domain knowledge and templates.
4. Files and state drive stage transitions, not conversation memory.
5. Tests validate dependency closure and runtime references.

## Official Patterns To Adopt

### Product Boundary

Official plugins expose scenario-level products such as `ops-direct-invoke`,
`pypto-op-orchestrator`, `model-infer-optimize`, and `triton-op-generator`.
Each product declares a curated dependency set instead of loading every
available skill.

Codex adapter implication:

- Keep the current all-skills bundle as the base package.
- Add scenario adapters for the official products one by one inside the single
  `cannbot` plugin.
- Do not claim end-to-end workflow support until the scenario adapter exists.
- Use `adapter-registry.json` to declare each adapter's maturity, state path,
  evidence path, and referenced skill closure.

### Orchestration Contract

Official `AGENTS.md` files define:

- trigger scope and non-goals;
- primary-agent boundaries;
- stage order;
- artifact gates;
- retry limits;
- escalation and failure routes.

Codex adapter implication:

- Add Codex-native workflow documents for high-value scenarios.
- Use file-backed state and artifacts instead of relying on chat history.
- Start with `ops-direct-invoke` as the `workflow-enterprise` reference
  adapter.
- Treat missing local NPU hardware as the normal `offline-no-local-npu`
  runtime. When external board-side evidence is still missing, state must
  remain `awaiting_external_npu_evidence`.

### Dependency Closure

Official plugins use `dependencies` in plugin metadata and `INCLUDED_SKILLS`
in installers. Tests validate that workflow references are covered by the
installed skill whitelist.

Codex adapter implication:

- Keep `officialSkillPackages` in `skills-manifest.json`.
- Add CI checks for generated manifest drift and unresolved non-Codex paths.
- Track skills that are not yet represented in official marketplace packages.

### Installation and Runtime Separation

Official installers prepare a tool-specific install directory and write a
manifest. Codex does this through `codex plugin add`, which copies the source
plugin into `~/.codex/plugins/cache/...`.

Codex adapter implication:

- Treat `/Users/mcgatom/projects/codex-cannbot` as source.
- Treat `~/.codex/plugins/cache/local/cannbot/<version>` as runtime output.
- Never ask users to edit cache files directly.

### Test Layering

Official tests cover static structure, dependency graph integrity, CLI
behavior, integration flows, and semantic evals.

Codex adapter implication:

- Current validation is only L1 static validation.
- Add GitHub Actions for `validate_codex_plugin.py`.
- Add install smoke tests with `codex plugin add`.
- Add workflow-level regression tasks after scenario adapters are introduced.

## Gap Matrix

Current Codex adapter registry coverage:

- `ops-direct-invoke`: `workflow-enterprise`, state path
  `.cannbot/ops-direct-invoke/state.json`, evidence path
  `.cannbot/ops-direct-invoke/evidence/`
- `ops-registry-invoke`: `workflow-preview`, state path
  `.cannbot/ops-registry-invoke/state.json`, evidence path
  `.cannbot/ops-registry-invoke/evidence/`

| Area | Official CANNBot | Current Codex Adapter | Gap |
| --- | --- | --- | --- |
| Plugin metadata | Per-product plugin metadata with dependencies and agents | Single Codex plugin metadata | Need scenario-level adapters |
| Skills | Curated skill packages | 95 skills total, including 93 upstream standalone skills and 2 local Codex workflow adapters | Good base layer |
| Agents | Primary and specialist subagents | None | Major gap |
| Workflows | Explicit stage machines and artifact gates | `ops-direct-invoke` has a `workflow-enterprise` Codex adapter; `ops-registry-invoke` has a `workflow-preview` adapter; other teams remain skill-only | Major gap remains outside the first two adapters |
| Hooks | Session and tool-use hooks | None | Medium gap; Codex support must be checked before implementing |
| Installer | Tool-specific `init.sh` and manifest | Codex plugin install/cache | Acceptable for Codex |
| Dependency tests | DG-01 to DG-11 | Local static validator plus adapter registry checks | Need broader scenario regression coverage |
| Runtime tests | Behavior/integration/ST evals | Offline workflow contracts only; local NPU is not required | Need user-evidence regression fixtures |
| Upstream sync | Official repo is canonical | `sync_upstream.py` preserves local Codex adapters | Need release checklist automation |

## Recommended Roadmap

1. Keep `ops-direct-invoke` as the enterprise reference adapter.
2. Promote `ops-registry-invoke` from `workflow-preview` to
   `workflow-enterprise` after adding offline regression fixtures for custom
   operator build, runtime, precision, and UT/ST evidence loops.
3. Add user-evidence regression fixtures for build, runtime, precision, and
   performance feedback loops.
4. Promote `pypto-op-orchestrator` to the next Codex workflow adapter.
5. Add `triton-op-generator`, `tilelang-op-orchestrator`, `model-infer-optimize`,
   and `torch-compile` adapters using the same contract.
6. Add task-level regression prompts for Ascend C, PyPTO, Triton, and model
   diagnostics.

## Current Positioning

This repository is a single Codex-native CANNBot plugin with a broad
`skill-ready` base, a `workflow-enterprise` adapter for `ops-direct-invoke`,
and a `workflow-preview` adapter for `ops-registry-invoke`. It is not yet a
full Codex-native implementation of every official CANNBot team plugin. The
correct next step is to preserve the working skill distribution and add
workflow adapters incrementally.
