# Official CANNBot Plugin Model for Codex

This document records how the official CANNBot plugin architecture maps to the
Codex plugin adapter.

## Official Model

CANNBot separates the repository into three layers:

1. Shared skills: reusable domain knowledge and procedures under directories
   such as `ops/`, `model/`, `graph/`, `infra/`, and `runtime/`.
2. Product packages: `.claude-plugin/marketplace.json` declares skill-only
   packages and development teams, including dependency relationships.
3. Tool adapters: `plugins-official/*` and `plugins-community/*` provide
   tool-specific agents, workflows, hooks, install scripts, and runtime
   manifests.

Official development teams are not just collections of skills. They usually
define a primary orchestrator, subagents, artifact gates, retry limits, hooks,
state files, and installer-time skill whitelists.

## What Codex Can Reuse Directly

Codex can consume standalone `SKILL.md` directories directly through a plugin
bundle. The Codex adapter therefore materializes the shared skill layer into:

- `.codex-plugin/plugin.json`
- `skills/`
- `skills-manifest.json`
- `codex-compatibility.json`

The generated manifest records each skill's canonical source path and the
official marketplace skill package names that contain it. This keeps the Codex
bundle auditable against the official product registry.

Codex workflow adapters are declared separately in `adapter-registry.json`.
The registry records scenario id, adapter skill, maturity, state path, evidence
path, and referenced skill closure. The default runtime is
`offline-no-local-npu`: Codex performs off-board development and analyzes
external NPU evidence provided by the user.

## What Codex Must Not Copy Blindly

The official `plugins-official/*` directories are tool applications, not
standalone Codex skills. Their `AGENTS.md`, subagent files, hooks, and
workflows assume Claude/OpenCode/Trae/Cursor/Copilot installation layouts and
runtime semantics. Copying them directly into Codex would create unresolved
paths, missing hook behavior, and misleading workflow guarantees.

For Codex, these teams need a dedicated adapter that preserves the workflow
contract while using Codex-native capabilities.

## Migration Principles

- The canonical source remains the upstream CANNBot repository.
- Generated Codex artifacts must be reproducible from canonical sources.
- The default Codex bundle includes only reviewed standalone skills.
- Every packaged skill must have source traceability and compatibility status.
- Official marketplace dependencies are recorded for audit and update review.
- Team/workflow plugins require explicit Codex workflow adapters before they are
  enabled as orchestrated products.
- Adapters must not require local NPU hardware. Missing board-side execution
  evidence is represented as `awaiting_external_npu_evidence`, not as a local
  environment failure.
- Local flat skill fallbacks under `~/.codex/skills` should not be used for
  CANNBot once the plugin is installed.

## Future Codex Team Adapters

The next layer should adapt official development teams one by one:

- `ops-direct-invoke`: design, review, develop, and acceptance gates for
  Ascend C direct invoke operators.
- `ops-registry-invoke`: custom operator project workflow and UT/ST gates.
- `pypto-op-orchestrator`: seven-stage PyPTO state machine with resumable
  artifacts.
- `tilelang-op-orchestrator`: TileLang design, development, and performance
  feedback loop.
- `triton-op-generator`: direct in-session Triton task extraction, design,
  coding, verification, and optimization.
- `model-infer-optimize`: model analysis, implementation, validation, and
  hooks for long-running optimization tasks.
- `torch-compile`: npugraph_ex guidance and diagnosis flow.

Each adapter should define a Codex-native workflow document, state file schema,
artifact gates, validation tests, and a real `codex plugin add` smoke test.
Enterprise adapters must also be listed in `adapter-registry.json` and must
route user-provided evidence from `.cannbot/<scenario>/evidence/` to the
appropriate diagnostic or tuning skills.
