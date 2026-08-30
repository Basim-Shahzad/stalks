# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

"Stalks" is a portfolio-tracking app for the Pakistan Stock Exchange (PSX). It has two active applications:

- `client/` — Next.js (App Router) frontend
- `server/` — FastAPI backend

`backend/` and `frontend/` at the repo root are the **legacy** Flask/Vite predecessors, excluded from context via `.claudeignore`. Do not read or edit them unless the user explicitly asks.

There are **no tests and no CI configured anywhere in this repo** — don't assume a test suite exists, and don't invent test commands.

## Commands

### Client (run from `client/`)
- `npm run dev` — start dev server (Next.js with Turbopack)
- `npm run build` — production build
- `npm run start` — run production build
- `npm run lint` / `npm run lint:fix` — ESLint (`eslint-config-next`)

No test script is configured.

### Server (run from `server/`)
Dependencies are managed with `uv` (`uv.lock` present, `requirements.txt` also present). No lint, format, or test tooling is configured (no ruff/black/pytest config anywhere) — don't assume one exists.

## Server architecture (FastAPI)

Entry point is `server/main.py`. Its `lifespan` handler creates DB tables and loads exchange/ticker reference data. Routes are mounted under `/api/v1`; CORS is locked to `http://localhost:3000`. Market data is no longer fetched on a schedule from this app — that's owned by a separate microservice now; this app only reads/serves stored OHLCV data.

### Mid-migration: two coexisting patterns

The server is being migrated from a flat, domain-scattered layout to a vertical-slice `features/` layout. **When adding new domain logic, follow the `features/` pattern, not the legacy one.**

- **New vertical-slice pattern** (`server/features/<domain>/{models,schemas,repository,service,router}`):
  - `features/auth`, `features/portfolios`, and `features/transactions` are fully migrated — repository/service/router, properly async against the `AsyncSession`-based `get_db`. `features/base` holds the shared generic `repository`/`service`/exception-handling base classes the others build on.
  - `features/transactions` also owns the PDF statement-parser (`statement_parser.py`), the watched-symbols event hooks (`events.py`), and the job-status router (`jobs_router`, mounted at `/api/v1/jobs`) — these were bundled in because they only ever served transactions.
- **Legacy flat pattern** (still what market-data and strategies use today):
  - `server/dependencies/market_data/`, `server/dependencies/strategies/` — business logic
  - `server/schemas/MarketDataSchema.py`
  - `server/api/v1/endpoints/market_data.py`, `strategies.py` — routers, wired together in `server/api/v1/api.py`
  - `server/models/enums.py` (`ExchangeType`) remains shared kernel, used by both features and the legacy code — it isn't owned by any one feature.

### Data layer
- `server/db/database.py` sets up async SQLAlchemy: `create_async_engine`, `async_sessionmaker`, and a shared `Base` that auto-adds `id`/`created_at`/`updated_at`. The `get_db()` dependency commits on success and rolls back on exception, per request.
- `peewee` is also a listed dependency but is not used by the active data layer (SQLAlchemy async is the real ORM) — likely vestigial.

### Auth
`server/features/auth/` issues self-signed JWT access + refresh tokens (argon2/pwdlib hashing), alongside Supabase config values (`supabase_url`/`supabase_key`) present in settings.

### Domain integrations
- Market data: on-demand live price scraping of the PSX site (`beautifulsoup4`/`requests`) via `server/services/psx_service.py`, used by portfolio holdings and strategies. Historical OHLCV storage/reads live in `server/dependencies/market_data/`; the scheduled fetch that populates it is a separate microservice, not this app.
- Transaction import: brokerage-statement PDF parsing via `pdfplumber` in `features/transactions/statement_parser.py` (async, includes PSX sector lookup/caching), invoked as a background job (`features/transactions/service.py`) after `POST /transactions/{portfolio_id}/upload/pdf`.

### Config / env vars
No `.env.example` exists. `server/core/config.py` (pydantic-settings) reads these from `.env`:
`SQLALCHEMY_DATABASE_URI`, `secret_key`, `algorithm` (default `HS256`), `access_token_expire_minutes`, `refresh_token_expire_days`, `app_env`, `supabase_url`, `supabase_key`.

## Client architecture (Next.js App Router)

- `client/app/` uses the `(stalks)` route group for the authenticated app shell (`Header`, `Sidebar`) wrapping `portfolio/` (with dynamic `[portfolio_id]/`), `stocks/`, and `transactions/`. `login/` and `signup/` sit outside the route group.
- State/data pattern: **Zustand** for client-side state (`client/stores/`), **TanStack Query** for server state (query definitions in `client/lib/queries/`, split by domain: `marketQueries.ts`, `portfolioQueries.ts`, `transactionQueries.ts`), **TanStack Table** for tabular data (transactions), **Recharts** for charts, **HeroUI** as the component kit, **Tailwind v4** for styling.
- `client/hooks/` (older, e.g. `usePortfolioApi.ts`, `useTransactionApi.ts`) and `client/lib/hooks/` + `client/lib/queries/` (newer, TanStack Query–based) overlap in purpose — prefer the `lib/queries` pattern for new data-fetching code.
- `client/services/api.service.ts` is the axios-based API client.
- Path alias `@/*` resolves to the `client/` project root (see `client/tsconfig.json`).

## Commit style

Follow conventional commits: `type(scope): description` (see `gcf.md` at the repo root for the fuller spec).
