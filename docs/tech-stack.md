# Tech Stack

## As built (2026-11-12, deadline-day minimal build)

Pinned in `requirements.txt` / `requirements-dev.txt`: fastapi 0.115.12, uvicorn[standard] 0.34.2, httpx 0.28.1, jinja2 3.1.6, python-multipart 0.0.20, pydantic 2.14.3, anthropic 2.8.0; dev: pytest 8.3.5, respx 0.22.0, ruff 0.17.4.

Changes from the plan below: stdlib `sqlite3` instead of SQLAlchemy/Postgres; plain JavaScript instead of HTMX; no MCP SDK. The env var `AI_PROVIDER_API_KEY` became `ANTHROPIC_API_KEY`, `AI_MODEL_DEFAULT`/`AI_MODEL_FALLBACK` became `AI_MODEL`, and `AI_DAILY_BUDGET_USD` became `AI_DAILY_CALL_LIMIT`. Webhook, session and rate-limit variables are unused. See `.env.example` for the current list.

## Original plan

Versions are intentions, not verified pins. Pin exact versions in the dependency file when scaffolding starts, after checking compatibility with the Python version in `.venv` (3.13.7).

| Layer | Choice | Why | Status |
|---|---|---|---|
| Language | Python 3.13 (`.venv` already created) | User preference; one language end to end | Accepted. Confirm all dependencies support 3.13 **[?]** |
| Web framework | FastAPI + Uvicorn | Async, typed, easy OpenAPI docs, good for tool endpoints | Accepted |
| Validation | Pydantic v2 | Structured AI output and API schemas | Accepted |
| HTTP client | httpx | Async, easy to mock (respx) | Accepted |
| Database | SQLAlchemy 2.x; SQLite (local), Postgres (prod) | Simple, portable | Accepted |
| UI | Jinja2 templates + HTMX; plain CSS (optionally Tailwind via CDN) | No Node/build step | Accepted |
| Live updates | Server-sent events for chat streaming | Simpler than WebSockets | Provisional |
| Agent interface | Official Python MCP SDK (streamable HTTP) + REST | Agentic Commerce credibility | Provisional **[?]** |
| AI | Anthropic API via a provider-agnostic gateway; Haiku-class default, Sonnet-class fallback; replay mode | Strong tool use; cost control | Provisional (see ADR-005) |
| PayPal | Direct REST: Orders v2 [V], Payments v2 refunds [V], Webhooks verify [V] | Control over idempotency and approval gate | Accepted |
| Testing | pytest, pytest-asyncio, respx | Mock PayPal and AI deterministically | Accepted |
| Lint/format | ruff | Fast, one tool | Accepted |
| Hosting | Render (web service + Postgres) | Sponsor credits **[R]**, Python-friendly | Provisional **[?]** free-tier limits |
| Local webhook testing | A tunnel tool, or test against the hosted URL | Webhooks need a public HTTPS URL | Open (choose in Phase 0) |
| CI | GitHub Actions: ruff + pytest (mocked) | Cheap safety net | Optional |

## Environment variables (names only; no values in the repo)

| Variable | Purpose | Exposed to browser? |
|---|---|---|
| `PAYPAL_CLIENT_ID` | Sandbox REST app client ID | No (server only for the MVP) |
| `PAYPAL_CLIENT_SECRET` | Sandbox REST app secret | **Never** |
| `PAYPAL_ENV` | Must be `sandbox`; the app refuses anything else | No |
| `PAYPAL_WEBHOOK_ID` | For signature verification | No |
| `APP_BASE_URL` | Public URL for `return_url` / `cancel_url` | Yes (non-secret) |
| `AI_MODE` | `live` or `replay` | No |
| `AI_PROVIDER_API_KEY` | Server-side AI key | **Never** |
| `AI_MODEL_DEFAULT` / `AI_MODEL_FALLBACK` | Model IDs | No |
| `AI_DAILY_BUDGET_USD` | Hard spend cap before falling back to replay | No |
| `RATE_LIMIT_PER_MINUTE` | Public demo protection | No |
| `DATABASE_URL` | SQLite or Postgres URL | **Never** |
| `SESSION_SECRET` | Signs cookies/sessions | **Never** |

A `.env.example` with names and empty values will be added at scaffolding time. `.env` is already git-ignored.

## Explicitly not using (and why)
- **React/Next.js:** extra build and deploy surface for a 31-day build.
- **PayPal Agent Toolkit as the payment layer:** see ADR-003.
- **PayPal Store Sync / Agent Ready:** unconfirmed sandbox access (ADR-004).
- **PayPal Vault, Subscriptions, Payouts:** not needed for the core flow; Vault has account-approval caveats **[V]**.
- **Local LLM hosting:** hosting cost and weaker tool use.
