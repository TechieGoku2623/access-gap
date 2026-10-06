export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: setup lint test research eval demo demo-build report record

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research
	$(UV) run ruff format --check src tests research
	$(UV) run mypy

test:
	$(UV) run pytest

research:
	$(UV) run python research/phase0/run_all.py

eval:
	$(UV) run python research/phase0/source_coverage/run.py
	$(UV) run python research/phase0/index_sensitivity/run.py
	$(UV) run python research/phase0/prevalence_bounds/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	$(UV) run access-gap demo

demo-build:
	$(UV) run access-gap demo-build

report:
	$(UV) run access-gap report --dest docs/report.html --therapy zolgensma

record:
	$(UV) run python scripts/record_demo.py
