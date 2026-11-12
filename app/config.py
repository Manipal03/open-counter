"""Settings loaded from environment variables.

The app refuses to start unless PAYPAL_ENV is "sandbox". The PayPal base URL is pinned
to the sandbox host and cannot be changed by configuration.
"""

import os
from dataclasses import dataclass

PAYPAL_SANDBOX_BASE_URL = "https://api-m.sandbox.paypal.com"


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    paypal_client_id: str
    paypal_client_secret: str
    app_base_url: str
    ai_mode: str
    ai_provider: str
    anthropic_api_key: str
    ai_model: str
    gemini_api_key: str
    gemini_model: str
    ai_daily_call_limit: int
    database_path: str
    paypal_base_url: str = PAYPAL_SANDBOX_BASE_URL


def _clean(value: str) -> str:
    """Drop whitespace and surrounding quotes that often sneak in when pasting keys."""
    return value.strip().strip('"').strip("'").strip()


def read_dotenv(path: str = ".env") -> dict[str, str]:
    """Parse simple KEY=VALUE lines from a local .env file, if it exists."""
    values: dict[str, str] = {}
    if not os.path.exists(path):
        return values
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_settings(env: dict[str, str] | None = None) -> Settings:
    if env is None:
        env = {**read_dotenv(), **os.environ}

    if env.get("PAYPAL_ENV", "").strip().lower() != "sandbox":
        raise ConfigError(
            "PAYPAL_ENV must be 'sandbox'. Open Counter never runs against live PayPal."
        )

    ai_mode = env.get("AI_MODE", "replay").strip().lower()
    if ai_mode not in {"live", "replay"}:
        raise ConfigError("AI_MODE must be 'live' or 'replay'.")
    ai_provider = env.get("AI_PROVIDER", "gemini").strip().lower()
    if ai_provider not in {"gemini", "anthropic"}:
        raise ConfigError("AI_PROVIDER must be 'gemini' or 'anthropic'.")
    api_key = env.get("ANTHROPIC_API_KEY", "").strip()
    gemini_key = env.get("GEMINI_API_KEY", "").strip()
    provider_key = gemini_key if ai_provider == "gemini" else api_key
    if ai_mode == "live" and not provider_key:
        ai_mode = "replay"

    try:
        limit = int(env.get("AI_DAILY_CALL_LIMIT", "300"))
    except ValueError as exc:
        raise ConfigError("AI_DAILY_CALL_LIMIT must be an integer.") from exc

    return Settings(
        paypal_client_id=_clean(env.get("PAYPAL_CLIENT_ID", "")),
        paypal_client_secret=_clean(env.get("PAYPAL_CLIENT_SECRET", "")),
        app_base_url=(
            env.get("APP_BASE_URL", "").strip()
            or env.get("RENDER_EXTERNAL_URL", "").strip()  # set automatically by Render
            or "http://localhost:8000"
        ).rstrip("/"),
        ai_mode=ai_mode,
        ai_provider=ai_provider,
        anthropic_api_key=api_key,
        ai_model=env.get("AI_MODEL", "claude-opus-5-5").strip(),
        gemini_api_key=gemini_key,
        gemini_model=env.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip(),
        ai_daily_call_limit=max(0, limit),
        database_path=env.get("DATABASE_PATH", "open_counter.db"),
    )
