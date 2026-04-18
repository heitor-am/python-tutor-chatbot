.PHONY: help install dev test lint fmt typecheck check docker-build docker-up docker-down deploy clean

help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies with uv"
	@echo "  dev          - Run Chainlit with auto-reload"
	@echo "  test         - Run tests with coverage"
	@echo "  lint         - Lint with ruff"
	@echo "  fmt          - Format with ruff"
	@echo "  typecheck    - Type check with mypy"
	@echo "  check        - Run lint + typecheck + test"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up    - Start docker-compose"
	@echo "  docker-down  - Stop docker-compose"
	@echo "  deploy       - Deploy to Fly.io"
	@echo "  clean        - Remove caches and build artifacts"

install:
	uv sync --all-extras

dev:
	uv run chainlit run app/main.py --host 0.0.0.0 --port 8000 -w

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy app

check: lint typecheck test

docker-build:
	docker build -t python-tutor-chatbot:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

deploy:
	flyctl deploy --remote-only --build-arg GIT_SHA=$$(git rev-parse HEAD)

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage build dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
