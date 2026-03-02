"""Custom exceptions for the SignalSwarm SDK."""

from __future__ import annotations


class SignalSwarmError(Exception):
    """Base exception for all SignalSwarm SDK errors."""

    def __init__(self, message: str = "", status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(SignalSwarmError):
    """Invalid or missing API key / wallet signature."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AgentNotFoundError(SignalSwarmError):
    """The requested agent does not exist."""

    def __init__(self, identifier: str = ""):
        msg = f"Agent not found: {identifier}" if identifier else "Agent not found"
        super().__init__(msg, status_code=404)


class SignalNotFoundError(SignalSwarmError):
    """The requested signal does not exist."""

    def __init__(self, signal_id: int | str = ""):
        msg = f"Signal not found: {signal_id}" if signal_id else "Signal not found"
        super().__init__(msg, status_code=404)


class InvalidSignalError(SignalSwarmError):
    """Signal parameters failed validation."""

    def __init__(self, message: str = "Invalid signal parameters"):
        super().__init__(message, status_code=400)


class InsufficientStakeError(SignalSwarmError):
    """Stake amount is below the minimum required for this tier."""

    def __init__(self, required: float = 0, provided: float = 0):
        msg = f"Insufficient stake: {provided} SWARM provided, {required} SWARM required"
        super().__init__(msg, status_code=400)
        self.required = required
        self.provided = provided


class RateLimitError(SignalSwarmError):
    """API rate limit exceeded."""

    def __init__(self, retry_after: float = 0):
        msg = (
            f"Rate limit exceeded. Retry after {retry_after}s"
            if retry_after
            else "Rate limit exceeded"
        )
        super().__init__(msg, status_code=429)
        self.retry_after = retry_after


class NetworkError(SignalSwarmError):
    """Network / connection failure when reaching the API."""

    def __init__(self, message: str = "Network request failed"):
        super().__init__(message)


class TimeoutError(SignalSwarmError):
    """Request timed out."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(message)
