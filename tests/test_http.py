import pytest

from hmc_power_orchestrator.exceptions import AuthError, HttpError, RateLimitError
from hmc_power_orchestrator.http import HTTPClient


def _fake_response(code: int):
    class Resp:
        status_code = code
        text = "oops"

        def json(self):
            return {}

    return Resp()


def test_retry_config():
    client = HTTPClient("https://example.com", retries=5)
    adapter = client._session.get_adapter("https://")
    retry = adapter.max_retries
    assert retry.total == 5
    assert 500 in retry.status_forcelist
    assert "GET" in retry.allowed_methods


def test_url_join(monkeypatch):
    client = HTTPClient("https://example.com/api")
    called = {}

    def fake_request(method, url, **kwargs):
        called["url"] = url
        return _fake_response(200)

    monkeypatch.setattr(client._session, "request", fake_request)
    client.get("/foo")
    assert called["url"] == "https://example.com/api/foo"


def test_error_mapping(monkeypatch):
    client = HTTPClient("https://example.com")

    monkeypatch.setattr(client._session, "request", lambda *a, **k: _fake_response(401))
    with pytest.raises(AuthError):
        client.get("/")

    monkeypatch.setattr(client._session, "request", lambda *a, **k: _fake_response(429))
    with pytest.raises(RateLimitError):
        client.get("/")

    monkeypatch.setattr(client._session, "request", lambda *a, **k: _fake_response(500))
    with pytest.raises(HttpError):
        client.get("/")
