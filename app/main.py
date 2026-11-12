"""Open Counter web app."""

import json
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import catalog, checkout
from app.ai import ShoppingAssistant
from app.config import Settings, load_settings
from app.db import connect, init_db
from app.paypal import PayPalClient

BASE = Path(__file__).parent
SESSION_COOKIE = "oc_session"


class ChatIn(BaseModel):
    message: str = Field(max_length=2000)


def create_app(
    settings: Settings | None = None,
    paypal: PayPalClient | None = None,
    assistant_client=None,
    gemini_client=None,
) -> FastAPI:
    settings = settings or load_settings()
    conn = connect(settings.database_path)
    init_db(conn)
    paypal = paypal or PayPalClient(settings)
    assistant = ShoppingAssistant(
        conn, settings, paypal, client=assistant_client, gemini_client=gemini_client
    )

    app = FastAPI(title="Open Counter", docs_url=None, redoc_url=None)
    app.state.conn = conn
    app.state.settings = settings
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
    templates = Jinja2Templates(directory=BASE / "templates")
    templates.env.filters["money"] = lambda cents: catalog.format_money(cents, "USD")

    def session_id(request: Request) -> tuple[str, bool]:
        sid = request.cookies.get(SESSION_COOKIE, "")
        if len(sid) == 32 and sid.isalnum():
            return sid, False
        return secrets.token_hex(16), True

    @app.get("/health")
    def health():
        return {"ok": True, "paypal_env": "sandbox", "ai_mode": settings.ai_mode}

    @app.get("/", response_class=HTMLResponse)
    def shop(request: Request):
        sid, new = session_id(request)
        resp = templates.TemplateResponse(
            request,
            "shop.html",
            {
                "products": catalog.list_products(conn),
                "ai_mode": settings.ai_mode,
                "ai_label": "Gemini" if settings.ai_provider == "gemini" else "Claude",
                "paypal_ready": paypal.configured,
            },
        )
        if new:
            resp.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="lax")
        return resp

    @app.post("/api/chat")
    def chat(body: ChatIn, request: Request):
        sid, new = session_id(request)
        result = assistant.reply(sid, body.message)
        co = None
        if result.checkout:
            co = {
                "approve_url": result.checkout["approve_url"],
                "total": result.checkout["total"],
                "currency": result.checkout["currency"],
                "lines": [{"name": li["name"], "qty": li["qty"]}
                          for li in result.checkout["lines"]],
            }
        resp = JSONResponse({
            "text": result.text,
            "mode": result.mode,
            "notice": result.notice,
            "checkout": co,
        })
        if new:
            resp.set_cookie(SESSION_COOKIE, sid, httponly=True, samesite="lax")
        return resp

    @app.get("/checkout/return", response_class=HTMLResponse)
    def checkout_return(request: Request, token: str = ""):
        order, error = None, None
        try:
            order = checkout.capture_after_approval(conn, paypal, token)
        except checkout.CheckoutError as exc:
            error = str(exc)
            order = checkout.get_order_by_paypal_id(conn, token) if token else None
        return templates.TemplateResponse(
            request, "result.html", {"order": _view(order), "error": error}
        )

    @app.get("/checkout/cancel", response_class=HTMLResponse)
    def checkout_cancel(request: Request, token: str = ""):
        order = checkout.cancel_by_buyer(conn, token) if token else None
        return templates.TemplateResponse(
            request, "result.html",
            {"order": _view(order), "error": "You cancelled at PayPal. Nothing was charged."},
        )

    @app.get("/orders", response_class=HTMLResponse)
    def orders(request: Request):
        rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 50").fetchall()
        items = []
        for r in rows:
            o = _view(dict(r))
            o["audit"] = checkout.audit_trail(conn, r["id"])
            items.append(o)
        return templates.TemplateResponse(request, "orders.html", {"orders": items})

    return app


def _view(order: dict | None) -> dict | None:
    if not order:
        return None
    o = dict(order)
    o["lines"] = json.loads(o.pop("items_json"))
    o["total"] = catalog.format_money(o["total_cents"], o["currency"])
    return o


def get_app() -> FastAPI:
    return create_app()
