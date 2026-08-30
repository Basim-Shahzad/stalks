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

Entry point is `server/main.py`. Its `lifespan` handler creates DB tables, loads exchange/ticker reference data, kicks off a background thread for market-data fetching, and starts an APScheduler job runner. Routes are mounted under `/api/v1`; CORS is locked to `http://localhost:3000`.

**Known issue:** `main.py` imports `services.market_data_service`, which does not exist under `server/services/` (only `psx_service.py`, `psx_statement_parsing_service.py`, and `psx_statement_parsing_async_service.py` exist there). This looks like a stale import from a rename — be aware it may need fixing if touched.

### Mid-migration: two coexisting patterns

The server is being migrated from a flat, domain-scattered layout to a vertical-slice `features/` layout. **When adding new domain logic, follow the `features/` pattern, not the legacy one.**

- **Legacy flat pattern** (still what portfolios, transactions, market-data, and strategies use today):
  - `server/models/` — SQLAlchemy models (`Portfolio.py`, `Transaction.py`, etc.)
  - `server/schemas/` — Pydantic schemas
  - `server/crud/` — data-access functions
  - `server/dependencies/` — business logic, grouped by domain (`market_data/`, `portfolio/`, `strategies/`, `transactions/`)
  - `server/api/v1/endpoints/` — routers, wired together in `server/api/v1/api.py`
- **New vertical-slice pattern** (`server/features/<domain>/{models,schemas,repository,service,router}`):
  - `features/auth` is the fully-built reference implementation.
  - `features/base` holds the shared generic `repository`/`service`/exception-handling base classes that other features build on.
  - `features/portfolios` and `features/transactions` currently exist only as empty stub directories awaiting migration — don't assume logic lives there yet.

### Data layer
- `server/db/database.py` sets up async SQLAlchemy: `create_async_engine`, `async_sessionmaker`, and a shared `Base` that auto-adds `id`/`created_at`/`updated_at`. The `get_db()` dependency commits on success and rolls back on exception, per request.
- `peewee` is also a listed dependency but is not used by the active data layer (SQLAlchemy async is the real ORM) — likely vestigial.

### Auth
`server/features/auth/` issues self-signed JWT access + refresh tokens (argon2/pwdlib hashing), alongside Supabase config values (`supabase_url`/`supabase_key`) present in settings.

### Domain integrations
- Market data: `yfinance` plus scraping of the PSX site (`beautifulsoup4`/`curl-cffi`/`requests`) via `server/services/psx_service.py` and `server/dependencies/market_data/`.
- Transaction import: brokerage-statement PDF parsing via `pdfplumber`/`pdfminer-six`/`pypdfium2` in `psx_statement_parsing_service.py` (sync) and `psx_statement_parsing_async_service.py` (async).

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
