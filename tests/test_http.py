import pytest
import requests

from hmc_power_orchestrator.exceptions import (
    AuthError,
    NetworkError,
    PermanentError,
    RateLimitError,
    TransientError,
)
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
    with pytest.raises(TransientError):
        client.get("/")

    monkeypatch.setattr(client._session, "request", lambda *a, **k: _fake_response(404))
    with pytest.raises(PermanentError):
        client.get("/")


def test_network_error(monkeypatch):
    client = HTTPClient("https://example.com")

    def boom(*a, **k):
        raise requests.ConnectionError("fail")

    monkeypatch.setattr(client._session, "request", boom)
    with pytest.raises(NetworkError):
        client.get("/")


def test_circuit_breaker(monkeypatch):
    client = HTTPClient("https://example.com", cb_threshold=2, cb_cooldown=60)

    def boom(*a, **k):
        raise requests.Timeout("fail")

    monkeypatch.setattr(client._session, "request", boom)
    with pytest.raises(NetworkError):
        client.get("/")
    with pytest.raises(NetworkError):
        client.get("/")
    # circuit should now be open and raise without calling request
    with pytest.raises(TransientError):
        client.get("/")


def test_circuit_breaker_recovery(monkeypatch):
    client = HTTPClient("https://example.com", cb_threshold=2, cb_cooldown=60)

    fake_time = [0.0]

    def fake_monotonic():
        return fake_time[0]

    monkeypatch.setattr("hmc_power_orchestrator.http.monotonic", fake_monotonic)

    def boom(*a, **k):
        raise requests.Timeout("fail")

    monkeypatch.setattr(client._session, "request", boom)
    with pytest.raises(NetworkError):
        client.get("/")
    with pytest.raises(NetworkError):
        client.get("/")

    # move time forward past cooldown and return success
    fake_time[0] = 61.0
    monkeypatch.setattr(client._session, "request", lambda *a, **k: _fake_response(200))
    client.get("/")
    assert client._cb_state == "closed"
    assert client._cb_failures == 0
