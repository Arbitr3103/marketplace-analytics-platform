.PHONY: test lint typecheck build verify

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

typecheck:
	cd backend && uv run mypy src
	cd frontend && npm run typecheck

build:
	cd frontend && npm run build

verify: test lint typecheck build
