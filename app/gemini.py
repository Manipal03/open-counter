"""Minimal Gemini API client (generateContent over REST, using httpx).

Reference: https://ai.google.dev/api/generate-content (POST /v1beta/models/{model}:generateContent).
Verified in the reference: Tool.functionDeclarations, FunctionDeclaration.parameters (OpenAPI
Schema subset with `nullable`), Part.functionCall {name, args, id?}, Part.functionResponse
{name, response, id?}, Part.thoughtSignature, Candidate.finishReason.
Unverified (not found on the reference pages read): the API-key header name and the role used
for function results. We use the widely documented `x-goog-api-key` header and role "user".
"""

import httpx

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com"


class GeminiError(Exception):
    def __init__(self, status_code: int, body: object):
        super().__init__(f"Gemini API error {status_code}")
        self.status_code = status_code
        self.body = body


class GeminiClient:
    def __init__(self, api_key: str, model: str, http: httpx.Client | None = None):
        self._api_key = api_key
        self._model = model
        self._http = http or httpx.Client(base_url=GEMINI_BASE_URL, timeout=45.0)

    def generate(self, system: str, contents: list[dict], tools: list[dict]) -> dict:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "tools": [{"functionDeclarations": tools}],
            "generationConfig": {"maxOutputTokens": 2000},
        }
        try:
            r = self._http.post(
                f"/v1beta/models/{self._model}:generateContent",
                headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"},
                json=body,
            )
        except httpx.HTTPError as exc:
            raise GeminiError(0, str(exc)) from exc
        try:
            data = r.json()
        except ValueError:
            data = r.text
        if r.status_code >= 400:
            raise GeminiError(r.status_code, data)
        return data


# Gemini uses an OpenAPI-style schema: single `type` values and `nullable` instead of
# JSON Schema type arrays, and no `additionalProperties`. Our Pydantic models still reject
# extra fields when the tool runs.
GEMINI_TOOLS = [
    {
        "name": "search_products",
        "description": "Search the shop catalog by keywords and optional maximum price in "
        "dollars. Returns up to 5 products with sku, name, description, price and stock.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Keywords, e.g. 'waterproof jacket'"},
                "max_price": {
                    "type": "NUMBER",
                    "nullable": True,
                    "description": "Maximum unit price in dollars, or null",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_product",
        "description": "Get one product by SKU.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"sku": {"type": "STRING"}},
            "required": ["sku"],
        },
    },
    {
        "name": "create_checkout",
        "description": "Create a PayPal checkout for the given SKUs and quantities. The server "
        "computes the price from the catalog. Returns the order total; the shopper then "
        "approves payment on PayPal.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "items": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "sku": {"type": "STRING"},
                            "qty": {"type": "INTEGER"},
                        },
                        "required": ["sku", "qty"],
                    },
                }
            },
            "required": ["items"],
        },
    },
]
