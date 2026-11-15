.PHONY: lint test

lint:
	uvx ruff@0.17.3 format --check --exclude migrations/versions .
	uv run lint-imports

test:
	[ -f .env ] || cp .env.example .env
	docker compose up -d --wait
	uv run pytest
