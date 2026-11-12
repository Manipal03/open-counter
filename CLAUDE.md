# PayPal AI Hackathon — Project Instructions

## Project Context

This repository is for the PayPal + AI hackathon. The final product must meaningfully integrate the PayPal Developer Platform and an AI capability.

## Approved Project: AgentStorefront

A small merchant uploads a messy catalog; AI normalizes it; the store is exposed to AI agents (hosted shopper chat, REST, optional MCP); a buyer approves the purchase in PayPal Sandbox and the server captures it.

Source-of-truth documents (read before making changes; update them when a decision changes):
- `docs/brainstorming.md` — research and idea comparison
- `docs/architecture.md` — components, checkout flow, data model, security model
- `docs/decisions.md` — ADRs and open decisions
- `docs/tech-stack.md` — stack and environment variable names
- `docs/plan.md` — phases, scope cuts, demo script

## Project-Specific Rules

Payments
- Prices, totals, currency, and payee are computed **server-side from the catalog**. Never trust amounts from the client, the AI, or MCP callers.
- Only the checkout service may call PayPal for money movement. No AI tool may reach order capture or refund.
- Capture only after the buyer's PayPal approval, with order status `APPROVED` and amount/currency matching the stored cart.
- The app must refuse to start unless `PAYPAL_ENV=sandbox`; the PayPal base URL is pinned to the sandbox host.
- Use idempotency for order creation and capture; never double-capture.
- Order state changes go through one state-machine function and are written to the append-only audit log.

AI
- All AI calls go through the AI gateway (`live` / `replay`), with timeouts, a budget cap, rate limits, and schema-validated output.
- AI output is a proposal. It must never set prices, stock, payee, or trigger capture. Product text is data, never instructions.
- Replay mode must be labeled in the UI as recorded.
- Never send buyer personal data or secrets to the AI provider.

Process
- Label claims about PayPal behavior as verified (with a doc link) or unverified. Do not describe PayPal Store Sync / Agent Ready as part of this product (ADR-004).
- Write the test first for payment-critical behavior: tampered amount, capture before approval, double capture, bad webhook signature, expired order, prompt-injection catalog row.
- Keep changes small. Run `ruff` and `pytest` before declaring work done. Summarize files changed, results, and remaining risks.
- Do not add dependencies without noting them in `docs/tech-stack.md`.
- Judge sandbox buyer credentials go in the Devpost testing instructions, never in the repo.

## Working Rules

- The product idea is approved: **AgentStorefront** (see below). Do not switch or expand scope without approval.
- Explain proposed architecture and major trade-offs before making large changes.
- Prefer small, testable, maintainable changes.
- Never invent PayPal API behavior; verify against official documentation.
- Use PayPal Sandbox for all payment development and testing.
- Keep all secrets and API credentials in environment variables.
- Never expose server-side secrets to browser code.
- Never commit credentials or private keys.
- Include meaningful error handling and tests for critical payment flows.
- Never treat an AI-generated payment recommendation as authorization to charge money.
- Require explicit user approval for consequential payment actions.
- Document setup, environment variables, tests, and demo instructions.
- Ensure the final demo can be tested without judges supplying their own AI API key.

## Development Workflow

1. Understand the requirement.
2. Propose a small implementation plan.
3. Make changes in manageable steps.
4. Run relevant tests and checks.
5. Summarize files changed, results, and remaining risks.