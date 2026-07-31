# Marketplace Analytics Platform

A sanitized portfolio edition of a production-used marketplace analytics and automation workflow.

The private operational system supports 50 stores and more than 30,000 SKUs. Nightly data collection, reporting, dashboards, and pricing checks reduced daily analysis from several hours to approximately 20-30 minutes. This public edition keeps the architecture and engineering patterns while using synthetic data and excluding provider credentials, customer identifiers, production infrastructure, and private business rules.

## Stack

- Frontend: Next.js 15, React 19, TypeScript
- Backend: Python 3.12, FastAPI, Pydantic, async SQLAlchemy
- Data and async boundaries: PostgreSQL, Redis cache and job queue
- Quality: pytest, Ruff, mypy, TypeScript type checking, Next.js production build
- Operations: Docker Compose and GitHub Actions

## Architecture

```text
Next.js dashboard
       |
       v
FastAPI REST API ----> Analytics service ----> PostgreSQL repository
                              |                        |
                              +----> Redis cache       +----> daily metrics
                              |
                              +----> Redis sync queue -----> private worker boundary
```

The application uses explicit repository, cache, and queue protocols. Tests inject in-memory adapters, while Docker Compose uses PostgreSQL and Redis adapters.

## API

- `GET /health` - process health
- `GET /api/v1/dashboard?days=30` - aggregated marketplace metrics
- `POST /api/v1/sync` - idempotent sync request accepted into the queue

The sync endpoint requires an `Idempotency-Key` header. The public edition demonstrates the queue boundary but intentionally excludes private marketplace credentials and provider-specific workers.

## Local demo

The default mode is dependency-free and uses deterministic synthetic data:

```bash
cd backend
uv sync --dev
uv run uvicorn marketplace_analytics.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`.

## Docker Compose

```bash
docker compose up --build
```

The default Compose environment starts the complete service topology but keeps the API in deterministic demo mode, so the dashboard works immediately without credentials or customer data. The PostgreSQL and Redis adapters are included for architecture review; enabling services mode requires a project-specific migration and ingestion strategy that is intentionally outside this sanitized edition.

## Verification

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy src

cd ../frontend
npm run typecheck
npm run build
```

## Security and portfolio boundary

- No `.env`, API keys, OAuth state, customer data, production hosts, or database dumps are included.
- Provider credentials are environment-only and are not returned by API responses.
- All fixtures are synthetic.
- Authentication and provider-specific ingestion workers remain outside this public edition.
- This repository is portfolio code. No open-source license is granted unless a separate license file is added.

## Author

[Vladimir Bragin](https://github.com/Arbitr3103) - Full-Stack Developer
