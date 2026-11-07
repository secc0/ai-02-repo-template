import pytest

from app import cli
from evals import run as evals_run
from tests.conftest import FakeClient


def test_cli_fails_early_without_key(clean_env, capsys):
    assert cli.main(["hi"]) == 2
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err


def test_cli_prints_answer(clean_env, capsys, monkeypatch):
    clean_env.setenv("OPENROUTER_API_KEY", "k")
    clean_env.setenv("MODEL_PRIMARY", "fake/model-a")
    fake = FakeClient(reply="pong")
    monkeypatch.setattr("app.llm.make_client", lambda settings: fake)
    assert cli.main(["ping"]) == 0
    out = capsys.readouterr()
    assert out.out.strip() == "pong"
    assert "fake/model-a" in out.err
    assert fake.calls[0]["messages"][0]["content"] == "ping"


@pytest.mark.parametrize(
    ("answer", "check", "expected"),
    [
        ("The answer is 5.", {"contains": "5"}, True),
        ("Paris", {"contains": "paris"}, True),
        ("London", {"contains": "paris"}, False),
        ("PONG.", {"equals": "pong"}, True),
        ("pong pong", {"equals": "pong"}, False),
        ("1, 2, 3", {"regex": r"1\s*,\s*2\s*,\s*3"}, True),
    ],
)
def test_check_answer(answer, check, expected):
    assert evals_run.check_answer(answer, check) is expected


def test_check_answer_rejects_unknown_type():
    with pytest.raises(ValueError):
        evals_run.check_answer("x", {"startswith": "x"})


def test_bundled_cases_are_valid():
    cases = evals_run.load_cases(evals_run.DEFAULT_CASES)
    assert 3 <= len(cases) <= 5
    for case in cases:
        evals_run.check_answer("", case["check"])  # raises on a malformed check


def test_run_cases_with_fake_client(settings):
    cases = [
        {"id": "a", "prompt": "q1", "check": {"contains": "yes"}},
        {"id": "b", "prompt": "q2", "check": {"contains": "no"}},
    ]
    results = evals_run.run_cases(cases, settings, client=FakeClient(reply="yes"))
    assert [r.passed for r in results] == [True, False]
    assert evals_run.pass_rate(results) == 0.5


def test_eval_model_falls_back_to_primary(clean_env):
    clean_env.setenv("OPENROUTER_API_KEY", "k")
    clean_env.setenv("MODEL_PRIMARY", "p/primary")
    assert evals_run.eval_settings().model_primary == "p/primary"
    clean_env.setenv("EVAL_MODEL", "p/eval")
    s = evals_run.eval_settings()
    assert s.model_primary == "p/eval"
    assert s.model_fallbacks == []


def test_evals_main_fails_clearly_without_key(clean_env, capsys):
    assert evals_run.main([]) == 2
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err
