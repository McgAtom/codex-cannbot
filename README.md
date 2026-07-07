# CANNBot for Codex

## 中文说明

CANNBot for Codex 是面向 Codex 平台的 CANNBot 插件。它把上游 CANNBot
的 standalone `SKILL.md` 能力打包成一个 Codex 插件，并在此基础上增加
Codex-native 的工作流适配器，让 Codex 能在没有本地 NPU 的机器上完成离板开发、
设计、代码生成、静态审查、日志解析和调优迭代。

这个仓库不是官方上游 CANNBot 项目的替代品，而是一个 Codex 适配/分发版本。
来源和可追溯信息记录在 `skills-manifest.json`、`codex-compatibility.json` 和
`adapter-registry.json` 中。

### 当前状态

- 插件 ID: `cannbot`
- 版本: `2026.07.05-codex.2`
- 上游提交: `7def5becc576de40d0e13b0fddad8345e57540e0`
- 打包技能: 94 个，包含 93 个上游技能和 1 个 Codex 工作流适配器
- Codex 兼容性: 94 个 `codex-ready`
- 默认运行模式: `offline-no-local-npu`
- 企业级工作流: 1 个 `workflow-enterprise`

### 核心运行模型

默认假设 Codex 本机没有 NPU 环境。插件不要求本地存在 `npu-smi`、板端执行、
profiling 工具或真实算子运行能力。Codex 负责离板工作：

- 需求理解和信息提炼
- CANN / Ascend C / PyPTO / TileLang / Triton 等方向的设计辅助
- 代码生成和改造建议
- 静态审查、测试方案和调试路径
- 编译日志、运行日志、精度结果、profile 结果的解析
- 根据用户从 NPU 环境拿到的结果继续迭代

如果离板工作已经完成，但还没有外部 NPU 证据，工作流状态必须标记为
`awaiting_external_npu_evidence`，不能声称板端已经通过。

### 怎么使用

先把本仓库所在的父目录加入 Codex 本地 marketplace，然后安装插件：

```bash
codex plugin marketplace add /Users/mcgatom
codex plugin add cannbot@local
codex plugin list
```

对于当前目录结构，marketplace entry 应指向：

```text
./projects/codex-cannbot
```

安装后，在 Codex 对话里直接提出任务即可。你可以明确点名场景，也可以描述问题，
Codex 会在需要专业信息提炼、诊断、设计、生成、审查或调优时查找并使用相关 skill。
插件不会每次加载全部 skill。

示例请求：

```text
帮我设计一个 Ascend C direct-invoke 算子的 tiling 和实现计划
```

```text
这是我在 NPU 环境上的编译错误，帮我判断是 CMake、include path 还是 API 用法问题
```

```text
这是精度对比结果，帮我分析可能的 dtype、layout 或 tiling 问题
```

```text
帮我把这个 PyTorch 模型推理里的 KVCache 部分做昇腾 NPU 适配分析
```

### 使用场景

默认包含：

- Ascend C / CANN 算子开发、调试、精度分析和性能分析
- CATLASS、PyPTO、TileLang、Triton Ascend 相关开发流程
- `torch.compile` / `npugraph_ex` 诊断
- 模型推理和模型训练诊断
- Runtime migration 和 GitCode 协作技能
- Codex-native direct-invoke 算子工作流适配器

当前企业级工作流：

- `ops-direct-invoke`: `workflow-enterprise`
  - 状态文件: `.cannbot/ops-direct-invoke/state.json`
  - 外部证据目录: `.cannbot/ops-direct-invoke/evidence/`

外部证据可以包括：

- build: 编译日志、CMake 输出、include/library 错误
- runtime: ACL/runtime 错误、launch 失败、错误码
- crash: hang、非法访问、内存错误、超时
- precision: golden mismatch、误差超限、dtype/layout 问题
- perf: profiling 输出、latency 表、瓶颈分析

### 支持级别

- `skill-ready`: standalone 技能已经打包；当用户请求相关主题或 Codex 识别到需要专业信息时按需调用。
- `workflow-preview`: 场景适配器存在，但 artifact gates 和离线回归覆盖还未达到企业级。
- `workflow-enterprise`: 场景适配器已进入 `adapter-registry.json`，并具备状态契约、证据契约、失败路由、文档和 CI 契约测试。

### 不包含什么

默认不直接打包：

- 上游 `plugins-official/*` 下的官方 CANNBot team 插件
- 上游 `plugins-community/*` 下的社区 workflow 应用
- 需要专门 Codex workflow adapter 的实验性 `ops-lab` 流程

原因是官方 team 插件包含 agents、workflows、hooks 和工具特定安装脚本。它们不能
直接复制到 Codex 插件里，否则会产生路径、hook 行为和运行时语义不匹配的问题。
正确方式是在单个 `cannbot` 插件内逐步增加 Codex-native workflow adapters。

### 验证

```bash
make ci
```

`make ci` 会运行脚本语法检查、插件契约验证、adapter registry 检查、文档一致性测试、
上游同步边界测试和本地 Codex install smoke 相关测试。

期望输出包含：

```json
{
  "plugin": "cannbot",
  "skillFiles": 94,
  "uniqueSkillNames": 94,
  "supportCounts": {
    "codex-ready": 94
  },
  "adapterScenarios": {
    "workflow-enterprise": 1
  }
}
```

本地安装 smoke test：

```bash
make smoke-install
```

从上游 CANNBot checkout 刷新：

```bash
make sync-upstream UPSTREAM=/tmp/cannbot-skills-update
make ci
```

同步脚本会保留本仓库维护的 `skills/cannbot-*` Codex 工作流适配器。

### 来源

上游 CANNBot 源项目：

```text
https://gitcode.com/cann/cannbot-skills
```

本仓库生成自上游提交：

```text
7def5becc576de40d0e13b0fddad8345e57540e0
```

### 合规说明

这不是法律意见，也不能替代律师审查。工程侧看，本仓库保留了上游
`LICENSE` 和 `NOTICE`，并在 README、manifest 和 compatibility 报告里记录来源。

当前仓库声明并保留的许可是 `CANN Open Software License Agreement Version 2.0`。
该许可允许在遵守条款的前提下使用、修改、集成和分发软件或衍生作品，但用途限定在
Huawei AI Processors 和/或 CANN Software 相关系统。分发时应保留 notices，并向接收方
提供该许可协议副本。不要移除、遮盖或修改上游版权和许可声明。

如果要对外发布、商业分发、放入企业内部 marketplace，或用于非 Huawei AI Processors
/ CANN Software 场景，应先做正式法务审查。

## English Guide

CANNBot for Codex is a Codex-native plugin for CANNBot workflows. It packages
the upstream standalone CANNBot `SKILL.md` layer as a single Codex plugin and
adds Codex-native workflow adapters for end-to-end off-board development.

This repository is not the canonical upstream CANNBot project. It is a Codex
adapter and distribution. Source traceability is recorded in
`skills-manifest.json`, `codex-compatibility.json`, and `adapter-registry.json`.

### Status

- Plugin ID: `cannbot`
- Version: `2026.07.05-codex.2`
- Upstream commit: `7def5becc576de40d0e13b0fddad8345e57540e0`
- Packaged skills: 94, including 93 upstream skills and 1 Codex workflow adapter
- Codex compatibility: 94 `codex-ready`
- Default runtime: `offline-no-local-npu`
- Enterprise workflows: 1 `workflow-enterprise`

### Runtime Model

The Codex machine is assumed to have no local NPU. The plugin must not require
local `npu-smi`, board execution, profiling tools, or real operator runs. Codex
owns off-board work:

- requirement extraction
- CANN, Ascend C, PyPTO, TileLang, and Triton design assistance
- code generation and migration guidance
- static review, test planning, and debug routing
- build log, runtime log, precision result, and profile analysis
- iterative fixes based on NPU evidence provided by the user

When off-board work is complete but NPU evidence is missing, workflow adapters
must use `awaiting_external_npu_evidence` instead of claiming board-side
success.

### How To Use

Add the parent directory as a local Codex marketplace and install the plugin:

```bash
codex plugin marketplace add /Users/mcgatom
codex plugin add cannbot@local
codex plugin list
```

For this repository layout, the marketplace entry should point to:

```text
./projects/codex-cannbot
```

After installation, ask Codex for the CANNBot task you need. You can name a
scenario explicitly or describe the issue naturally. Codex should search and
use relevant skills when the request needs specialized extraction, diagnosis,
design, generation, review, or tuning. It should not load every skill for every
conversation.

Example prompts:

```text
Design the tiling and implementation plan for an Ascend C direct-invoke operator.
```

```text
Here is my NPU build log. Decide whether this is a CMake, include path, or API usage issue.
```

```text
Here is a precision mismatch report. Analyze possible dtype, layout, or tiling causes.
```

```text
Analyze how to adapt this PyTorch model inference KVCache path for Ascend NPU.
```

### Use Cases

Included by default:

- Ascend C / CANN operator development, debugging, precision analysis, and performance analysis
- CATLASS, PyPTO, TileLang, and Triton Ascend workflows
- `torch.compile` / `npugraph_ex` diagnostics
- model inference and model training diagnostics
- runtime migration and GitCode collaboration skills
- Codex-native direct-invoke operator workflow adapter

Current enterprise workflow:

- `ops-direct-invoke`: `workflow-enterprise`
  - State path: `.cannbot/ops-direct-invoke/state.json`
  - Evidence path: `.cannbot/ops-direct-invoke/evidence/`

External evidence can include:

- build: compiler logs, CMake output, include/library errors
- runtime: ACL/runtime errors, launch failures, error codes
- crash: hangs, illegal access, memory faults, timeouts
- precision: golden mismatch, tolerance failures, dtype/layout issues
- perf: profiling output, latency tables, bottleneck notes

### Support Levels

- `skill-ready`: standalone skills are packaged and invoked on demand.
- `workflow-preview`: a scenario adapter exists but is not yet enterprise complete.
- `workflow-enterprise`: a scenario adapter is listed in `adapter-registry.json`
  and has a state contract, evidence contract, failure routing, documentation,
  and CI-enforced contract tests.

### What Is Not Included

The default package does not directly copy:

- official CANNBot team plugins under upstream `plugins-official/*`
- community workflow applications under upstream `plugins-community/*`
- experimental `ops-lab` workflows that need dedicated Codex workflow adapters

Official CANNBot team plugins contain agents, workflows, hooks, and
tool-specific installers. Copying them directly into Codex would create path,
hook, and runtime mismatches. The Codex-native approach is to add workflow
adapters incrementally inside the single `cannbot` plugin.

### Validate

```bash
make ci
```

`make ci` runs script syntax checks, plugin contract validation, adapter
registry checks, documentation consistency tests, upstream sync edge-case tests,
and local Codex install smoke-related tests.

Expected output includes:

```json
{
  "plugin": "cannbot",
  "skillFiles": 94,
  "uniqueSkillNames": 94,
  "supportCounts": {
    "codex-ready": 94
  },
  "adapterScenarios": {
    "workflow-enterprise": 1
  }
}
```

For a local install smoke test:

```bash
make smoke-install
```

To refresh from a checked-out upstream CANNBot repository:

```bash
make sync-upstream UPSTREAM=/tmp/cannbot-skills-update
make ci
```

The sync command preserves local `skills/cannbot-*` Codex workflow adapters.

### Repository Layout

```text
.codex-plugin/plugin.json      # Codex plugin metadata
adapter-registry.json          # Codex workflow adapter registry
skills/                        # packaged CANNBot skills
skills-manifest.json           # generated source and marketplace traceability
codex-compatibility.json       # Codex compatibility report
docs/codex-adapter.md          # generated adapter report
docs/official-plugin-model.md  # official CANNBot model mapped to Codex
docs/official-plugin-comparison.md
scripts/validate_codex_plugin.py
scripts/sync_upstream.py
scripts/smoke_install.sh
tests/test_plugin_contract.py
Makefile
.github/workflows/ci.yml
```

### Upstream

Canonical CANNBot source:

```text
https://gitcode.com/cann/cannbot-skills
```

Generated from upstream commit:

```text
7def5becc576de40d0e13b0fddad8345e57540e0
```

### Compliance Notes

This is not legal advice. It does not replace review by counsel.

This repository retains the upstream `LICENSE` and `NOTICE`. The declared
license is `CANN Open Software License Agreement Version 2.0`. At an engineering
level, the license permits use, modification, integration, and distribution of
the software or derivative works when the terms are followed, but the permitted
purpose is limited to systems with Huawei AI Processors and/or CANN Software.
Distribution should retain notices and provide recipients with a copy of the
license agreement. Do not remove, obscure, or alter upstream copyright or
license notices.

Before external publication, commercial distribution, enterprise marketplace
publication, or any use outside Huawei AI Processors / CANN Software scenarios,
run a formal legal review.
