"""Comprehensive tests for signalswarm.client.SignalSwarm.

Tests initialization, URL construction, headers, and static methods.
No mocks except for external HTTP calls (none needed here since we test
only the constructor and static methods).
"""

import hashlib

import pytest

from signalswarm.client import SignalSwarm, _DEFAULT_API_URL


class TestClientInitialization:
    def test_default_url(self):
        client = SignalSwarm()
        assert client.api_url == "https://signalswarm.xyz"

    def test_custom_url(self):
        client = SignalSwarm(api_url="https://custom-api.example.com")
        assert client.api_url == "https://custom-api.example.com"

    def test_trailing_slash_stripped(self):
        client = SignalSwarm(api_url="https://example.com/")
        assert client.api_url == "https://example.com"

    def test_default_timeout(self):
        client = SignalSwarm()
        assert client.timeout == 30.0

    def test_custom_timeout(self):
        client = SignalSwarm(timeout=60.0)
        assert client.timeout == 60.0

    def test_default_max_retries(self):
        client = SignalSwarm()
        assert client.max_retries == 3

    def test_custom_max_retries(self):
        client = SignalSwarm(max_retries=5)
        assert client.max_retries == 5

    def test_default_retry_backoff(self):
        client = SignalSwarm()
        assert client.retry_backoff == 0.5

    def test_custom_retry_backoff(self):
        client = SignalSwarm(retry_backoff=1.0)
        assert client.retry_backoff == 1.0

    def test_api_key_stored(self):
        client = SignalSwarm(api_key="sk-test-key")
        assert client._api_key == "sk-test-key"

    def test_no_api_key_by_default(self):
        client = SignalSwarm()
        assert client._api_key == ""


class TestURLConstruction:
    def test_base_url_appends_api_v1(self):
        client = SignalSwarm(api_url="https://example.com")
        # httpx normalizes base_url with a trailing slash
        assert str(client._http.base_url).rstrip("/") == "https://example.com/api/v1"

    def test_url_already_has_api_v1(self):
        client = SignalSwarm(api_url="https://example.com/api/v1")
        assert str(client._http.base_url).rstrip("/") == "https://example.com/api/v1"

    def test_trailing_slash_then_api_v1(self):
        client = SignalSwarm(api_url="https://example.com/")
        # After rstrip("/") -> "https://example.com", then + "/api/v1"
        assert str(client._http.base_url).rstrip("/") == "https://example.com/api/v1"

    def test_default_url_construction(self):
        client = SignalSwarm()
        assert str(client._http.base_url).rstrip("/") == f"{_DEFAULT_API_URL}/api/v1"


class TestRequestHeaders:
    def test_user_agent_header(self):
        client = SignalSwarm()
        headers = client._http.headers
        assert headers["user-agent"] == "signalswarm/0.3.0"

    def test_content_type_header(self):
        client = SignalSwarm()
        headers = client._http.headers
        assert headers["content-type"] == "application/json"

    def test_api_key_header_present_when_set(self):
        client = SignalSwarm(api_key="sk-test-123")
        headers = client._http.headers
        assert headers["x-api-key"] == "sk-test-123"

    def test_no_api_key_header_when_empty(self):
        client = SignalSwarm()
        headers = client._http.headers
        assert "x-api-key" not in headers


class TestSolvePowStaticMethod:
    def test_returns_string(self):
        result = SignalSwarm._solve_pow("test-challenge", 1)
        assert isinstance(result, str)

    def test_valid_nonce_difficulty_1(self):
        challenge = "static-pow-test"
        nonce = SignalSwarm._solve_pow(challenge, 1)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("0")

    def test_valid_nonce_difficulty_2(self):
        challenge = "static-pow-test-d2"
        nonce = SignalSwarm._solve_pow(challenge, 2)
        digest = hashlib.sha256((challenge + nonce).encode("utf-8")).hexdigest()
        assert digest.startswith("00")

    def test_deterministic(self):
        n1 = SignalSwarm._solve_pow("deterministic", 2)
        n2 = SignalSwarm._solve_pow("deterministic", 2)
        assert n1 == n2


class TestContextManager:
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with SignalSwarm() as client:
            assert client is not None
            assert isinstance(client, SignalSwarm)

    @pytest.mark.asyncio
    async def test_close(self):
        client = SignalSwarm()
        await client.close()
        # After close, the http client should be closed
        assert client._http.is_closed


class TestFollowRedirects:
    def test_follow_redirects_enabled(self):
        client = SignalSwarm()
        assert client._http.follow_redirects is True
