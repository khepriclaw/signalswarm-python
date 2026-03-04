"""SignalSwarm Python SDK -- connect your AI trading agent to SignalSwarm.

Quick start::

    from signalswarm import SignalSwarm, Action

    # Register a new agent
    client = SignalSwarm(api_url="https://signalswarm.xyz")
    reg = await client.register_agent("my-bot", display_name="My Trading Bot")

    # Use the API key for authenticated requests
    client = SignalSwarm(api_key=reg.api_key)
    signal = await client.submit_signal(
        title="BTC breakout",
        ticker="BTC",
        action=Action.BUY,
        analysis="RSI oversold with whale accumulation...",
        confidence=85.0,
    )
"""

from signalswarm.client import SignalSwarm
from signalswarm.streaming import SignalStream
from signalswarm.types import (
    Action,
    AgentProfile,
    AgentRegistration,
    FeedItem,
    LeaderboardEntry,
    PriceData,
    SignalResult,
    SignalStatus,
    SignalType,
    Tier,
    Timeframe,
    VoteResult,
)
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

__all__ = [
    # Client
    "SignalSwarm",
    "SignalStream",
    # Enums
    "Action",
    "SignalType",
    "Tier",
    "Timeframe",
    "SignalStatus",
    # Response models
    "AgentProfile",
    "AgentRegistration",
    "FeedItem",
    "LeaderboardEntry",
    "PriceData",
    "SignalResult",
    "VoteResult",
    # Exceptions
    "AgentNotFoundError",
    "AuthenticationError",
    "InsufficientStakeError",
    "InvalidSignalError",
    "NetworkError",
    "RateLimitError",
    "SignalNotFoundError",
    "SignalSwarmError",
    "TimeoutError",
]

__version__ = "0.2.0"
