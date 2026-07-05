# Official CANNBot Plugin Comparison

This document compares the official CANNBot plugins with this Codex adapter.

## Baseline

- Official upstream: `https://gitcode.com/cann/cannbot-skills`
- Compared upstream commit: `7def5becc576de40d0e13b0fddad8345e57540e0`
- This adapter version: `2026.07.05-codex.1`
- This adapter packages: 93 standalone skills

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
- Add scenario adapters for the official products one by one.
- Do not claim end-to-end workflow support until the scenario adapter exists.

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
- Start with one workflow, likely `ops-direct-invoke` or
  `pypto-op-orchestrator`.

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

| Area | Official CANNBot | Current Codex Adapter | Gap |
| --- | --- | --- | --- |
| Plugin metadata | Per-product plugin metadata with dependencies and agents | Single Codex plugin metadata | Need scenario-level adapters |
| Skills | Curated skill packages | 93 standalone skills | Good base layer |
| Agents | Primary and specialist subagents | None | Major gap |
| Workflows | Explicit stage machines and artifact gates | None for end-to-end teams | Major gap |
| Hooks | Session and tool-use hooks | None | Medium gap; Codex support must be checked before implementing |
| Installer | Tool-specific `init.sh` and manifest | Codex plugin install/cache | Acceptable for Codex |
| Dependency tests | DG-01 to DG-11 | Local static validator | Need CI and dependency drift checks |
| Runtime tests | Behavior/integration/ST evals | Not implemented | Major gap |
| Upstream sync | Official repo is canonical | Manual generated snapshot | Need update script and release process |

## Recommended Roadmap

1. Add GitHub Actions for static validation.
2. Add an update script that regenerates the plugin from upstream CANNBot.
3. Add a manifest drift check so generated files cannot go stale.
4. Build a Codex-native `ops-direct-invoke` workflow adapter.
5. Add install smoke tests that exercise `codex plugin add cannbot@local`.
6. Add task-level regression prompts for Ascend C, PyPTO, Triton, and model
   diagnostics.

## Current Positioning

This repository is currently a Codex-native CANNBot skill distribution. It is
not yet a full Codex-native implementation of the official CANNBot team
plugins. The correct next step is to preserve the working skill distribution
and add workflow adapters incrementally.
