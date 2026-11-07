import pytest

from app.config import ConfigError, load_settings, parse_list


def test_parse_list_strips_and_drops_empty():
    assert parse_list(" a, b ,,c ,") == ["a", "b", "c"]
    assert parse_list("") == []
    assert parse_list(None) == []


def test_load_settings_reads_env(clean_env):
    clean_env.setenv("OPENROUTER_API_KEY", "k")
    clean_env.setenv("MODEL_PRIMARY", "p/one")
    clean_env.setenv("MODEL_FALLBACKS", "p/two, p/three")
    s = load_settings()
    assert s.api_key == "k"
    assert s.model_primary == "p/one"
    assert s.model_fallbacks == ["p/two", "p/three"]


def test_load_settings_reads_dotenv_file(clean_env, tmp_path):
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=k\nMODEL_PRIMARY=p/one\n")
    s = load_settings()
    assert s.model_primary == "p/one"
    assert s.model_fallbacks == []


@pytest.mark.parametrize("missing", ["OPENROUTER_API_KEY", "MODEL_PRIMARY"])
def test_missing_variable_is_named(clean_env, missing):
    for name in ("OPENROUTER_API_KEY", "MODEL_PRIMARY"):
        if name != missing:
            clean_env.setenv(name, "x")
    with pytest.raises(ConfigError, match=missing):
        load_settings()


def test_api_key_not_in_repr(clean_env):
    clean_env.setenv("OPENROUTER_API_KEY", "super-secret")
    clean_env.setenv("MODEL_PRIMARY", "p/one")
    assert "super-secret" not in repr(load_settings())
