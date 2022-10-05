export PATH := $(PWD)/.venv/bin:$(PATH)
export VIRTUAL_ENV := $(PWD)/.venv
export PROJECT_NAME := $(shell ls */settings.py | xargs dirname)


.PHONY: deploy .env .venv
.DEFAULT_GOAL := help

.env:
	@echo 'PYTHONPATH="$(PROJECT_NAME)"' > .env

.venv:
	@python3.8 -m venv $(VIRTUAL_ENV)
	pip install --upgrade pip

.rm-venv:
	@if [ -d $(VIRTUAL_ENV) ]; then rm -rf $(VIRTUAL_ENV); fi

.install-hook:
	@echo "make lint" > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit

install: .venv .env .install-hook  ## Create .venv and install dependencies.
	pip install --upgrade pip
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

reinstall: .rm-venv install ## Remove .venv if exists, create a new .venv and install dependencies.

install-dev: install ## Create .venv and install dev dependencies.
	@if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

reinstall-dev: .rm-venv install-dev ## Remove .venv if exists, create a new .venv and install dev dependencies.

clean: ## Clean all caches file.
	@rm -rf dependencies .pytest_cache .coverage build/ dist/ $(PROJECT_NAME).egg-info/
	@find $(PROJECT_PATH) -name __pycache__ | xargs rm -rf
	@find tests -name __pycache__ | xargs rm -rf

lint: ## Apply lintings to ensure code quality.
	@black --line-length=100 --target-version=py38 --check .
	@flake8 --max-line-length=150 --ignore=E402,W503 --exclude .venv,build --max-complexity 5

format: ## Format code based in PEP8.
	@black --line-length=100 --target-version=py38 .

coverage: ## Test code and check coverage from tests.
	@pytest --cov-config=.coveragerc --cov=$(PROJECT_NAME) tests/ --cov-fail-under=90

static: ## Check static typing.
	@mypy $(PROJECT_NAME)

test:  ## Execute all unity tests.
	@pytest

build: ## Build package.
	@rm -rf build/ dist/ $(PROJECT_NAME).egg-info/
	@python -m build --wheel
	@echo "Twine check..."
	@twine check dist/*

publish: build ## Build package and publish to PyPi.
	@if [ ! -f $(PYPIRC) ]; then \
		echo "$(PYPIRC) not found. Please, create '$(HOME)/.pypirc' file with following content:"; \
		printf "\n[pypi]\nusername = __token__\npassword = <PyPI token>\n\n"; \
		exit 1; \
	fi
	@echo "Upload to Pypi..."
	@twine upload dist/*
	@rm -rf build/ dist/ $(PROJECT_NAME).egg-info/

help: ## Show documentation.
	@for makefile_file in $(MAKEFILE_LIST); do \
		grep -E '^[a-zA-Z_-]+:.*?##' $$makefile_file | sort | awk 'BEGIN {FS = ":.*?##"}; {printf ${COLOR}, $$1, $$2}'; \
	done
