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
    anthropic_api_key: str
    ai_model: str
    ai_daily_call_limit: int
    database_path: str
    paypal_base_url: str = PAYPAL_SANDBOX_BASE_URL


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
    api_key = env.get("ANTHROPIC_API_KEY", "").strip()
    if ai_mode == "live" and not api_key:
        ai_mode = "replay"

    try:
        limit = int(env.get("AI_DAILY_CALL_LIMIT", "300"))
    except ValueError as exc:
        raise ConfigError("AI_DAILY_CALL_LIMIT must be an integer.") from exc

    return Settings(
        paypal_client_id=env.get("PAYPAL_CLIENT_ID", "").strip(),
        paypal_client_secret=env.get("PAYPAL_CLIENT_SECRET", "").strip(),
        app_base_url=env.get("APP_BASE_URL", "http://localhost:8000").rstrip("/"),
        ai_mode=ai_mode,
        anthropic_api_key=api_key,
        ai_model=env.get("AI_MODEL", "claude-opus-5-5").strip(),
        ai_daily_call_limit=max(0, limit),
        database_path=env.get("DATABASE_PATH", "open_counter.db"),
    )
