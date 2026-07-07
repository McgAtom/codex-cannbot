---
name: cannbot-ops-registry-invoke
description: Use when the user wants Codex to manage an offline Ascend C registry-invoke custom operator workflow with OpDef, ACLNN/API integration, UT/ST design, external NPU evidence analysis, or resumable progress.
x-codex-adapter: true
---

# CANNBot Ops Registry Invoke

This is the Codex-native workflow-preview adapter for Ascend C registry-invoke custom operator development. It extends CANNBot operator coverage beyond `<<<>>>` direct invoke into complete custom operator projects with operator definition, tiling, kernel, ACLNN/API integration, examples, UT, ST, and evidence-driven fix loops.

The Codex machine is assumed to run in `offline-no-local-npu` mode. Codex performs off-board design, code generation, review, test planning, and evidence analysis. Board-side compilation, installation, execution, precision comparison, and profiling are supplied by the user as external evidence.

## Trigger Scope

Use this adapter when the user asks Codex to create, migrate, review, debug, or tune a full Ascend C custom operator project using registry-invoke or ACLNN-style integration. Typical requests mention custom operator engineering, OpDef, `op_host`, `op_kernel`, `op_api`, ACLNN two-stage APIs, UT, ST, tiling, multi-architecture support, build/deploy errors, or board-side evidence from a custom operator package.

Use `cannbot-ops-direct-invoke` instead when the user explicitly wants a lightweight `<<<>>>` kernel direct-invoke harness rather than a registered custom operator project.

## Non Goals

This adapter does not require local NPU hardware. Do not fail because `npu-smi`, local CANN runtime, custom operator install, board execution, or profiling tools are unavailable on the Codex machine.

This adapter does not claim successful board-side registration, installation, precision, or performance without user-provided external evidence. If off-board work is complete but evidence is missing, set status to `awaiting_external_npu_evidence`.

This adapter does not directly copy official CANNBot team agents, hooks, or installers. It preserves the workflow semantics through Codex-native state, artifacts, and skill routing.

## State And Evidence

Create or update `.cannbot/ops-registry-invoke/state.json` before mutating custom operator code.

State schema:

```json
{
  "scenario": "ops-registry-invoke",
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

Use `.cannbot/ops-registry-invoke/evidence/` for external NPU evidence supplied by the user.

Recognized evidence classes:

- `build`: CMake, compiler, package, install, or custom op registration errors
- `runtime`: ACLNN/API runtime errors, launch failures, tensor metadata errors
- `crash`: hangs, memory faults, illegal access, timeout symptoms
- `precision`: UT/ST/golden mismatch, tolerance failures, dtype/layout mismatch
- `perf`: profiling output, latency data, bottleneck notes, simulator reports

## Resume Protocol

When `.cannbot/ops-registry-invoke/state.json` exists:

1. Read it first.
2. Read artifacts listed in `artifacts`.
3. Inspect `.cannbot/ops-registry-invoke/evidence/` for new user-provided results.
4. Inspect the operator project layout before editing.
5. Continue from the first incomplete stage instead of restarting.

If state references missing artifacts, mark the state as blocked, reconstruct the smallest missing artifact, and continue only after the artifact map is coherent.

## Skill Routing

Do not load every CANNBot skill for every request. Use relevant skills when the user explicitly asks for that domain or when the workflow needs specialized extraction, diagnosis, design, generation, review, or tuning.

Routing defaults:

- Environment and chip assumptions: `ascendc-env-check`, `npu-arch`
- Operator spec, API, precision, and tiling design: `ascendc-docs-search`, `ascendc-docs-gen`, `ops-spec-gen`, `ops-precision-standard`, `ascendc-api-best-practices`, `ascendc-tiling-design`
- Registry custom operator project structure: `ascendc-registry-invoke-template`
- UT and coverage planning: `ascendc-ut-develop`
- ST case design: `ascendc-st-design`
- Static review: `ascendc-code-review`, `ascendc-performance-best-practices`
- Build or runtime evidence: `ascendc-runtime-debug`
- Crash, hang, or memory evidence: `ascendc-crash-debug`
- Precision evidence: `ascendc-precision-debug`, `ops-precision-standard`
- Performance evidence: `ops-profiling`, `ascendc-performance-best-practices`

## Stages

### 0. Intake

Collect the operator name, target chip or architecture, API surface, input/output tensors, supported dtypes, formats, shape constraints, expected math, integration target, and acceptance criteria.

Artifact gate:

- `.cannbot/ops-registry-invoke/state.json`

### 1. Environment Assumptions

Record target chip, CANN version assumptions, compiler assumptions, repository type, package/install assumptions, and any user-provided environment facts. Treat local NPU absence as normal.

Write `operators/{operator_name}/environment.md` with unavailable local board checks and external evidence still needed.

### 2. Operator Contract Design

Write:

- `operators/{operator_name}/REQUIREMENTS.md`
- `operators/{operator_name}/DESIGN.md`
- `operators/{operator_name}/PLAN.md`

`DESIGN.md` must cover operator math, shape inference, dtype/format contract, OpDef/API contract, tiling strategy, workspace assumptions, precision standard, multi-architecture considerations, UT/ST plan, and expected external NPU evidence.

### 3. Project Structure And API Plan

Use `ascendc-registry-invoke-template` for expected custom operator layout. Plan files under `op_host`, `op_kernel`, `op_api`, `op_graph`, `examples`, and `tests` according to the target repository style.

Write `operators/{operator_name}/PROJECT_LAYOUT.md` with generated or modified paths and responsibilities.

### 4. Implementation

Generate or update the operator definition, tiling implementation, kernel implementation, ACLNN/API layer, graph/proto artifacts when applicable, examples, and build metadata. Preserve local style and do not overwrite user changes without inspection.

### 5. UT And ST Planning

Use `ascendc-ut-develop` for UT scope and coverage planning. Use `ascendc-st-design` for ST factors, constraints, generated cases, and expected golden behavior.

Write:

- `operators/{operator_name}/UT_PLAN.md`
- `operators/{operator_name}/ST_PLAN.md`

### 6. Review And Fix

Run the strongest available off-board review. Write `operators/{operator_name}/REVIEW.md` with defects found, fixes applied, checks rerun, residual risks, and external NPU checks still required.

### 7. Evidence Analysis

Read `.cannbot/ops-registry-invoke/evidence/` and any evidence pasted by the user. Classify it as `build`, `runtime`, `crash`, `precision`, or `perf`, then route to the matching skill.

Write `operators/{operator_name}/evidence-analysis.md`. If evidence reveals contract or tiling issues, return to stage 2. If evidence reveals implementation issues, return to stage 4 or 6. If evidence is insufficient, keep status as `awaiting_external_npu_evidence`.

### 8. Final

Before claiming completion:

1. Reread `.cannbot/ops-registry-invoke/state.json`.
2. Confirm required artifacts exist.
3. Run available off-board checks or explain why they could not run.
4. Check whether external NPU evidence is present.
5. Summarize changed files, validation evidence, and remaining risks.

Use `status: "complete"` only after applicable off-board checks pass and external NPU evidence is sufficient for the user's acceptance criteria. Use `status: "awaiting_external_npu_evidence"` when Codex has completed off-board work but board-side evidence has not been provided.

## Artifact Gates

Minimum preview artifact set:

- `.cannbot/ops-registry-invoke/state.json`
- `operators/{operator_name}/environment.md`
- `operators/{operator_name}/REQUIREMENTS.md`
- `operators/{operator_name}/DESIGN.md`
- `operators/{operator_name}/PLAN.md`
- `operators/{operator_name}/PROJECT_LAYOUT.md`
- implementation files for the selected custom operator layout
- `operators/{operator_name}/UT_PLAN.md`
- `operators/{operator_name}/ST_PLAN.md`
- `operators/{operator_name}/REVIEW.md`
- `operators/{operator_name}/evidence-analysis.md` when user evidence exists

The workflow can advance without local NPU execution, but it must not hide missing external evidence.

## Failure Routing

- Build, package, install, or registration evidence: inspect build scripts, CMake, generated package layout, include paths, op registration metadata, and route to `ascendc-runtime-debug` when needed.
- Runtime API evidence: inspect ACLNN two-stage flow, tensor metadata, workspace/executor handling, shape inference, and route to `ascendc-runtime-debug`.
- Crash, hang, memory fault, or timeout evidence: route to `ascendc-crash-debug`.
- Numerical mismatch evidence: route to `ascendc-precision-debug` plus `ops-precision-standard`.
- Performance evidence: route to `ops-profiling` and `ascendc-performance-best-practices`.
- Missing or weak tests: return to stage 5 and update UT/ST plans.
- Suspected operator contract or tiling design issue: return to stage 2 and update `DESIGN.md`.

## Acceptance Standard

A preview-grade off-board custom operator workflow is acceptable when:

- adapter state is coherent and resumable
- required artifacts exist and match the state file
- operator contract, project layout, UT plan, and ST plan are explicit
- implementation changes are scoped to the requested custom operator workflow
- available static, unit, or smoke checks pass
- missing NPU execution is explicitly represented as `awaiting_external_npu_evidence`
- user-provided external evidence has been classified, analyzed, and routed to the correct fix loop

Promotion to `workflow-enterprise` requires offline regression fixtures for build, runtime, precision, and performance evidence loops.

## State Updates

After each stage, update:

- `current_stage`
- `status`
- `attempts`
- `artifacts`
- `evidence`
- `last_updated`
- `blocked_reason`
