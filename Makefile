.PHONY: install lint type-check test test-cov quality health-bot health-crawler run-crawler run-bot build clean

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest

install:
	$(PIP) install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check telegram_search/ apps/ tests/

lint-fix:
	$(PYTHON) -m ruff check telegram_search/ apps/ tests/ --fix

type-check:
	$(PYTHON) -m mypy telegram_search

test:
	$(PYTEST)

test-cov:
	$(PYTEST) --cov=telegram_search --cov-report=html

quality:
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

health-bot:
	$(PYTHON) -m telegram_search.health --component bot

health-crawler:
	$(PYTHON) -m telegram_search.health --component crawler

run-crawler:
	$(PYTHON) -m apps.crawler.main

run-bot:
	$(PYTHON) -m apps.bot.main

build:
	$(PYTHON) -m build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ htmlcov/
