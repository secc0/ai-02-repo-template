"""Shared test helpers: a fake OpenAI-style client (no network, no key)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.config import Settings

ENV_VARS = ("OPENROUTER_API_KEY", "MODEL_PRIMARY", "MODEL_FALLBACKS", "EVAL_MODEL")


class FakeClient:
    """Mimics `client.chat.completions.create(...)` and records every call.

    `reply` may be a string or a callable taking the request kwargs.
    """

    def __init__(self, reply: Any = "hello", model: str = "fake/model-a") -> None:
        self.reply = reply
        self.model = model
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        reply = self.reply(kwargs) if callable(self.reply) else self.reply
        message = SimpleNamespace(content=reply)
        return SimpleNamespace(model=self.model, choices=[SimpleNamespace(message=message)])


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> pytest.MonkeyPatch:
    """Remove relevant env vars and run from an empty dir so no real .env is loaded."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    return monkeypatch


@pytest.fixture
def settings() -> Settings:
    return Settings(
        api_key="test-key",
        model_primary="fake/model-a",
        model_fallbacks=["fake/model-b", "fake/model-c"],
    )
