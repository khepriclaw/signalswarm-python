"""Unit tests for signalswarm.exceptions."""

import pytest
from signalswarm.exceptions import (
    AgentNotFoundError,
    AuthenticationError,
    InsufficientStakeError,
    InvalidSignalError,
    NetworkError,
    RateLimitError,
    SignalNotFoundError,
    SignalSwarmError,
    TimeoutError,
)


class TestSignalSwarmError:
    def test_base(self):
        err = SignalSwarmError("test", status_code=500)
        assert str(err) == "test"
        assert err.status_code == 500

    def test_defaults(self):
        err = SignalSwarmError()
        assert err.message == ""
        assert err.status_code is None

    def test_is_exception(self):
        assert issubclass(SignalSwarmError, Exception)


class TestAuthenticationError:
    def test_default_message(self):
        err = AuthenticationError()
        assert "Authentication" in str(err)
        assert err.status_code == 401


class TestAgentNotFoundError:
    def test_with_identifier(self):
        err = AgentNotFoundError("bot-1")
        assert "bot-1" in str(err)
        assert err.status_code == 404

    def test_without_identifier(self):
        err = AgentNotFoundError()
        assert "Agent not found" in str(err)


class TestSignalNotFoundError:
    def test_with_id(self):
        err = SignalNotFoundError(123)
        assert "123" in str(err)
        assert err.status_code == 404


class TestInvalidSignalError:
    def test_default(self):
        err = InvalidSignalError()
        assert err.status_code == 400


class TestInsufficientStakeError:
    def test_amounts(self):
        err = InsufficientStakeError(required=100, provided=50)
        assert err.required == 100
        assert err.provided == 50
        assert "100" in str(err)
        assert "50" in str(err)


class TestRateLimitError:
    def test_retry_after(self):
        err = RateLimitError(retry_after=30.0)
        assert err.retry_after == 30.0
        assert err.status_code == 429

    def test_no_retry_after(self):
        err = RateLimitError()
        assert err.retry_after == 0


class TestNetworkError:
    def test_default(self):
        err = NetworkError()
        assert "Network" in str(err)


class TestTimeoutError:
    def test_default(self):
        err = TimeoutError()
        assert "timed out" in str(err)

    def test_is_signalswarm_error(self):
        assert issubclass(TimeoutError, SignalSwarmError)
