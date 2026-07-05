#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/validate_codex_plugin.py --expected-name cannbot >/tmp/codex-cannbot-validate.json

if ! command -v codex >/dev/null 2>&1; then
  echo "codex CLI not found; plugin contract validated, install smoke skipped"
  exit 0
fi

codex plugin list --json >/tmp/codex-cannbot-plugins-before.json
codex plugin remove cannbot@local --json >/tmp/codex-cannbot-remove.json 2>/tmp/codex-cannbot-remove.err || true
codex plugin add cannbot@local --json >/tmp/codex-cannbot-add.json
codex plugin list --json >/tmp/codex-cannbot-plugins-after.json

python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
expected_version = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
data = json.loads(Path("/tmp/codex-cannbot-plugins-after.json").read_text(encoding="utf-8"))
plugins = data if isinstance(data, list) else data.get("installed", data.get("plugins", []))
matches = []
for plugin in plugins:
    name = plugin.get("name") or plugin.get("pluginId") or plugin.get("id")
    plugin_id = plugin.get("pluginId") or plugin.get("id") or ""
    if name in {"cannbot", "cannbot@local"} or str(plugin_id).startswith("cannbot@"):
        matches.append(plugin)
if not matches:
    raise SystemExit("cannbot plugin is not listed after install")
text = json.dumps(matches, ensure_ascii=False)
if str(root) not in text:
    raise SystemExit(f"cannbot plugin is listed but does not reference {root}")
for plugin in matches:
    if plugin.get("version") != expected_version:
        raise SystemExit(f"unexpected cannbot plugin version: {plugin.get('version')}")
print("cannbot plugin install smoke passed")
PY
