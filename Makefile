PYTHON ?= python
VENV ?= .venv
PIP := $(VENV)/Scripts/python.exe

.PHONY: help install venv smoke lint up down logs clean

help:
	@echo "Available commands:"
	@echo "  make install      install project dependencies"
	@echo "  make venv         create a local virtual environment"
	@echo "  make smoke        run VM ingestion smoke test"
	@echo "  make lint         run Ruff lint checks"
	@echo "  make up           start local stack with Podman"
	@echo "  make down         stop local stack"
	@echo "  make logs         view running container logs"
	@echo "  make clean        remove generated caches and local artifacts"

venv:
	python -m venv $(VENV)
	@echo "Virtual environment created at $(VENV)"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

smoke:
	$(PYTHON) vm_ingestion_test.py --dry-run

lint:
	$(PYTHON) -m ruff check .

up:
	podman compose up -d --build

down:
	podman compose down

logs:
	podman compose logs -f

clean:
	rmdir /s /q .pytest_cache 2>nul || true
	rmdir /s /q __pycache__ 2>nul || true
	for /d %d in (.*) do @if "%d"==".git" goto :skip
	for /d %d in (*) do @if exist "%d\__pycache__" rmdir /s /q "%d\__pycache__"
	:skip
	@echo "Cleanup complete"
