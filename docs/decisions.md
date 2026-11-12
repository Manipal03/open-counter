# Decision Log (ADRs)

Format: context → decision → alternatives → consequences. Status values: **Accepted**, **Provisional** (depends on a Phase 0 check), **Open**.

---

## ADR-001 — Project: AgentStorefront
**Status:** Accepted (user-approved 2026-10-12)

- **Context:** Eight finalists were compared in [brainstorming.md](brainstorming.md). Judges weigh technology, design, impact, innovation, and presentation equally. Two $5,000 honorable mentions are open: Best Use of PayPal + AI and Best Use of Agentic Commerce.
- **Decision:** Build AgentStorefront: a self-serve way for a small merchant to make a catalog browsable and buyable by AI agents, with PayPal checkout.
- **Alternatives considered:** ContractToCash (recommended on score and risk), Mandate, DisputeDesk, others.
- **Consequences:** Strongest fit for Agentic Commerce; higher build effort than ContractToCash; overlaps in spirit with PayPal's own Store Sync **[R]**; needs a judge-usable shopper agent. The scored gap to ContractToCash was within noise.

## ADR-002 — Human approval model
**Status:** Accepted

- **Decision:** The buyer's approval inside PayPal (`payer-action` link **[V]**) is the only authorization for a charge. The server captures only after the buyer returns, the order is `APPROVED`, and the amount and currency match the stored cart. No AI component can reach the capture call.
- **Alternatives:** Pre-authorized "autonomous" buying with spending rules (rejected: contradicts CLAUDE.md; larger surface; Mandate-style scope).
- **Consequences:** Every demo purchase requires a click-through in PayPal sandbox. That is also the clearest story for judges: agent proposes, human approves.

## ADR-003 — PayPal integration via direct REST (Orders v2), not the Agent Toolkit
**Status:** Accepted

- **Context:** The Python toolkit exposes 43 tools but its order tools are limited (create_order, get_order, pay_order, create_refund, get_refund **[V]**) and it targets agent-driven calls. We need strict control over idempotency, amount checks, and the approval gate.
- **Decision:** Implement a small `httpx` client for OAuth, create order, get order, capture, and refund. Use `api-m.sandbox.paypal.com` **[V]**.
- **Alternatives:** `paypal-agent-toolkit` (faster for invoices/catalog, but not needed); PayPal's remote MCP server (tool catalog unclear **[?]**, may expose only 2 tools **[R]**).
- **Consequences:** Slightly more code, much clearer tests. We can still mention the toolkit as an optional integration in the write-up. If time allows, a read-only toolkit use (e.g., shipment tracking) is a stretch item.

## ADR-004 — PayPal's own catalog is not the source of truth
**Status:** Accepted

- **Decision:** Our database owns products and prices. We do not sync to PayPal Catalog or rely on Store Sync.
- **Why:** Store Sync/Agent Ready access in the hackathon sandbox is unconfirmed **[?]**, and a local source of truth makes server-side price recomputation simple.
- **Consequences:** The "agent-ready" claim in the pitch refers to our MCP/REST interface, not to PayPal's programs. Do not claim otherwise.

## ADR-005 — AI provider strategy and "no judge key" policy
**Status:** Accepted (model choice Provisional)

- **Decision:**
  - All AI calls go through one **AI gateway** module with `live` and `replay` modes.
  - `live` uses a **server-side** key (Anthropic API) with a daily budget cap, per-IP rate limits, and timeouts. Default to a small, fast model for ingestion and the shopper agent (candidate: `claude-haiku-5-5`), configurable by environment variable; escalate to a larger model (`claude-sonnet-5-5`) only if quality demands it.
  - `replay` serves recorded responses for the scripted demo path and is shown in the UI as "recorded".
  - Judges never supply a key.
- **Alternatives:** Local open-weights model (heavier hosting, weaker tool use); bring-your-own-key (violates the requirement).
- **Consequences:** We pay for demo traffic, so budget caps are mandatory. Verify current pricing and model names at build time; I have not verified pricing.

## ADR-006 — Stack: Python + FastAPI, server-rendered UI, Render hosting
**Status:** Accepted (hosting Provisional)

- **Decision:** FastAPI backend; Jinja2 templates + HTMX; no SPA and no Node build step. Host on Render.
- **Why:** Python preferred; Windows-friendly; one deployable; fewer moving parts in 31 days; Render is a sponsor with credits **[R]**.
- **Alternatives:** React/Next.js (richer UI, extra build and deploy complexity); Fly/Railway (fine, no sponsor tie).
- **Consequences:** UI polish relies on careful CSS, not component libraries. Free-tier cold starts must be handled (warm-up before judging, or paid instance with credits).

## ADR-007 — Agent interface: shared tool layer with three front doors
**Status:** Accepted (MCP transport Provisional)

- **Decision:** Implement `search_products`, `get_product`, `create_checkout` once. Expose them via (1) the hosted shopper agent, (2) a REST API, (3) an MCP server. The hosted chat is the primary judge path.
- **Why:** Judges can't be expected to configure an MCP client. MCP still earns the "agentic commerce" credibility.
- **Open:** Python MCP SDK streamable-HTTP mounting inside FastAPI **[?]**. Fallback: run the MCP server as a separate process or ship it as a documented local demo only.

## ADR-008 — Database and money handling
**Status:** Accepted

- **Decision:** SQLAlchemy 2.x; SQLite locally; Postgres in production via `DATABASE_URL`. Money as integer minor units + ISO currency. Append-only `event` table for audit.
- **Consequences:** Alembic migrations may be skipped for the MVP (create tables on startup) to save time; revisit if the schema changes after deploy.

## ADR-009 — Testing strategy
**Status:** Accepted

- **Decision:** `pytest`. Unit tests for the state machine, totals recomputation, amount check, and AI output validation. HTTP mocking for PayPal in CI. AI tests use recorded fixtures (no network, no cost). A small set of **sandbox contract tests**, opt-in via a marker, run manually before submission. One end-to-end happy path and one failure path are scripted for the demo.
- **Must-have tests (payment-critical):** tampered amount rejected; capture blocked if not approved; double capture blocked; webhook with a bad signature rejected; expired order handled; prompt-injection catalog row cannot alter a total.

## ADR-010 — Licensing and repository
**Status:** Open

- The hackathon requires a public repo with an open-source license **[R]**. `LICENSE` is currently empty.
- **Recommendation:** MIT. **Needs from you:** the license choice and the copyright holder name. Not guessed.
- Branch naming: the repo is on `master`; the main branch is `main`. Decide before the first commit.

## ADR-011 — Judge access to the demo
**Status:** Accepted

- **Decision:** Hosted demo with a pre-seeded merchant and catalog. A sandbox **buyer** account is created for judges and its login is given in the Devpost "testing instructions" field, **not committed to the repo**. The README documents how anyone can create their own sandbox accounts and run locally.
- **Consequences:** The demo must survive a restart (seed on boot). The video must not depend on live AI succeeding (replay mode as a safety net).
