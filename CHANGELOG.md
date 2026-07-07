# Changelog

## 2026.07.05-codex.2

- Add Codex-native `cannbot-ops-direct-invoke` workflow adapter foundation.
- Package 94 skills total: 93 upstream standalone skills plus 1 local Codex
  workflow adapter.
- Add `adapter-registry.json` with `offline-no-local-npu` runtime semantics and
  one `workflow-enterprise` adapter.
- Clarify external NPU evidence handling with `awaiting_external_npu_evidence`
  status for off-board workflows.
- Harden plugin contract, upstream sync, validator edge-case, and local install
  smoke tests.

## 2026.07.05-codex.1

- Publish Codex-native CANNBot plugin package.
- Package 93 standalone skills from upstream commit
  `7def5becc576de40d0e13b0fddad8345e57540e0`.
- Add official CANNBot marketplace coverage metadata.
- Add Codex adapter design notes and local validation script.
