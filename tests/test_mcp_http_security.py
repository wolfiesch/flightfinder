"""Security policy tests for the FlightFinder MCP HTTP server."""

import pytest

from flightfinder.mcp_http_server import (
    build_http_access_settings,
    validate_api_token,
    validate_host_header,
    validate_origin_header,
)


@pytest.fixture(autouse=True)
def clear_mcp_token_env(monkeypatch):
    monkeypatch.delenv("FLIGHTFINDER_MCP_API_TOKEN", raising=False)
    monkeypatch.delenv("FLIGHTFINDER_MCP_API_KEY", raising=False)


def test_loopback_bind_is_default_safe_without_token():
    settings = build_http_access_settings(host="127.0.0.1")

    assert settings.api_token is None
    assert validate_host_header("localhost:3001", settings)
    assert validate_host_header("127.0.0.1:3001", settings)
    assert validate_origin_header("http://localhost:3001", settings)
    assert not validate_host_header("evil.example.com", settings)
    assert not validate_origin_header("https://evil.example.com", settings)


def test_remote_bind_requires_token_and_explicit_allowlists():
    with pytest.raises(ValueError, match="require"):
        build_http_access_settings(host="0.0.0.0")

    with pytest.raises(ValueError, match="allowed-host"):
        build_http_access_settings(host="0.0.0.0", api_token="secret")

    with pytest.raises(ValueError, match="allowed-origin"):
        build_http_access_settings(
            host="0.0.0.0",
            allowed_hosts=["flightfinder.example.com"],
            api_token="secret",
        )


def test_remote_bind_rejects_wildcard_allowlists():
    with pytest.raises(ValueError, match="explicit"):
        build_http_access_settings(
            host="0.0.0.0",
            allowed_hosts=["*"],
            allowed_origins=["https://trusted.example.com"],
            api_token="secret",
        )

    with pytest.raises(ValueError, match="explicit"):
        build_http_access_settings(
            host="0.0.0.0",
            allowed_hosts=["flightfinder.example.com"],
            allowed_origins=["*"],
            api_token="secret",
        )


def test_remote_bind_allows_only_configured_host_origin_and_token():
    settings = build_http_access_settings(
        host="0.0.0.0",
        allowed_hosts=["flightfinder.example.com"],
        allowed_origins=["https://trusted.example.com"],
        api_token="secret",
    )

    assert validate_host_header("flightfinder.example.com", settings)
    assert not validate_host_header("evil.example.com", settings)
    assert validate_origin_header("https://trusted.example.com", settings)
    assert not validate_origin_header("https://evil.example.com", settings)
    assert validate_api_token({"authorization": "Bearer secret"}, settings)
    assert validate_api_token({"x-flightfinder-api-token": "secret"}, settings)
    assert not validate_api_token({"authorization": "Bearer wrong"}, settings)
    assert not validate_api_token({}, settings)


def test_remote_bind_can_read_token_from_environment(monkeypatch):
    monkeypatch.setenv("FLIGHTFINDER_MCP_API_TOKEN", "from-env")

    settings = build_http_access_settings(
        host="0.0.0.0",
        allowed_hosts=["flightfinder.example.com"],
        allowed_origins=["https://trusted.example.com"],
    )

    assert validate_api_token({"authorization": "Bearer from-env"}, settings)
