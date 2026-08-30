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

**Known issue:** `server/main.py` currently fails to import — it does `from features.market_data...` (both `get_tickers` and `config`), but that module was deleted. Anyone running the server needs to fix or remove those two imports (and the ticker-loading step in `lifespan` that used them) first.

Entry point is `server/main.py`. Its `lifespan` handler creates DB tables via `Base.metadata.create_all` and registers the app's exception handlers. Routes are mounted under `/api/v1` (wired up in `server/api/v1/api.py`); CORS is locked to `http://localhost:3000`.

### Vertical-slice `features/` layout

The whole server lives under `server/features/<domain>/`, each following (as much as the domain needs) `{models,schemas,repository,service,router}`:

- `features/auth` — JWT access/refresh tokens (argon2/pwdlib hashing), `User`/`RefreshToken` models.
- `features/portfolios` — portfolio CRUD and holdings computation (`holdings.py`).
- `features/transactions` — transaction CRUD, the watched-symbols event hooks (`events.py`), the PSX broker-statement PDF parser (`statement_parser.py`), and background-job tracking (`models/Job.py`, `jobs_router` mounted at `/api/v1/jobs`).
- `features/strategies` — bracket sell-strategy CSV basket generation (`strategy.py`, `sell/bracket.py`); has no model of its own, computes over transactions already persisted by `features/transactions`.
- `features/base` — shared generic `BaseRepository`/`BaseService`/domain-exception classes (`NotFoundException`, `ConflictException`, etc.) that the other features build on, plus the exception handlers registered in `main.py` that map them to HTTP responses.

`server/models/enums.py` (`ExchangeType`) is the one piece of shared kernel left outside `features/`, since it's used across multiple features.

There used to be a `features/market_data` (exchange config, Supabase-backed OHLCV CSV storage, ticker list). It was deleted; nothing has replaced its market-data-serving endpoints yet.

### Data layer
- `server/db/database.py` sets up async SQLAlchemy: `create_async_engine`, `async_sessionmaker`, and a shared `Base` that auto-adds `id`/`created_at`/`updated_at`. The `get_db()` FastAPI dependency commits on success and rolls back on exception, per request. All feature repositories are async and use this.
- `peewee`, `pandas`, and `yfinance` are still listed as dependencies in `server/pyproject.toml` but nothing in `server/` imports them anymore — leftover from removed/superseded code, not in active use.

### Domain integrations
- Live price lookups: on-demand PSX site scraping (`beautifulsoup4`/`requests`) via `server/services/psx_service.py`, used by portfolio holdings and strategies.
- Transaction import: brokerage-statement PDF parsing via `pdfplumber` in `features/transactions/statement_parser.py` (async, includes PSX sector lookup/caching), invoked as a background job (`features/transactions/service.py`) after `POST /transactions/{portfolio_id}/upload/pdf`.

### Config / env vars
No `.env.example` exists. `server/core/config.py` (pydantic-settings, extra env vars forbidden) currently defines: `SQLALCHEMY_DATABASE_URI`, `secret_key`, `algorithm` (default `HS256`), `access_token_expire_minutes`, `refresh_token_expire_days`, `app_env`. Supabase (`supabase_url`/`supabase_key`) was removed from `Settings` along with `features/market_data` — if a local `.env` still sets those keys, `Settings()` will fail validation on startup (extra inputs aren't permitted).

## Client architecture (Next.js App Router)

- `client/app/` uses the `(stalks)` route group for the authenticated app shell (`Header`, `Sidebar`) wrapping `portfolio/` (with dynamic `[portfolio_id]/`), `stocks/`, and `transactions/`. `login/` and `signup/` sit outside the route group.
- State/data pattern: **Zustand** for client-side state (`client/stores/`), **TanStack Query** for server state (query definitions in `client/lib/queries/`, split by domain: `marketQueries.ts`, `portfolioQueries.ts`, `transactionQueries.ts`), **TanStack Table** for tabular data (transactions), **Recharts** for charts, **HeroUI** as the component kit, **Tailwind v4** for styling.
- `client/hooks/` (older, e.g. `usePortfolioApi.ts`, `useTransactionApi.ts`) and `client/lib/hooks/` + `client/lib/queries/` (newer, TanStack Query–based) overlap in purpose — prefer the `lib/queries` pattern for new data-fetching code.
- `client/services/api.service.ts` is the axios-based API client.
- Path alias `@/*` resolves to the `client/` project root (see `client/tsconfig.json`).
- Note: `client/lib/queries/marketQueries.ts` calls `/market/data/{exchange}/{symbol}`, a server endpoint that no longer exists now that `features/market_data` was removed.

## Commit style

Follow conventional commits: `type(scope): description` (see `gcf.md` at the repo root for the fuller spec).
