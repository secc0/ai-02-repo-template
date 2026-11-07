"""Minimal OpenRouter client built on the openai SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class Completion:
    text: str
    model: str


def make_client(settings: Settings) -> Any:
    """Create an OpenAI-compatible client pointed at OpenRouter."""
    from openai import OpenAI

    return OpenAI(api_key=settings.api_key, base_url=OPENROUTER_BASE_URL)


def complete(
    prompt: str,
    settings: Settings,
    *,
    model: str | None = None,
    client: Any | None = None,
) -> Completion:
    """Send a single user prompt and return the answer and the model that produced it.

    OpenRouter tries `model` (if given), then settings.model_primary, then each entry of
    settings.model_fallbacks in order, via the `models` routing parameter.
    """
    client = client or make_client(settings)
    primary = model or settings.model_primary
    candidates = [primary, settings.model_primary, *settings.model_fallbacks]
    models = list(dict.fromkeys(candidates))  # de-duplicate, keep order

    kwargs: dict[str, Any] = {
        "model": primary,
        "messages": [{"role": "user", "content": prompt}],
    }
    if len(models) > 1:
        kwargs["extra_body"] = {"models": models}

    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""
    return Completion(text=text, model=response.model or primary)
