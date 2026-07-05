import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SmokeInstallTests(unittest.TestCase):
    def test_smoke_install_accepts_codex_list_installed_shape(self):
        version = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = tmp_path / "installed"
            fake_codex = tmp_path / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    set -euo pipefail
                    if [[ "$1 $2" != "plugin list" && "$1 $2" != "plugin remove" && "$1 $2" != "plugin add" ]]; then
                      echo "unexpected command: $*" >&2
                      exit 2
                    fi
                    case "$2" in
                      list)
                        if [[ -f "{state}" ]]; then
                          printf '%s\\n' '{{"installed":[{{"pluginId":"cannbot@local","name":"cannbot","version":"{version}","source":{{"path":"{ROOT}"}}}}]}}'
                        else
                          printf '%s\\n' '{{"installed":[]}}'
                        fi
                        ;;
                      remove)
                        rm -f "{state}"
                        printf '%s\\n' '{{}}'
                        ;;
                      add)
                        touch "{state}"
                        printf '%s\\n' '{{}}'
                        ;;
                    esac
                    """
                ),
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

            result = subprocess.run(
                ["bash", "scripts/smoke_install.sh"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("cannbot plugin install smoke passed", result.stdout)

    def test_smoke_install_temp_files_are_parallel_safe(self):
        version = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state = tmp_path / "installed"
            fake_codex = tmp_path / "codex"
            fake_codex.write_text(
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    set -euo pipefail
                    case "$2" in
                      list)
                        sleep 0.05
                        if [[ -f "{state}" ]]; then
                          printf '%s\\n' '{{"installed":[{{"pluginId":"cannbot@local","name":"cannbot","version":"{version}","source":{{"path":"{ROOT}"}}}}]}}'
                        else
                          printf '%s\\n' '{{"installed":[]}}'
                        fi
                        ;;
                      remove)
                        rm -f "{state}"
                        printf '%s\\n' '{{}}'
                        ;;
                      add)
                        touch "{state}"
                        printf '%s\\n' '{{}}'
                        ;;
                      *)
                        exit 2
                        ;;
                    esac
                    """
                ),
                encoding="utf-8",
            )
            fake_codex.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"

            procs = [
                subprocess.Popen(
                    ["bash", "scripts/smoke_install.sh"],
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )
                for _ in range(2)
            ]
            results = [proc.communicate(timeout=10) + (proc.returncode,) for proc in procs]

        for stdout, stderr, returncode in results:
            self.assertEqual(returncode, 0, stdout + stderr)
            self.assertIn("cannbot plugin install smoke passed", stdout)


if __name__ == "__main__":
    unittest.main()
