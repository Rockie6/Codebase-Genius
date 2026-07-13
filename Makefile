# Simple project automation

VENV_DIR := .venv
PY := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
UVICORN := $(VENV_DIR)/bin/uvicorn

.PHONY: help venv deps install run test test-diagram generate docker-build docker-run docker-stop docker-clean clean clean-venv

help:
	@echo "Targets:"
	@echo "  make install        # create venv and install deps"
	@echo "  make run            # run FastAPI server"
	@echo "  make test           # run smoke test"
	@echo "  make docker-build   # build Docker image"
	@echo "  make docker-run     # run Docker container"
	@echo "  make clean-venv     # remove .venv"
	@echo "  make clean          # clean outputs and venv"

venv:
	python3 -m venv $(VENV_DIR)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r codebase_genius/requirements.txt

install: deps

run:
	$(UVICORN) codebase_genius.api_server:app --host 0.0.0.0 --port 8000

test:
	$(PY) -m codebase_genius.scripts.smoke_test

test-diagram:
	$(PY) -m codebase_genius.scripts.test_diagram

docker-build:
	docker build -t codebase-genius:local codebase_genius

docker-run:
	docker run -d --rm --name codebase-genius-local -p 8000:8000 codebase-genius:local

docker-stop:
	-docker stop codebase-genius-local

docker-clean: docker-stop
	-docker rm codebase-genius-local

clean-venv:
	-rm -rf $(VENV_DIR)

clean: clean-venv
	-rm -rf codebase_genius/outputs/* outputs/*
