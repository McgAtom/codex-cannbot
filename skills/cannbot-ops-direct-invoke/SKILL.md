---
name: cannbot-ops-direct-invoke
description: Use when the user wants Codex guidance for offline Ascend C <<<>>> direct-invoke operator development, review, debugging, or tuning.
x-codex-adapter: true
---

# CANNBot Ops Direct Invoke

Lightweight Codex guide for Ascend C `<<<>>>` direct-invoke operator work. The Codex machine is assumed to be `offline-no-local-npu`: Codex designs, edits, reviews, and analyzes evidence, while board-side compilation/execution/profiling results come from the user.

Use state only when the task is long-running or needs resume support:

- suggested state: `.cannbot/ops-direct-invoke/state.json`
- suggested evidence directory: `.cannbot/ops-direct-invoke/evidence/`
- waiting status: `awaiting_external_npu_evidence`

## When To Use

Use this guide for direct-invoke kernel projects, tiling design, host harnesses, launch configuration, static review, and follow-up fixes from external build/runtime/precision/perf evidence.

Use a narrower skill directly when the user asks only for API lookup, one log explanation, or a small code review.

## Skill Routing

Do not load every CANNBot skill. Pick the smallest relevant set:

- environment or chip assumptions: `ascendc-env-check`, `npu-arch`
- API, precision, and tiling design: `ascendc-docs-search`, `ops-spec-gen`, `ops-precision-standard`, `ascendc-api-best-practices`, `ascendc-tiling-design`
- direct-invoke project structure: `ascendc-direct-invoke-template`
- static review: `ascendc-code-review`, `ascendc-performance-best-practices`
- build/runtime evidence: `ascendc-runtime-debug`
- crash/hang/memory evidence: `ascendc-crash-debug`
- precision evidence: `ascendc-precision-debug`, `ops-precision-standard`
- performance evidence: `ops-profiling`, `ops-simulator`, `aiss-tiling-solver`, `ascendc-perf-optimize`

## Evidence Handoff

Ask the user for the smallest missing NPU-side result instead of requiring local board access. Classify pasted or filed evidence as:

- `build`: compiler, CMake, include, library, or package errors
- `runtime`: ACL/runtime errors, launch failures, tensor metadata issues
- `crash`: hang, timeout, illegal access, or memory fault
- `precision`: golden mismatch, tolerance failure, dtype/layout issue
- `perf`: profiling output, latency table, bottleneck note

When evidence changes the design, revise the design. When evidence shows an implementation defect, patch and review the code. When evidence is absent, summarize off-board checks and mark the next state as `awaiting_external_npu_evidence` rather than claiming board-side success.
