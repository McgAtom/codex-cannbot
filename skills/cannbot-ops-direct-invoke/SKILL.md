---
name: cannbot-ops-direct-invoke
description: Use when the user wants Codex to manage an end-to-end Ascend C <<<>>> direct-invoke operator development workflow with staged artifacts, validation gates, or resumable progress.
x-codex-adapter: true
---

# CANNBot Ops Direct Invoke

This is the Codex-native workflow adapter for Ascend C direct-invoke operator development. Use it to orchestrate official CANNBot skills into one resumable engineering workflow. The primary agent owns the workflow state and invokes narrower skills only after the required stage artifacts exist.

## Required State

Create or update `.cannbot/ops-direct-invoke/state.json` in the target repository before mutating operator code.

State schema:

```json
{
  "operator": "operator_name",
  "current_stage": "intake",
  "status": "in_progress",
  "attempts": {},
  "artifacts": {},
  "last_updated": "ISO-8601 timestamp",
  "blocked_reason": ""
}
```

Use `operators/{operator_name}/` as the default operator workspace unless the user or repository already has a stronger local convention.

## Resume Protocol

When `.cannbot/ops-direct-invoke/state.json` exists:

1. Read it first.
2. Read the artifacts listed in `artifacts`.
3. Inspect the operator workspace before editing.
4. Continue from the first incomplete stage instead of restarting.

If state references missing artifacts, mark the state as blocked and reconstruct the smallest missing artifact before continuing.

## Stages

### 0. Intake

Collect the operator name, target chip or architecture, input/output tensors, supported dtypes, layouts, shape constraints, expected math, and acceptance criteria. If the request is underspecified, infer only low-risk defaults and record assumptions.

Artifact gate:

- `.cannbot/ops-direct-invoke/state.json`

### 1. Environment Gate

Use `ascendc-env-check` and `npu-arch` when environment or chip details matter. Check CANN, compiler, Python, `npu-smi`, visible NPU devices, `ASCEND_HOME_PATH`, and repository build prerequisites when available.

Write `operators/{operator_name}/environment.md` with:

- detected environment
- missing dependencies
- chip/architecture assumptions
- whether board execution is available
- local commands that were run

Do not proceed to implementation when mandatory build prerequisites are absent. Continue design-only work when hardware is unavailable and record that limitation.

### 2. Design

Use `ascendc-docs-search`, `ops-spec-gen`, `ops-precision-standard`, `ascendc-api-best-practices`, and `ascendc-tiling-design` as needed.

Write:

- `operators/{operator_name}/DESIGN.md`
- `operators/{operator_name}/PLAN.md`

`DESIGN.md` must cover math semantics, shape and dtype contract, tiling strategy, memory movement, precision standard, expected edge cases, and validation plan. `PLAN.md` must be an executable checklist ordered by dependency.

### 3. Walkthrough

Review the design before code generation. Use `ascendc-code-review` for static reasoning and `ascendc-performance-best-practices` for obvious performance risks.

Write `operators/{operator_name}/WALKTHROUGH.md` with:

- design risks
- rejected alternatives
- dependencies on environment availability
- exact criteria for moving to implementation

### 4. Implementation

Use `ascendc-direct-invoke-template` as the starting point for direct-invoke project structure. Preserve local repository style and build tooling. Do not overwrite user changes without inspecting them.

Expected outputs usually include:

- kernel implementation
- host/direct invoke harness
- tiling or launch configuration
- unit or smoke tests
- golden reference when applicable

Update `.cannbot/ops-direct-invoke/state.json` after each meaningful artifact is created.

### 5. Review And Fix Loop

Use `ascendc-code-review`, `ascendc-runtime-debug`, `ascendc-crash-debug`, and `ascendc-precision-debug` depending on failure mode.

Write `operators/{operator_name}/REVIEW.md` with:

- defects found
- fixes applied
- tests rerun
- residual risks

Route failures:

- build or compile failure: inspect compiler output, CMake/build scripts, include paths, and CANN environment
- runtime failure: use `ascendc-runtime-debug`
- crash, hang, or memory fault: use `ascendc-crash-debug`
- numerical mismatch: use `ascendc-precision-debug` plus `ops-precision-standard`
- suspected bad tiling: return to stage 2 and update `DESIGN.md`

### 6. Precision And Performance Acceptance

Run the strongest available validation for the current machine. Use `ops-profiling`, `ops-simulator`, `aiss-tiling-solver`, and `ascendc-perf-optimize` when performance data is requested or available.

Write:

- `operators/{operator_name}/precision.md`
- `operators/{operator_name}/performance.md`

If hardware is unavailable, provide compile-only or static evidence and mark board validation as blocked in state.

### 7. Final Summary

Before claiming completion:

1. Reread `.cannbot/ops-direct-invoke/state.json`.
2. Confirm every required artifact exists.
3. Run the available tests or explain why they could not run.
4. Summarize changed files, validation evidence, and remaining risks.

## GitCode Integration

Use `gitcode-issue-gen`, `gitcode-issue-handler`, `gitcode-pr-handler`, and `gitcode-toolkit` only when the user is working against GitCode issues or PRs. These are collaboration helpers, not required for local operator development.

## State Updates

After each stage, update:

- `current_stage`
- `status`
- `attempts`
- `artifacts`
- `last_updated`
- `blocked_reason`

Use `status: "complete"` only after all applicable validation gates pass. Use `status: "blocked"` only when the missing dependency is outside the local code changes you can make.
