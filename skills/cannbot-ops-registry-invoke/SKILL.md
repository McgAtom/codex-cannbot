---
name: cannbot-ops-registry-invoke
description: Use when the user wants Codex guidance for offline Ascend C registry-invoke custom operator development, ACLNN/API integration, UT/ST planning, evidence analysis, or tuning.
x-codex-adapter: true
---

# CANNBot Ops Registry Invoke

Lightweight Codex guide for full Ascend C custom operator projects. It covers registry-invoke work such as OpDef, `op_host`, `op_kernel`, `op_api`, ACLNN/API integration, examples, UT/ST planning, and evidence-driven fixes.

The Codex machine is assumed to be `offline-no-local-npu`. Use state only when the task is long-running or needs resume support:

- suggested state: `.cannbot/ops-registry-invoke/state.json`
- suggested evidence directory: `.cannbot/ops-registry-invoke/evidence/`
- waiting status: `awaiting_external_npu_evidence`

## When To Use

Use this guide when the user asks for a complete registered custom operator project, ACLNN two-stage API integration, multi-architecture custom op layout, UT/ST design, build/deploy diagnosis, or fixes from external custom-op evidence.

Use `cannbot-ops-direct-invoke` instead for a lightweight `<<<>>>` direct-invoke kernel harness.

## Skill Routing

Do not load every CANNBot skill. Pick the smallest relevant set:

- environment or chip assumptions: `ascendc-env-check`, `npu-arch`
- operator spec, API, precision, and tiling: `ascendc-docs-search`, `ascendc-docs-gen`, `ops-spec-gen`, `ops-precision-standard`, `ascendc-api-best-practices`, `ascendc-tiling-design`
- custom operator project structure: `ascendc-registry-invoke-template`
- UT planning and coverage: `ascendc-ut-develop`
- ST case design: `ascendc-st-design`
- static review: `ascendc-code-review`, `ascendc-performance-best-practices`
- build/runtime evidence: `ascendc-runtime-debug`
- crash/hang/memory evidence: `ascendc-crash-debug`
- precision evidence: `ascendc-precision-debug`, `ops-precision-standard`
- performance evidence: `ops-profiling`, `ascendc-performance-best-practices`

## Evidence Handoff

Ask the user for the smallest missing NPU-side result instead of requiring local board access. Classify pasted or filed evidence as:

- `build`: CMake, compiler, package, install, or registration errors
- `runtime`: ACLNN/API runtime errors, launch failures, tensor metadata issues
- `crash`: hang, timeout, illegal access, or memory fault
- `precision`: UT/ST/golden mismatch, tolerance failure, dtype/layout issue
- `perf`: profiling output, latency table, bottleneck note

When evidence changes the operator contract or tiling, revise the design. When evidence shows implementation or API-layer defects, patch and review the code. When evidence is absent, summarize off-board checks and mark the next state as `awaiting_external_npu_evidence` rather than claiming board-side success.
