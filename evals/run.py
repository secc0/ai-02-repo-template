"""Run evals/cases.yaml against one model and print pass/fail plus the pass rate.

The model comes from EVAL_MODEL, falling back to MODEL_PRIMARY.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv, load_dotenv

from app.config import ConfigError, Settings
from app.llm import complete

DEFAULT_CASES = Path(__file__).with_name("cases.yaml")


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    detail: str


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = data.get("cases") or []
    for case in cases:
        if not {"id", "prompt", "check"} <= case.keys():
            raise ValueError(f"Case is missing id/prompt/check: {case!r}")
    return cases


def check_answer(answer: str, check: dict[str, str]) -> bool:
    if len(check) != 1:
        raise ValueError(f"A check must have exactly one key, got: {check!r}")
    kind, expected = next(iter(check.items()))
    expected = str(expected)
    if kind == "contains":
        return expected.lower() in answer.lower()
    if kind == "equals":
        return answer.strip().rstrip(".").lower() == expected.strip().lower()
    if kind == "regex":
        return re.search(expected, answer) is not None
    raise ValueError(f"Unknown check type: {kind!r}")


def eval_settings() -> Settings:
    load_dotenv(find_dotenv(usecwd=True))
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "Missing required environment variable: OPENROUTER_API_KEY. "
            "Set it in your shell or copy .env.example to .env and fill it in."
        )
    model = os.getenv("EVAL_MODEL", "").strip() or os.getenv("MODEL_PRIMARY", "").strip()
    if not model:
        raise ConfigError("Missing required environment variable: EVAL_MODEL (or MODEL_PRIMARY).")
    # No fallbacks: an eval should measure exactly one model.
    return Settings(api_key=api_key, model_primary=model, model_fallbacks=[])


def run_cases(
    cases: list[dict[str, Any]], settings: Settings, *, client: Any | None = None
) -> list[CaseResult]:
    results = []
    for case in cases:
        try:
            completion = complete(case["prompt"], settings, client=client)
            passed = check_answer(completion.text, case["check"])
            detail = completion.text.strip().replace("\n", " ")[:80]
        except Exception as exc:  # report the failure and keep going
            passed, detail = False, f"error: {type(exc).__name__}: {exc}"
        results.append(CaseResult(case["id"], passed, detail))
    return results


def pass_rate(results: list[CaseResult]) -> float:
    return sum(r.passed for r in results) / len(results) if results else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.run")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--min-pass-rate", type=float, default=0.8, help="exit 1 below this rate (0-1)"
    )
    args = parser.parse_args(argv)

    try:
        settings = eval_settings()
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cases = load_cases(args.cases)
    print(f"model: {settings.model_primary}  cases: {len(cases)}")
    results = run_cases(cases, settings)
    for r in results:
        print(f"{'PASS' if r.passed else 'FAIL'}  {r.case_id:<12} {r.detail}")

    rate = pass_rate(results)
    print(f"pass rate: {rate:.0%} ({sum(r.passed for r in results)}/{len(results)})")
    return 0 if rate >= args.min_pass_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
