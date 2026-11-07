from app.config import Settings
from app.llm import complete
from tests.conftest import FakeClient


def test_complete_returns_text_and_answering_model(settings):
    client = FakeClient(reply="hi there", model="fake/model-b")
    result = complete("hello", settings, client=client)
    assert result.text == "hi there"
    assert result.model == "fake/model-b"


def test_complete_sends_fallbacks_in_extra_body(settings):
    client = FakeClient()
    complete("hello", settings, client=client)
    (call,) = client.calls
    assert call["model"] == "fake/model-a"
    assert call["messages"] == [{"role": "user", "content": "hello"}]
    assert call["extra_body"] == {"models": ["fake/model-a", "fake/model-b", "fake/model-c"]}


def test_complete_without_fallbacks_omits_extra_body():
    s = Settings(api_key="k", model_primary="fake/only")
    client = FakeClient()
    complete("hello", s, client=client)
    assert "extra_body" not in client.calls[0]


def test_model_override_goes_first_without_duplicates(settings):
    client = FakeClient()
    complete("hello", settings, model="fake/model-b", client=client)
    call = client.calls[0]
    assert call["model"] == "fake/model-b"
    assert call["extra_body"]["models"] == ["fake/model-b", "fake/model-a", "fake/model-c"]


def test_complete_handles_empty_content(settings):
    result = complete("hello", settings, client=FakeClient(reply=None))
    assert result.text == ""
