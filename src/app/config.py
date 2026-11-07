"""Settings loaded from environment variables (and a local .env file, if present)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import find_dotenv, load_dotenv


class ConfigError(RuntimeError):
    """Raised when a required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    model_primary: str
    model_fallbacks: list[str] = field(default_factory=list)


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            f"Missing required environment variable: {name}. "
            "Set it in your shell or copy .env.example to .env and fill it in."
        )
    return value


def parse_list(raw: str | None) -> list[str]:
    """Split a comma-separated string into a list of non-empty, stripped items."""
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings(*, load_env_file: bool = True) -> Settings:
    """Load settings, failing early with the name of the first missing variable."""
    if load_env_file:
        load_dotenv(find_dotenv(usecwd=True))
    return Settings(
        api_key=_require("OPENROUTER_API_KEY"),
        model_primary=_require("MODEL_PRIMARY"),
        model_fallbacks=parse_list(os.getenv("MODEL_FALLBACKS")),
    )
