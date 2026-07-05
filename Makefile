PYTHON ?= python3
UPSTREAM ?= /tmp/cannbot-skills-update

.PHONY: validate test ci smoke-install reinstall sync-upstream

validate:
	$(PYTHON) scripts/validate_codex_plugin.py --expected-name cannbot

test:
	$(PYTHON) -m unittest discover -s tests -v

ci: validate test

smoke-install:
	bash scripts/smoke_install.sh

reinstall:
	codex plugin remove cannbot@local --json || true
	codex plugin add cannbot@local --json

sync-upstream:
	$(PYTHON) scripts/sync_upstream.py --upstream "$(UPSTREAM)" --apply
