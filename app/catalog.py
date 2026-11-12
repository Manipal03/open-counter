"""Read-only catalog access. The catalog is the only source of prices."""

import re
import sqlite3

STOPWORDS = {
    "the", "and", "for", "with", "want", "need", "looking", "something", "some", "can", "you",
    "show", "find", "please", "have", "any", "under", "below", "than", "less", "about", "that",
    "this", "what", "who", "its", "it's", "get", "buy", "would", "like", "dollars", "usd",
}


def _row(r: sqlite3.Row) -> dict:
    return {
        "sku": r["sku"],
        "name": r["name"],
        "description": r["description"],
        "category": r["category"],
        "price_cents": r["price_cents"],
        "currency": r["currency"],
        "stock": r["stock"],
    }


def list_products(conn: sqlite3.Connection) -> list[dict]:
    return [_row(r) for r in conn.execute("SELECT * FROM products ORDER BY category, name")]


def get_product(conn: sqlite3.Connection, sku: str) -> dict | None:
    r = conn.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
    return _row(r) if r else None


def search_products(
    conn: sqlite3.Connection, query: str = "", max_price_cents: int | None = None, limit: int = 5
) -> list[dict]:
    words = [
        w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2 and w not in STOPWORDS
    ]
    results = []
    for p in list_products(conn):
        if max_price_cents is not None and p["price_cents"] > max_price_cents:
            continue
        name = f"{p['name']} {p['category']}".lower()
        desc = p["description"].lower()
        score = 0
        for w in words:
            stem = w.rstrip("s")
            if stem in name:
                score += 2
            elif stem in desc:
                score += 1
        if words and score == 0:
            continue
        results.append((score, p))
    results.sort(key=lambda sp: (-sp[0], sp[1]["price_cents"]))
    return [p for _, p in results[:limit]]


def format_money(cents: int, currency: str) -> str:
    return f"{cents // 100}.{cents % 100:02d}"
