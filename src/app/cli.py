"""Tiny command-line entry point: send a prompt, print the answer."""

from __future__ import annotations

import argparse
import sys

from app.config import ConfigError, load_settings
from app.llm import complete

DEFAULT_PROMPT = "Say hello in one short sentence."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app", description="Send a prompt to OpenRouter.")
    parser.add_argument("prompt", nargs="*", help="prompt text (default: a hello prompt)")
    args = parser.parse_args(argv)
    prompt = " ".join(args.prompt) or DEFAULT_PROMPT

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = complete(prompt, settings)
    print(result.text)
    print(f"[model: {result.model}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
