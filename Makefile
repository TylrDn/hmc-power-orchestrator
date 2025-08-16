.PHONY: help setup lint test run fmt

help: ## print target help
@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## create venv & install deps
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

lint: ## run ruff
ruff hmc_orchestrator tests

test: ## run tests
pytest -q

run: ## example run
python -m hmc_orchestrator.cli list-lpars

fmt: ## format (placeholder)
@echo "no formatters configured"
