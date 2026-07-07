---
name: cannbot-ops-direct-invoke
description: Use when the user wants Codex to manage an end-to-end offline Ascend C <<<>>> direct-invoke operator development workflow with staged artifacts, external NPU evidence analysis, validation gates, or resumable progress.
x-codex-adapter: true
---

# CANNBot Ops Direct Invoke

This is the Codex-native enterprise workflow adapter for Ascend C direct-invoke operator development. It orchestrates official CANNBot skills into one resumable workflow while assuming the Codex machine is `offline-no-local-npu`.

Codex owns off-board development: requirements intake, design, code generation, static review, test planning, log parsing, and iterative fixes. Board-side compilation, execution, profiling, and precision comparison come from user-provided external evidence.

## Trigger Scope

Use this adapter when the user asks Codex to develop, review, debug, or iterate an Ascend C `<<<>>>` direct-invoke operator workflow. Typical requests include creating a direct-invoke project, designing tiling, generating kernel and host code, reviewing compile/runtime/precision/performance evidence, or resuming a staged CANNBot operator task.

Use narrower skills directly when the user asks only for isolated knowledge lookup, API explanation, log interpretation, or a small code review that does not need workflow state.

## Non Goals

This adapter does not require or assume local NPU hardware. Do not fail the workflow because `npu-smi`, board execution, CANN runtime, or profiling tools are unavailable on the Codex machine.

This adapter does not claim board-side success without external evidence. If no external evidence is available after off-board work is complete, set the state to `awaiting_external_npu_evidence` and summarize the exact commands or checks the user should run in their NPU environment.

This adapter does not copy official CANNBot `plugins-official/*` agents, hooks, or installers. It preserves the workflow contract with Codex-native state, artifacts, and skill routing.

## State And Evidence

Create or update `.cannbot/ops-direct-invoke/state.json` in the target repository before mutating operator code.

State schema:

```json
{
  "scenario": "ops-direct-invoke",
  "operator": "operator_name",
  "current_stage": "intake",
  "status": "in_progress",
  "runtime": "offline-no-local-npu",
  "attempts": {},
  "artifacts": {},
  "evidence": {},
  "last_updated": "ISO-8601 timestamp",
  "blocked_reason": ""
}
```

Use `.cannbot/ops-direct-invoke/evidence/` for external NPU evidence supplied by the user. Evidence can be copied into files or summarized in artifacts, but it must remain traceable to the user-provided result.

Recognized evidence classes:

- `build`: compiler output, CMake logs, missing include/library errors
- `runtime`: ACL/runtime errors, launch failures, error codes, stack snippets
- `crash`: hangs, memory faults, illegal access, timeout symptoms
- `precision`: golden mismatch, tolerance failures, dtype/layout mismatch
- `perf`: profiling output, latency tables, bottleneck notes, simulator reports

## Resume Protocol

When `.cannbot/ops-direct-invoke/state.json` exists:

1. Read it first.
2. Read the artifacts listed in `artifacts`.
3. Inspect `.cannbot/ops-direct-invoke/evidence/` for new user-provided results.
4. Inspect the operator workspace before editing.
5. Continue from the first incomplete stage instead of restarting.

If state references missing artifacts, mark the state as blocked, reconstruct the smallest missing artifact, and continue only after the artifact map is coherent again.

## Skill Routing

Do not load every CANNBot skill for every request. Use relevant skills only when the user explicitly asks for that domain or when the workflow needs specialized extraction, diagnosis, design, generation, review, or tuning.

Routing defaults:

- Environment and chip assumptions: `ascendc-env-check`, `npu-arch`
- API, memory movement, precision, and tiling design: `ascendc-docs-search`, `ops-spec-gen`, `ops-precision-standard`, `ascendc-api-best-practices`, `ascendc-tiling-design`
- Project scaffolding and implementation: `ascendc-direct-invoke-template`
- Static review: `ascendc-code-review`, `ascendc-performance-best-practices`
- Build or runtime evidence: `ascendc-runtime-debug`
- Crash, hang, or memory evidence: `ascendc-crash-debug`
- Precision evidence: `ascendc-precision-debug`, `ops-precision-standard`
- Performance evidence: `ops-profiling`, `ops-simulator`, `aiss-tiling-solver`, `ascendc-perf-optimize`

## Stages

### 0. Intake

Collect the operator name, target chip or architecture, input/output tensors, supported dtypes, layouts, shape constraints, expected math, and acceptance criteria. Infer only low-risk defaults and record every assumption.

Artifact gate:

- `.cannbot/ops-direct-invoke/state.json`

### 1. Environment Assumptions

Record the target chip, CANN version, compiler assumptions, Python assumptions, repository build prerequisites, and any user-provided environment facts. Treat local NPU absence as normal.

Write `operators/{operator_name}/environment.md` with:

- target environment assumptions
- user-provided NPU environment facts
- local commands that were run, if any
- unavailable local board checks
- external evidence still needed

### 2. Design

Write:

- `operators/{operator_name}/DESIGN.md`
- `operators/{operator_name}/PLAN.md`

`DESIGN.md` must cover math semantics, shape and dtype contract, tiling strategy, memory movement, precision standard, expected edge cases, off-board validation plan, and external NPU evidence expected from the user. `PLAN.md` must be an executable checklist ordered by dependency.

### 3. Walkthrough

Review the design before code generation.

Write `operators/{operator_name}/WALKTHROUGH.md` with:

- design risks
- rejected alternatives
- external evidence required for board-side confidence
- exact criteria for moving to implementation

### 4. Implementation

Use `ascendc-direct-invoke-template` as the starting point for direct-invoke project structure. Preserve local repository style and build tooling. Do not overwrite user changes without inspecting them.

Expected outputs usually include:

- kernel implementation
- host/direct-invoke harness
- tiling or launch configuration
- unit or smoke tests
- golden reference when applicable

Update `.cannbot/ops-direct-invoke/state.json` after each meaningful artifact is created.

### 5. Review And Fix

Run the strongest available off-board review. Write `operators/{operator_name}/REVIEW.md` with:

- defects found
- fixes applied
- tests or static checks rerun
- residual risks
- external NPU checks still required

### 6. Evidence Analysis

Read `.cannbot/ops-direct-invoke/evidence/` and any evidence pasted by the user. Classify it as `build`, `runtime`, `crash`, `precision`, or `perf`, then route to the matching skill.

Write:

- `operators/{operator_name}/evidence-analysis.md`
- updated `operators/{operator_name}/REVIEW.md` when fixes are applied

If evidence shows a design issue, return to stage 2 and update `DESIGN.md`. If evidence shows an implementation defect, return to stage 4 or 5. If evidence is insufficient, keep status as `awaiting_external_npu_evidence` and ask for the smallest missing result.

### 7. Final

Before claiming completion:

1. Reread `.cannbot/ops-direct-invoke/state.json`.
2. Confirm every required artifact exists.
3. Run available off-board tests or explain why they could not run.
4. Check whether external NPU evidence is present.
5. Summarize changed files, verification evidence, and remaining risks.

Use `status: "complete"` only after applicable off-board checks pass and external NPU evidence is sufficient for the user's acceptance criteria. Use `status: "awaiting_external_npu_evidence"` when Codex has completed off-board work but board-side evidence has not been provided. Use `status: "blocked"` only when the next required input is outside local code changes and cannot be reasonably inferred.

## Artifact Gates

Minimum enterprise artifact set:

- `.cannbot/ops-direct-invoke/state.json`
- `operators/{operator_name}/environment.md`
- `operators/{operator_name}/DESIGN.md`
- `operators/{operator_name}/PLAN.md`
- `operators/{operator_name}/WALKTHROUGH.md`
- implementation files for the selected repository layout
- `operators/{operator_name}/REVIEW.md`
- `operators/{operator_name}/evidence-analysis.md` when user evidence exists

The workflow can advance without local NPU execution, but it must not hide missing external evidence.

## Failure Routing

- Build or compile evidence: inspect compiler output, CMake/build scripts, include paths, CANN assumptions, and route to `ascendc-runtime-debug` when needed.
- Runtime launch evidence: inspect ACL/runtime error codes, launch parameters, tensor metadata, and route to `ascendc-runtime-debug`.
- Crash, hang, memory fault, or timeout evidence: route to `ascendc-crash-debug`.
- Numerical mismatch evidence: route to `ascendc-precision-debug` plus `ops-precision-standard`.
- Performance evidence: route to `ops-profiling`, `ops-simulator`, `aiss-tiling-solver`, or `ascendc-perf-optimize`.
- Suspected tiling or memory movement design issue: return to stage 2 and update `DESIGN.md`.

## Acceptance Standard

An enterprise-grade off-board PR is acceptable when:

- adapter state is coherent and resumable
- required artifacts exist and match the state file
- implementation changes are scoped to the requested operator workflow
- available static, unit, or smoke checks pass
- missing NPU execution is explicitly represented as `awaiting_external_npu_evidence`
- user-provided external evidence has been classified, analyzed, and routed to the correct fix loop

## GitCode Integration

Use `gitcode-issue-gen`, `gitcode-issue-handler`, `gitcode-pr-handler`, and `gitcode-toolkit` only when the user is working against GitCode issues or PRs. These are collaboration helpers, not required for local operator development.

## State Updates

After each stage, update:

- `current_stage`
- `status`
- `attempts`
- `artifacts`
- `evidence`
- `last_updated`
- `blocked_reason`
