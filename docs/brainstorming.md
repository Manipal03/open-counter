# PayPal + AI Hackathon — Brainstorming Report

*Prepared 2026-10-12. Ideation only: no code, dependencies, or scaffolding were created.*

## 0. How to read this report

Evidence labels used throughout:

| Label | Meaning |
|---|---|
| **[V]** | Verified on an official PayPal page (or the official hackathon page) that I fetched. Link given. |
| **[R]** | Reported by a secondary source only (news, blog, third-party directory). Treat as indicative. |
| **[H]** | My hypothesis or judgment. Not verified. |
| **[?]** | Open question. Must be confirmed in the docs or the sandbox before committing. |

Limits of the research:
- The Devpost rules page returned HTTP 403 to my fetch tool. Hackathon facts below come from PayPal's community blog **[V]** plus third-party summaries **[R]**. **Read the official rules yourself before committing to an idea.**
- Several PayPal doc pages are endpoint indexes only. They don't state limits, sandbox behavior, or webhook event names. Those are marked **[?]**.
- Market/competitor claims come from vendor marketing and aggregators. I could not verify win rates, pricing, or adoption figures.

---

## 1. Hackathon facts and what they imply

| Item | Finding | Label / source |
|---|---|---|
| Theme | "Build something new that combines PayPal and AI." No prescribed tracks. The project "must meaningfully use both PayPal and AI." | **[V]** [PayPal community blog](https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/) |
| Dates | Opens Oct 1, 2026. Closes Nov 12, 2026 (blog gives only the date; other sources say noon or 2 p.m. PT). Winners about Dec 21. | **[V]** blog / **[R]** [GenAI Magazine](https://thegenaimagazine.com/paypal-ai-hackathon-2026-ideas-deadline-prizes). **Exact close time is inconsistent. Check Devpost.** |
| Time left | About 31 days from today (Oct 12) to Nov 12. | Calculated |
| Main prizes | 1st $12,000, 2nd $8,000, 3rd $5,000. | **[V]** blog |
| Honorable mentions ($5,000 each) | Most Creative, Most Impactful, Best Demo Delivery, **Best Use of PayPal + AI**, **Best Use of Agentic Commerce**. | **[V]** blog |
| Sponsor prizes | AG Grid, APIMatic, Bryntum, Channel3, Render (credits). One project can win one main/honorable prize plus one sponsor prize. | **[V]** blog / **[R]** secondary |
| Judging | Five equally weighted criteria: Technological Implementation, Design, Potential Impact, Innovation, Presentation. A pass/fail gate first checks theme fit and use of the required tech. | **[R]** [Devpost via search snippet](https://paypalaihackathon.devpost.com/rules), [GenAI Magazine](https://thegenaimagazine.com/paypal-ai-hackathon-2026-ideas-deadline-prizes) |
| Submission | Public GitHub repo with an open-source license and setup instructions, a working hosted demo or run instructions, a YouTube video under 3 minutes, and a written description. Mockups don't count. | **[R]** secondary summaries. **Confirm on Devpost.** |
| Judges' effort | Judges may not run the project and may judge only the description, images, and video. | **[R]** search summary of the rules |
| Existing projects | Allowed if significant progress is made during the hackathon. | **[R]** |
| Sandbox | Free PayPal sandbox is used. No real money moves. | **[R]** repo descriptions; also required by this project's CLAUDE.md |

**Implications [H]:**
1. **The 3-minute video is probably the most important artifact.** The demo must tell its story in 3 minutes, and it must look good even if the judges never run it.
2. **The hosted demo must work without anyone's API key.** Plan for a server-side AI key with spend limits plus a deterministic "replay" mode, so the demo works if the AI provider is down. Decide this early.
3. **Crowding.** The organizers' idea list is public ([GenAI Magazine's 10 ideas](https://thegenaimagazine.com/paypal-ai-hackathon-2026-ideas-deadline-prizes) **[R]**): gift-finder shopping agent, invoice chaser, churn saver, dispute copilot, ask-your-payments dashboard, deposit bookings, creator splitter, chat-to-pay shop, price-watch buyer, integration copilot. **Expect many entries on these exact ideas.** One existing entry I found: an agent escrow with an AI judge ([JudgePay](https://github.com/Techfrontiers/judgepay-paypal) **[V]** on GitHub; uses Orders authorize, Payments capture/void, Payouts). That makes "AI agent escrow" a crowded space.

---

## 2. PayPal capabilities researched

| Capability | What the official docs show | Notes / open questions |
|---|---|---|
| **Orders v2** | Create an order; intent `CAPTURE` or `AUTHORIZE`; buyer approves via a `payer-action` link; server captures. An authorize hold is valid 29 days. A created order stays `CREATED` only 3 hours. **[V]** [Standard flow](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/) | Idempotency (`PayPal-Request-Id`) not covered on that page. **[?]** |
| **Payments v2** | Get, capture, reauthorize, void an authorization; get and refund a capture. **[V]** [Payments v2](https://developer.paypal.com/docs/api/payments/v2/) | Honor-period details not on the page. **[?]** |
| **Payouts v1** | Create batch, show batch, show item, cancel unclaimed item. `sender_batch_id` gives idempotency. Error simulation by putting `ERRPYO002` in the item note. Statuses PENDING, PROCESSING, SUCCESS, DENIED, CANCELED. **[V]** [API](https://developer.paypal.com/docs/api/payments.payouts-batch/v1/), [integration guide](https://developer.paypal.com/docs/payouts/standard/integrate-api/) | The guide lists "verify a live business account" as a prerequisite. **[?] Whether sandbox Payouts works on a fresh sandbox business account must be tested on day 1.** |
| **Invoicing v2** | Create, send, remind, cancel; record payments and refunds; QR code; templates; recurring series; search; auto-reminder config. **[V]** [Invoicing v2](https://developer.paypal.com/docs/api/invoicing/v2/) | Invoice webhook event names not verified (the event-names page returned 404 to my fetch). **[?]** |
| **Subscriptions v1** | Plans, subscriptions, suspend, cancel, reactivate, revise plan/quantity, capture, list transactions. **[V]** [Subscriptions v1](https://developer.paypal.com/docs/api/subscriptions/v1/) | Sandbox simulation of renewals/failures **[?]** |
| **Customer Disputes v1** | List and show disputes; provide evidence; accept claim; appeal; make/accept/deny offer; send message. **Sandbox-only** endpoints to adjudicate a dispute and force `require-evidence`, so outcomes can be simulated. **[V]** [Disputes v1](https://developer.paypal.com/docs/api/customer-disputes/v1/) | How to create realistic sandbox disputes in bulk **[?]** |
| **Transaction Search v1** | List transactions, balances, balance/net summary, daily summary. **[V]** [Transaction Search](https://developer.paypal.com/docs/api/transaction-search/v1/) | Date-range limits and sandbox data delay not stated. **[?]** |
| **Vault (Orders v2)** | Save a PayPal/card payment method with `store_in_vault: ON_SUCCESS`, then charge later using the vault ID, even when the payer isn't present. **[V]** [Vault](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/save-payment-methods/) | Page says you need an Expanded Checkout integration and PayPal approval for card saving. **[?] Treat Vault as a risk, not a given.** |
| **Webhooks** | Verify-signature endpoint; simulate-event endpoint; event-types listing. **[V]** [Webhooks v1](https://developer.paypal.com/docs/api/webhooks/v1/) | Exact event names per product **[?]** |
| **Agent Toolkit** | `pip install paypal-agent-toolkit` (Python 3.11+ per search results **[R]**). Frameworks: OpenAI Agents SDK, LangChain, Vercel AI SDK, MCP. **43 tools**: invoices (20), orders/payments (5: create_order, get_order, pay_order, create_refund, get_refund), disputes (3), shipment tracking (3), catalog (3), subscriptions (7), reporting (2). **No payouts tools.** Defaults to `SANDBOX`. **[V]** [GitHub](https://github.com/paypal/agent-toolkit), [quickstart](https://developer.paypal.com/ai-tools/toolkit) | Python version pins in the quickstart look dated. **[?]** |
| **MCP server** | Remote: sandbox `https://mcp.sandbox.paypal.com`, production `https://mcp.paypal.com`; transports `/sse` and `/http`; bearer-token auth using client ID/secret. Local: `npx -y @paypal/mcp --tools=all` (needs Node 18+). **[V]** [MCP quickstart](https://developer.paypal.com/ai-tools/mcp-server) | A PayPal "limited release" page reportedly says the remote server has only 2 tools. **[R]** [PayPal limited-release page](https://developer.paypal.com/limited-release/agents/). **[?] Verify the tool catalog.** The local server needs Node, which a Python-only stack doesn't otherwise have. |
| **Agentic commerce programs** | "Agent Ready" (merchants accept agent-initiated payments) and "Store Sync" (catalog sent to AI surfaces); Perplexity "Instant Buy" is the most developed integration. **[R]** [Digital Commerce 360](https://www.digitalcommerce360.com/2025/10/28/paypal-agentic-commerce-ai-driven-shopping-services/), [PayPal newsroom](https://newsroom.paypal-corp.com/2025-11-PayPal-and-Perplexity-Launch-Instant-Buy). One source says OpenAI retired ChatGPT Instant Checkout on 2026-03-04; sources conflict. **[R]** | **[?] I found no developer docs showing that hackathon participants can access Agent Ready or Store Sync in the sandbox. Do not build on them until confirmed.** |

**Industry context for agentic commerce [R]:** Google's AP2 uses signed "mandates" (intent mandate, cart mandate) as proof of human authorization and doesn't move money itself ([AP2 spec](https://ap2-protocol.org/ap2/specification/), [PYMNTS](https://www.pymnts.com/artificial-intelligence-2/2025/google-unveils-a-payment-protocol-for-ai-driven-commerce/)). Visa and Mastercard have agent-payment programs ([paz.ai summary](https://www.paz.ai/glossary/agent-payments-protocol-ap2)). **Gap [H]:** I found no sign of an open, PayPal-native "authorization policy" layer built on PayPal Orders. This is a hypothesis, not a finding, since my search was shallow.

---

## 3. Existing products and gaps (competitive scan)

| Area | Existing products found | Gap / implication |
|---|---|---|
| AI dispute handling | [Chargeflow](https://www.chargeflow.io/integrations/paypal) and [Justt](https://thepaypers.com/fraud-and-fincrime/news/justt-upgrades-ai-chargeback-management) both support PayPal disputes **[R]** (vendor claims). | A dispute copilot is **not novel**. Only a clear angle (transparency, small seller, human-in-the-loop) could differentiate. |
| AR / invoice chasing | [Chaser](https://erpresearch.com/erp-add-ons/ar-collections/chaser), Upflow, Kolleno, Invoiced **[R]**. Chaser's "AI" is mostly email drafting per one source. Aimed at SMB/mid-market (Chaser from £199/mo). | Plain reminders are a crowded category. The gap **[H]** is *upstream*: turning a contract into the right invoices. |
| Agent escrow | [JudgePay PayPal Edition](https://github.com/Techfrontiers/judgepay-paypal) **[V]** (hackathon entry). | Avoid, or differentiate sharply. |
| Agent payment standards | AP2, ACP, Visa/Mastercard programs **[R]**. | Standards define authorization *proofs*, but a PayPal-specific policy and approval UX looks open **[H]**. |
| Hackathon crowd | Organizer idea list **[R]**. Other repos seen are early-stage (e.g., [Sai/Aarav](https://github.com/aaravbodla/PAYPAL-AI-HACKATHON): no app yet **[V]**). | Differentiation will come from execution quality and a distinct angle, not from the domain. |

---

## 4. Candidate pool (22 ideas)

Verdicts after a critical first pass. "Generic" = likely to be built by many teams; "Weak PayPal" = PayPal is a bolt-on.

| # | Idea | Verdict | Reason |
|---|---|---|---|
| 1 | Gift-finder shopping agent with PayPal checkout | Dropped | Generic. On the organizer list. Product search and data aren't PayPal-related. |
| 2 | Price-watch auto-buyer | Dropped | Generic. Needs real product feeds. Hard to demo deterministically. |
| 3 | Invoice-chasing assistant | Merged into D | Crowded; plain reminders are commodity. |
| 4 | Subscription churn saver | Dropped | Needs churn data the sandbox can't realistically supply. Fake data would look weak. |
| 5 | "Ask your payments" analytics chat | Dropped | Generic; sandbox data is thin; only AG Grid synergy. |
| 6 | Chat-to-pay shop from photos | Dropped | Generic; PayPal is just a payment link. |
| 7 | Voice/phone ordering → PayPal invoice | Dropped | Telephony integration eats the time; not PayPal-central. |
| 8 | Agent-to-agent escrow marketplace | Dropped | Existing entry (JudgePay). |
| 9 | Micropayments for AI agents (pay-per-API-call) | Dropped | PayPal fees likely make micropayments impractical. **[H]**, unverified. |
| 10 | Kids' allowance/chores agent | Dropped | Weak AI necessity. |
| 11 | Booking assistant with deposits | Dropped | Generic; organizer list. |
| 12 | Nonprofit giving concierge with recurring Vault donations | Dropped | Vault risk; AI is a thin layer. |
| 13 | Creator/marketplace revenue splitter | Merged into E | Same Payouts workflow. |
| 14 | Cross-border price and currency advisor | Dropped | Weak PayPal API use. |
| **A** | **Mandate**: policy and approval gateway for AI agents that spend via PayPal | **Finalist** | Targets agentic commerce and this project's own approval rule. |
| **B** | **AgentStorefront**: turn any small shop's catalog into an agent-buyable store | **Finalist** | Merchant-side agentic commerce. |
| **C** | **DisputeDesk**: evidence-building copilot for PayPal disputes | **Finalist** | Strong PayPal API fit. Competitors exist. |
| **D** | **ContractToCash**: contract → milestone invoices → collections | **Finalist** | Upstream AI value; Invoicing-central. |
| **E** | **ReimburseAI**: receipts → policy check → approval → Payouts | **Finalist** | Payouts-central; clear approval step. |
| **F** | **PotLuck**: all-or-nothing group purchases with authorize holds | **Finalist** | Unusual use of PayPal's auth/capture/void. |
| **G** | **SandboxPilot**: AI that tests a PayPal integration against sandbox scenarios | **Finalist** | Developer-tool angle; sponsor synergy (APIMatic, Postman). |
| **H** | **HaggleNet**: buyer and seller agents negotiate, PayPal settles | **Finalist** | Flashy demo; weakest PayPal depth (kept deliberately to show the trade-off). |

---

## 5. Finalists (8)

Complexity scale: low ≈ 1–2 person-weeks, medium ≈ 3–4, high ≥ 5. These are rough **[H]** estimates against a 31-day window and don't account for your team size, which I don't know.

---

### A. Mandate — a spending-policy gateway for AI agents

**Pitch:** A guard layer between any AI shopping/ops agent and PayPal that turns "agent wants to buy X" into a policy-checked, human-approved, auditable PayPal order.

- **Target users / problem:** Developers and small teams letting AI agents buy things (subscriptions, supplies, ad credit). Agents can be wrong or prompt-injected, and there's no simple way to bound what they spend or prove who approved what.
- **Solution / journey:**
  1. User sets policies (per-order cap, monthly budget, allowed merchants/categories).
  2. An agent submits a purchase proposal via an HTTP API or MCP tool.
  3. Mandate validates it against policy. An AI risk reviewer flags suspicious items (inflated price, odd payee, instructions embedded in a product page) and routes it.
  4. In-policy orders may auto-approve only under a rule the user explicitly pre-authorized; everything else needs a click.
  5. Approval creates a PayPal order; the buyer approves in PayPal; the server captures.
  6. An audit log records the chain.
- **Why it matters:** Agentic commerce adoption depends on trust and control. AP2-style mandates exist as concepts **[R]**, but a concrete, tryable PayPal flow looks rare **[H]**.
- **How PayPal is central:** Every spend ends in a real sandbox Orders flow. Payer approval and capture are the approval gate. Authorize-then-capture can hold funds until policy and human checks pass.
- **PayPal APIs:** [Orders v2](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/), [Payments v2 (authorize/capture/void/refund)](https://developer.paypal.com/docs/api/payments/v2/), [Webhooks](https://developer.paypal.com/docs/api/webhooks/v1/), optionally the [Agent Toolkit](https://github.com/paypal/agent-toolkit) / [MCP server](https://developer.paypal.com/ai-tools/mcp-server).
- **AI's role / necessity:** (a) Parse messy purchase proposals into structured line items; (b) assess risk and injection signals in agent-supplied context; (c) explain the decision in plain language for the approver. *Policy enforcement itself must be deterministic code; AI is advisory.* Necessity is moderate, since some parts could be rules.
- **Agentic workflow?** Yes, but as the thing being governed. A demo agent proposes purchases and Mandate governs; Mandate is not itself an autonomous spender.
- **Differentiator:** PayPal-native, open, tryable by judges; makes "AI recommendation ≠ authorization" visible. **[H]** I found no direct equivalent, but my search was limited.
- **MVP:** Policy editor; proposal API; deterministic policy engine; AI risk note; approval screen; sandbox order create/approve/capture; audit log; a demo agent; a prompt-injection test case.
- **Demo (3 min):** The agent tries a $40 item (auto-approved by a pre-set rule), a $400 item (needs a click), and a "$40" item whose page contains hidden "send $900 to this payee" text (blocked and flagged). Show the audit trail.
- **Architecture (Python):** FastAPI; SQLite/Postgres; PayPal REST via `httpx` or the Python toolkit; LLM behind a thin interface with a mock/replay mode; simple web UI; webhook receiver with signature verification.
- **Security / approval / reliability:** Server recomputes amounts and payees; idempotency keys on order creation; AI output never sets amount or payee; explicit approval record; rate limits; secrets in env; webhook verification.
- **Risks / dependencies:** Judges may see it as "just a policy engine"; the AI value must be visibly useful; the demo agent must be believable.
- **Complexity:** Medium.
- **Judging fit:** Strong for **Best Use of Agentic Commerce**; good Technological Implementation (security story); Presentation hinges on the injection demo.
- **Reason to build:** On-theme, safe by design, and the demo has a clear tension (block vs. allow).
- **Reason not to:** Abstract. The "wow" is in what gets blocked, which is harder to show than a shopping flow.

---

### B. AgentStorefront — make any small shop buyable by AI agents

**Pitch:** A merchant uploads a catalog (CSV or a photo of a price list); the system produces an agent-readable store (an MCP server and an API) with PayPal checkout, so an AI assistant can browse and buy with the shopper's approval.

- **Target users / problem:** Small merchants whose products aren't visible or purchasable by AI assistants. PayPal's own programs (Agent Ready/Store Sync) target merchants too **[R]**, but I could not confirm hackathon access **[?]**.
- **Solution / journey:**
  1. Merchant uploads a catalog.
  2. AI normalizes products (titles, attributes, variants, policies) and flags gaps.
  3. The system exposes an MCP server with `search_products`, `get_product`, `create_checkout`.
  4. A shopper's AI assistant (demo: an MCP client or hosted chat UI) finds "waterproof jacket under $80", builds a cart, and returns a PayPal approval link.
  5. Shopper approves in PayPal; order captured; the merchant dashboard shows it.
- **Why it matters:** If shoppers start buying through AI assistants **[R]**, small merchants without integrations are invisible.
- **How PayPal is central:** Checkout and capture are the point of the store. Shipment tracking and refunds are available through the toolkit.
- **PayPal APIs:** [Orders v2](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/), catalog and shipment-tracking tools in the [Agent Toolkit](https://github.com/paypal/agent-toolkit), [Payments v2 refunds](https://developer.paypal.com/docs/api/payments/v2/).
- **AI's role / necessity:** Catalog cleanup and enrichment from messy input (hard without AI); natural-language product matching; a shopper-side agent that proposes a cart. Necessity: high for ingestion, medium for search.
- **Agentic workflow?** Yes. The shopper agent calls tools; checkout always ends with human approval.
- **Differentiator:** Self-serve and open; works from a spreadsheet. Existing programs target established PayPal merchants **[R]**. **[H]** Not verified as unique.
- **MVP:** CSV ingest plus AI normalization; MCP server (Python MCP SDK suitability **[?]**); cart and order creation; approval link; merchant order view.
- **Demo:** Upload a messy CSV; the catalog is cleaned in seconds; ask an AI client for a gift under $50; it browses and presents a PayPal approval link; approve; the order appears in the merchant view.
- **Architecture:** FastAPI backend plus a Python MCP server module; Postgres/SQLite; LLM for ingestion and the shopper agent; PayPal sandbox orders; Render for hosting (sponsor-prize alignment).
- **Security:** Server recomputes totals from its own catalog; the agent cannot set prices; approval via PayPal; MCP auth; rate limiting.
- **Risks:** Judges need a shopper agent that works without their own key, so a hosted shopper UI is required (extra work). MCP client setup is hard for judges. Search quality on a small catalog.
- **Complexity:** Medium–High.
- **Judging fit:** Strong for **Best Use of Agentic Commerce**; good Impact story; Design depends on the shopper UI.
- **Reason to build:** Clear, relatable story with a real two-sided demo.
- **Reason not to:** Overlaps PayPal's own Store Sync direction **[R]**, and AI-shopping hype invites "me too" comparisons.

---

### C. DisputeDesk — evidence copilot for PayPal disputes

**Pitch:** A small seller connects PayPal; the app reads each dispute, assembles evidence from order and shipping data, drafts a response, and submits only after the seller approves.

- **Target users / problem:** Small sellers who lose disputes by missing deadlines or submitting weak evidence.
- **Solution / journey:** New dispute found (webhook or poll) → AI classifies the reason and lists required evidence → pulls transaction and tracking data → drafts a response citing the evidence → seller reviews, edits, approves → the app submits evidence or accepts the claim.
- **Why it matters:** Disputes cost sellers revenue and time. Larger vendors already sell this (Chargeflow, Justt) **[R]**, so the opportunity is the small seller **[H]**.
- **How PayPal is central:** The disputes lifecycle is the product: reading disputes, evidence, offers, accept claim.
- **PayPal APIs:** [Customer Disputes v1](https://developer.paypal.com/docs/api/customer-disputes/v1/) (including sandbox adjudicate/require-evidence), [Transaction Search](https://developer.paypal.com/docs/api/transaction-search/v1/), disputes and shipment-tracking tools in the [Agent Toolkit](https://github.com/paypal/agent-toolkit), [Webhooks](https://developer.paypal.com/docs/api/webhooks/v1/).
- **AI's role / necessity:** Reads unstructured evidence (messages, receipts, carrier info), classifies, drafts persuasive and accurate responses, and recommends accept vs. contest with reasoning. High necessity.
- **Agentic workflow?** Moderately: a multi-step investigator; submission requires human approval.
- **Differentiator:** Small-seller focus, human approval, transparent reasoning. **Not novel as a category.**
- **MVP:** Dispute inbox; AI triage; evidence checklist; draft response; approve-and-submit; deadline countdown.
- **Demo:** Create a sandbox dispute, force a state with the sandbox-only endpoints, show triage, draft, and approval, then adjudicate it.
- **Architecture:** FastAPI with polling or webhooks; DB; LLM with structured output; PayPal sandbox; simple dashboard.
- **Security:** Approval before any submission; minimize PII sent to the LLM; audit log; deadline alerts.
- **Risks:** **[?]** Producing realistic sandbox disputes and evidence data; the demo may look staged. Funded competitors.
- **Complexity:** Medium.
- **Judging fit:** High on Technological Implementation and Impact; weaker on Innovation; qualifies for **Best Use of PayPal + AI**.
- **Reason to build:** Deep, honest PayPal API use with real business value.
- **Reason not to:** Crowded and on the organizer list, so judges may see many similar entries.

---

### D. ContractToCash — from contract to milestone invoices to collection

**Pitch:** Upload a freelance contract or SOW; AI extracts payment terms and milestones, drafts matching PayPal invoices, and manages reminders according to the contract.

- **Target users / problem:** Freelancers and small agencies who invoice by hand and chase payments inconsistently, often not following their own contract terms.
- **Solution / journey:** Upload PDF → AI extracts parties, milestones, amounts, due dates, late-fee terms, with clause citations → user reviews a structured summary → the app creates draft invoices (or a recurring series) → user approves sending → reminders go out on the contract's schedule → payment status syncs back.
- **Why it matters:** Late payment is a common small-business problem **[H]** (no figures verified). Existing AR tools handle reminders but not contract understanding **[H]**.
- **How PayPal is central:** PayPal Invoicing is the delivery and collection channel, including reminders, QR codes, and payment recording.
- **PayPal APIs:** [Invoicing v2](https://developer.paypal.com/docs/api/invoicing/v2/), [Webhooks](https://developer.paypal.com/docs/api/webhooks/v1/), [Agent Toolkit invoice tools](https://github.com/paypal/agent-toolkit) (20 invoice tools **[V]**).
- **AI's role / necessity:** Reads unstructured legal text, extracts structured terms with clause citations, flags ambiguity ("net 30" vs "due on delivery"), and drafts tone-appropriate reminders. Very high necessity; rules can't parse arbitrary contracts.
- **Agentic workflow?** Yes, bounded: plan → draft → wait for approval → monitor → remind. Nothing is sent without approval.
- **Differentiator:** Starts from the contract, not the invoice. Chaser-type tools start from existing invoices **[R]**. **[H]** Not verified as unique.
- **MVP:** PDF/text upload; extraction with citations and a review UI; invoice drafting; approval to send; reminder schedule; status dashboard; sample contracts.
- **Demo:** Upload a four-page sample SOW with three milestones. The system extracts terms and shows the source clauses. Approve. Three invoices are created in the sandbox. Simulate a payment and an overdue reminder.
- **Architecture:** FastAPI; PDF text extraction library; LLM with a JSON schema; Invoicing via REST/toolkit; scheduler (e.g., APScheduler); SQLite; simple UI.
- **Security:** Mandatory human review of extracted terms; amounts validated against the contract; no auto-send; PII minimization; upload size and type limits.
- **Risks:** Extraction accuracy (needs a small test set); **[?]** whether sandbox invoice emails and reminders behave visibly; **[?]** invoice webhook events.
- **Complexity:** Medium (lowest build risk of the eight).
- **Judging fit:** Strong Technological Implementation and a clear Impact story; moderate Innovation; **Best Use of PayPal + AI** plausible. Doesn't target Agentic Commerce.
- **Reason to build:** Realistic scope, a visible AI step, and a PayPal-central flow.
- **Reason not to:** "Invoice automation" is on the organizer list, so judges must see the contract-first angle quickly.

---

### E. ReimburseAI — receipts to approved payouts

**Pitch:** Employees or contractors upload receipts; AI checks them against policy, a manager approves, and PayPal Payouts reimburses them.

- **Target users / problem:** Small teams, clubs, and distributed communities that reimburse by hand with spreadsheets and bank transfers.
- **Solution / journey:** Upload receipt photo → AI extracts merchant, date, amount, category and checks policy (limits, categories, duplicates) → manager sees a summary with flags → approves a batch → the app creates a Payouts batch → status updates arrive.
- **Why it matters:** Expense handling is slow and error-prone; paying many people is a natural fit for Payouts.
- **How PayPal is central:** Money movement is Payouts; approvals gate the batch.
- **PayPal APIs:** [Payouts v1](https://developer.paypal.com/docs/api/payments.payouts-batch/v1/) and the [Payouts guide](https://developer.paypal.com/docs/payouts/standard/integrate-api/) (idempotent `sender_batch_id`; sandbox error simulation **[V]**); webhooks for payout events.
- **AI's role / necessity:** Vision/OCR extraction from varied receipts; policy reasoning; duplicate and anomaly detection; plain-language flags. High necessity for extraction, medium for policy.
- **Agentic workflow?** Light: a pipeline with a human gate. Agentic framing isn't needed.
- **Differentiator:** Lightweight and PayPal-native for teams without an expense suite. Many expense tools exist **[H]**, so this isn't novel.
- **MVP:** Receipt upload; extraction; policy rules; flags; manager approval; payout batch; status view.
- **Demo:** Upload four receipts (one over limit, one duplicate); show flags; approve three; the Payouts batch succeeds in the sandbox; simulate one failure using the `ERRPYO002` note value.
- **Architecture:** FastAPI; a vision-capable LLM; SQLite; Payouts REST; webhooks; basic UI.
- **Security:** Dual control (submitter ≠ approver); amounts come only from the approved record; idempotent batches; role checks; receipt images stored privately.
- **Risks:** **[?] Sandbox Payouts availability (the guide lists a verified live business account as a prerequisite). Test first; if Payouts doesn't work in the sandbox, this idea fails.** The toolkit has no payout tools **[V]**, so the REST calls must be written by hand.
- **Complexity:** Medium.
- **Judging fit:** Good Technological Implementation and Demo; weaker Innovation; no particular tie to Agentic Commerce.
- **Reason to build:** Relatable demo, easy to explain.
- **Reason not to:** Familiar category with the single point of failure above.

---

### F. PotLuck — all-or-nothing group purchases

**Pitch:** An AI organizer plans a group purchase (a gift, a trip deposit, a team order); each member's PayPal approval creates an authorization hold; funds are captured only if everyone commits, otherwise every hold is voided.

- **Target users / problem:** Friend groups, office teams, and community buyers who chase each other for money and get stuck when someone drops out.
- **Solution / journey:** Organizer describes the goal → AI proposes items, a budget, and a fair split (equal, income-weighted, by usage) → invitation links go out → each member approves a PayPal authorization for their share → when the threshold is met the organizer confirms and all holds are captured; if the deadline passes, all holds are voided.
- **Why it matters:** Group payments are a daily friction. All-or-nothing pledges (as in crowdfunding) lower each contributor's risk.
- **How PayPal is central:** The mechanic *is* PayPal's authorize/capture/void. The 29-day authorization window **[V]** enables it.
- **PayPal APIs:** [Orders v2 `AUTHORIZE`](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/), [Payments v2 capture/void/reauthorize](https://developer.paypal.com/docs/api/payments/v2/), [Webhooks](https://developer.paypal.com/docs/api/webhooks/v1/).
- **AI's role / necessity:** Planning, split suggestions, and group nudges. **Necessity is the weakest of the eight:** a form could do most of it.
- **Agentic workflow?** Optional. A coordinator agent could chase members but it isn't essential.
- **Differentiator:** Uses an unusual PayPal feature for a social purpose. **[H]** Group-pay apps and pooled-funding sites exist, so novelty rests on the hold mechanic.
- **MVP:** Create a pot; invite links; per-member authorization; threshold logic; capture-all or void-all; expiry handling.
- **Demo:** Three sandbox buyers pledge; one drops out; the deadline passes; all holds void. Rerun with all three: all captured.
- **Architecture:** FastAPI; DB; scheduler for deadlines; webhooks; small web UI; LLM for planning.
- **Security:** Server decides amounts; never capture without the recorded threshold; handle partial capture failures and expired holds; idempotent captures; clear messaging that a hold isn't a charge.
- **Risks:** **[?]** Behavior of multiple sandbox buyers and partial failures; holds expiring; PayPal policy on collecting money on behalf of others **[?]** (needs checking).
- **Complexity:** Medium.
- **Judging fit:** Innovation and PayPal depth are good; AI is the weak point. Could suit **Best Use of PayPal + AI** only if the AI part is made more meaningful.
- **Reason to build:** A distinctive use of PayPal mechanics with a fun demo.
- **Reason not to:** AI looks bolted on, and judges explicitly look for meaningful AI.

---

### G. SandboxPilot — AI that tests your PayPal integration

**Pitch:** Point it at your checkout code or endpoint list; it generates and runs sandbox scenarios (declines, duplicate captures, expired orders, webhook retries) and reports integration bugs with suggested fixes.

- **Target users / problem:** Developers integrating PayPal who miss edge cases that only show up in production.
- **Solution / journey:** Provide a repo URL or endpoint list → AI generates test scenarios → the runner executes them against the sandbox → AI analyzes failures and proposes fixes → a report is produced.
- **Why it matters:** Payment bugs are costly. This project's own rules call for tests of critical payment flows.
- **How PayPal is central:** The tool exercises PayPal APIs and sandbox behaviors (idempotency, webhook verification, error simulation).
- **PayPal APIs:** [Orders v2](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/), [Webhooks (verify, simulate)](https://developer.paypal.com/docs/api/webhooks/v1/), [Payouts error simulation](https://developer.paypal.com/docs/payouts/standard/integrate-api/), [Disputes sandbox endpoints](https://developer.paypal.com/docs/api/customer-disputes/v1/).
- **AI's role / necessity:** Scenario generation, root-cause analysis, fix suggestions. Medium–high necessity.
- **Agentic workflow?** Yes: a plan–run–observe–fix loop.
- **Differentiator:** Test-focused rather than code-generation-focused. **[H]** "PayPal integration copilot" is on the organizer list; I didn't research dev-tool competitors in depth.
- **MVP:** A scenario library; a runner; an AI analyzer; a report.
- **Demo:** Run against a deliberately buggy sample checkout; find a double-capture bug; show the fix.
- **Architecture:** Python CLI/FastAPI; pytest-style runner; LLM; sandbox credentials.
- **Security:** A sandbox-only guard that refuses production credentials; secrets never sent to the LLM; sandboxed code execution.
- **Risks:** The audience is developers, so Impact and Design may score lower. Needs a "buggy app" fixture. Repo analysis can balloon in scope. Sandbox flakiness.
- **Complexity:** High.
- **Judging fit:** Strong Technological Implementation; narrower Impact; harder Presentation.
- **Reason to build:** Useful to the hackathon's own audience, including judges who are PayPal engineers.
- **Reason not to:** The most abstract demo and the hardest to make visual.

---

### H. HaggleNet — negotiating agents settled through PayPal

**Pitch:** A buyer's agent and a seller's agent negotiate price and terms within limits their owners set; when they agree, a PayPal order is created for both sides to approve.

- **Target users / problem:** Buyers and sellers of negotiable goods (second-hand items, services, bulk lots) who spend time haggling.
- **Solution / journey:** Seller sets a floor and tone; buyer sets a ceiling → agents negotiate in a visible transcript → agreement produces a proposed deal → both owners approve → PayPal order created and captured.
- **Why it matters:** It explores a real agentic-commerce question: what happens when both sides use agents?
- **How PayPal is central:** *Weakest of the eight.* PayPal is the settlement step, with basic depth (create, approve, capture, optional refund).
- **PayPal APIs:** [Orders v2](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/), [Payments v2](https://developer.paypal.com/docs/api/payments/v2/).
- **AI's role / necessity:** Core. The negotiation is the product. Needs strict boundaries so an agent can never agree outside its owner's limits (enforced in code).
- **Agentic workflow?** Yes. Multi-agent negotiation is the point.
- **Differentiator:** Two-sided negotiation is uncommon in demos **[H]**; I did not research academic or commercial negotiation agents.
- **MVP:** Two agent profiles; a negotiation loop with a turn cap; hard limits; deal summary; PayPal settlement.
- **Demo:** A live negotiation transcript ends in an agreed price; both owners approve; the PayPal order is captured. The most entertaining three minutes of the eight.
- **Architecture:** FastAPI; LLM with a tool-constrained negotiation protocol; WebSocket for the live transcript; PayPal orders.
- **Security:** Limits enforced outside the LLM; the final price re-validated server-side; both parties must approve; transcript stored.
- **Risks:** Judges might see PayPal as a bolt-on, which is the exact failure the brief warns about, and it could fail the "meaningful PayPal use" check **[H]**. Negotiations can get repetitive; the real-world need is unclear.
- **Complexity:** Low–Medium.
- **Judging fit:** High on Innovation and Presentation; low on PayPal depth.
- **Reason to build:** Fast to build with a memorable demo, leaving time to polish.
- **Reason not to:** The PayPal integration is shallow and it could be judged a gimmick.

---

## 6. Comparison

### Scoring methodology

- Each idea is scored **1–10** on seven criteria. 10 is best, and I avoided 9–10 without strong evidence.
- Weights reflect the hackathon criteria and this project's rules **[H]**:

| Criterion | Weight | Why |
|---|---|---|
| Strength of PayPal integration | 20 | The brief requires meaningful PayPal use; also feeds *Best Use of PayPal + AI*. |
| Innovation potential | 15 | Official criterion. |
| Real-world impact | 15 | Official criterion. |
| Strength of AI integration | 15 | The brief requires meaningful AI. |
| Technical feasibility | 15 | A working demo is mandatory in about 31 days. |
| Demo quality | 10 | Maps to Design and Presentation. |
| Differentiation | 10 | Guards against crowded ideas. |

- **Overall = Σ(score × weight) ÷ 10**, giving a value out of 100.
- **Caveats:** The scores are my judgment on partly unverified facts. A 1–2 point change in a few cells could reorder the middle of the table. I'd put the uncertainty at roughly ±5 points. **Don't read the ranking as precise, and it does not predict who wins.** Team skills, your own interest, and polish matter more than a 3-point gap.

### Scores

| Idea | Innovation (15) | Impact (15) | PayPal (20) | AI (15) | Feasibility (15) | Demo (10) | Differentiation (10) | **Overall /100** |
|---|---|---|---|---|---|---|---|---|
| A. Mandate | 7 | 7 | 6 | 6 | 7 | 7 | 6 | **65.5** |
| B. AgentStorefront | 7 | 7 | 7 | 7 | 6 | 8 | 6 | **68.5** |
| C. DisputeDesk | 5 | 8 | 8 | 8 | 6 | 7 | 4 | **67.5** |
| D. ContractToCash | 6 | 7 | 7 | 8 | 8 | 8 | 5 | **70.5** |
| E. ReimburseAI | 5 | 7 | 7 | 7 | 6 | 8 | 5 | **64.5** |
| F. PotLuck | 7 | 5 | 8 | 5 | 7 | 7 | 7 | **66.0** |
| G. SandboxPilot | 6 | 6 | 6 | 8 | 5 | 6 | 6 | **61.5** |
| H. HaggleNet | 8 | 4 | 4 | 8 | 8 | 9 | 6 | **65.0** |

Rationale for key cells:
- **Feasibility** for E is held at 6 because sandbox Payouts access is unconfirmed **[?]**. C is 6 because realistic sandbox disputes are unconfirmed **[?]**. B is 6 because a judge-usable shopper agent adds work.
- **Differentiation** for C is 4 because funded competitors exist **[R]**.
- **PayPal** for H is 4 because settlement is the only PayPal step.
- **AI** for F is 5 because the AI part could mostly be a form.

---

## 7. Ranked shortlist and trade-offs

Ranked by score, with the caveat that the gaps are within the noise:

1. **D. ContractToCash (70.5):** lowest build risk and a clear AI step; the contract-first angle is a hypothesis. It sits on the crowded invoice theme and doesn't target the Agentic Commerce prize.
2. **B. AgentStorefront (68.5):** strongest fit for *Agentic Commerce* with a two-sided demo; higher build effort and overlap with PayPal's own direction **[R]**.
3. **C. DisputeDesk (67.5):** deepest PayPal-plus-AI fit and high impact; funded competitors and the organizer list make it the most likely to look like other entries.
4. **F. PotLuck (66.0):** the most creative use of PayPal mechanics; AI is thin and the rules on pooling money need checking.
5. **A. Mandate (65.5):** best match to this project's "approval, not recommendation" principle and to *Agentic Commerce*; its value shows only through what it blocks.
6. **H. HaggleNet (65.0):** fastest to build with the best demo, but PayPal is shallow, which risks the "meaningful use" requirement.
7. **E. ReimburseAI (64.5):** solid but familiar; depends on one unverified sandbox capability.
8. **G. SandboxPilot (61.5):** appeals to developer-judges but is the hardest to present and the most complex.

**Key trade-offs to weigh:**
- **Prize targeting vs. build risk:** Agentic Commerce ideas (A, B, H) go after a specific $5,000 award, but are either shallower on PayPal (H) or heavier to build (B). Invoice or dispute ideas (C, D) are safer to build but more crowded.
- **Novelty vs. depth:** F and H are the most unusual; C, D, and E use more PayPal API surface in standard ways.
- **Combinations are possible,** for example D with Mandate-style approval gates, or B with Mandate as its checkout guard. That would raise complexity.

**Things to check before choosing (a day or two of work, none of it done yet):**
1. Read the official Devpost rules (the page was blocked for my fetch tool), especially the submission requirements and close time.
2. In the sandbox: can you create an order, authorize, capture, and void? Does Payouts work? Can you create disputes? Do invoice emails and reminders appear?
3. Confirm the remote MCP tool catalog and whether the Python toolkit meets your needs.
4. Decide the AI approach for the hosted demo: a server-side key with spend caps, plus a mock/replay mode.
5. Confirm whether Agent Ready or Store Sync can be used in the sandbox. I found no evidence that they can.

*This report doesn't select an idea. The decision is yours.*

---

## 8. Sources

**Hackathon**
- [PayPal community blog: PayPal AI Hackathon](https://developer.paypal.com/community/blog/PayPal_AI_Hackathon/) (official)
- [Devpost rules](https://paypalaihackathon.devpost.com/rules) (official; not fetched, returned 403)
- [GenAI Magazine summary and idea list](https://thegenaimagazine.com/paypal-ai-hackathon-2026-ideas-deadline-prizes) (secondary)

**PayPal docs (official)**
- [Orders v2 standard flow](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/standard/)
- [Vault / save payment methods](https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/save-payment-methods/)
- [Payments v2](https://developer.paypal.com/docs/api/payments/v2/)
- [Payouts API](https://developer.paypal.com/docs/api/payments.payouts-batch/v1/) and [integration guide](https://developer.paypal.com/docs/payouts/standard/integrate-api/)
- [Invoicing v2](https://developer.paypal.com/docs/api/invoicing/v2/)
- [Subscriptions v1](https://developer.paypal.com/docs/api/subscriptions/v1/)
- [Customer Disputes v1](https://developer.paypal.com/docs/api/customer-disputes/v1/)
- [Transaction Search v1](https://developer.paypal.com/docs/api/transaction-search/v1/)
- [Webhooks v1](https://developer.paypal.com/docs/api/webhooks/v1/)
- [Agent Toolkit (GitHub)](https://github.com/paypal/agent-toolkit) and [quickstart](https://developer.paypal.com/ai-tools/toolkit)
- [MCP server quickstart](https://developer.paypal.com/ai-tools/mcp-server)

**Market and context (secondary; treat as indicative)**
- [Digital Commerce 360: PayPal agentic commerce services](https://www.digitalcommerce360.com/2025/10/28/paypal-agentic-commerce-ai-driven-shopping-services/)
- [PayPal newsroom: Perplexity Instant Buy](https://newsroom.paypal-corp.com/2025-11-PayPal-and-Perplexity-Launch-Instant-Buy)
- [AP2 specification](https://ap2-protocol.org/ap2/specification/) and [PYMNTS on AP2](https://www.pymnts.com/artificial-intelligence-2/2025/google-unveils-a-payment-protocol-for-ai-driven-commerce/)
- [Chargeflow PayPal](https://www.chargeflow.io/integrations/paypal) and [Justt update](https://thepaypers.com/fraud-and-fincrime/news/justt-upgrades-ai-chargeback-management)
- [Chaser (ERP Research)](https://erpresearch.com/erp-add-ons/ar-collections/chaser)
- [JudgePay PayPal Edition (GitHub)](https://github.com/Techfrontiers/judgepay-paypal)
