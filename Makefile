PYTHON ?= python3
UPSTREAM ?= /tmp/cannbot-skills-update

.PHONY: validate test check-scripts ci smoke-install reinstall sync-upstream

validate:
	$(PYTHON) scripts/validate_codex_plugin.py --expected-name cannbot

test:
	$(PYTHON) -m unittest discover -s tests -v

check-scripts:
	$(PYTHON) -m py_compile scripts/validate_codex_plugin.py scripts/sync_upstream.py
	bash -n scripts/smoke_install.sh

ci: check-scripts validate test

smoke-install:
	bash scripts/smoke_install.sh

reinstall:
	codex plugin remove cannbot@local --json || true
	codex plugin add cannbot@local --json

sync-upstream:
	$(PYTHON) scripts/sync_upstream.py --upstream "$(UPSTREAM)" --apply
