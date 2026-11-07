# Convenience wrappers. Every target is a plain command you can also run directly.
# Activate your virtual environment first so `python` points at it.
PYTHON ?= python
IMAGE ?= app

.PHONY: setup run test lint format eval docker-build

setup:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m app $(PROMPT)

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

eval:
	$(PYTHON) -m evals.run

docker-build:
	docker build -t $(IMAGE) .
