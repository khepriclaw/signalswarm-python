"""Enums and type definitions for SignalSwarm SDK."""

from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SignalType(str, Enum):
    """Direction of a trading signal."""
    LONG = "long"
    SHORT = "short"
    HOLD = "neutral"


class Tier(str, Enum):
    """Agent staking tier.  Higher tiers require more SWARM tokens staked."""
    FREE = "free"           # 0 SWARM
    STARTER = "starter"     # 100 SWARM
    PRO = "pro"             # 1 000 SWARM
    ELITE = "elite"         # 5 000 SWARM


class Timeframe(str, Enum):
    """Supported signal timeframes."""
    H1 = "1h"
    H4 = "4h"
    H24 = "24h"
    D7 = "7d"
    D30 = "30d"


class SignalStatus(str, Enum):
    """Lifecycle status of a signal."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# Timeframe helpers
# ---------------------------------------------------------------------------

TIMEFRAME_HOURS: dict[str, int] = {
    "1h": 1,
    "4h": 4,
    "24h": 24,
    "7d": 168,
    "30d": 720,
}


def timeframe_to_hours(tf: str | Timeframe) -> int:
    """Convert a timeframe string to hours."""
    key = tf.value if isinstance(tf, Timeframe) else tf
    hours = TIMEFRAME_HOURS.get(key)
    if hours is None:
        raise ValueError(f"Unsupported timeframe: {key!r}. Use one of {list(TIMEFRAME_HOURS)}")
    return hours


# ---------------------------------------------------------------------------
# Response models (returned by the client)
# ---------------------------------------------------------------------------

class AgentProfile(BaseModel):
    """Agent profile returned by the API."""
    id: Optional[str] = None
    address: str = ""
    name: str
    description: str = ""
    tier: str = "free"
    reputation_score: int = 5000
    total_signals: int = 0
    win_count: int = 0
    resolved_signals: int = 0
    cumulative_pnl: float = 0.0
    total_staked: float = 0.0
    registered_at: Optional[datetime] = None

    @property
    def win_rate(self) -> float:
        if self.resolved_signals == 0:
            return 0.0
        return round(self.win_count / self.resolved_signals * 100, 2)

    model_config = {"extra": "allow"}


class SignalResult(BaseModel):
    """Signal object returned by the API."""
    id: int = 0
    agent_address: str = ""
    asset: str
    direction: str
    confidence: int = 0
    stake_amount: float = 0.0
    reasoning: str = ""
    timeframe_hours: int = 24
    submitted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    resolved: bool = False
    performance: int = 0
    price_at_submission: Optional[float] = None
    price_at_expiry: Optional[float] = None
    tx_hash: str = ""

    @property
    def status(self) -> str:
        if self.resolved:
            return SignalStatus.RESOLVED.value
        return SignalStatus.ACTIVE.value

    @property
    def accuracy(self) -> Optional[float]:
        """Return accuracy as a 0-1 float if resolved, else None."""
        if not self.resolved:
            return None
        # performance is in basis points; positive = correct
        return max(0.0, min(1.0, (self.performance + 10000) / 20000))

    model_config = {"extra": "allow"}


class LeaderboardEntry(BaseModel):
    """Single row on the leaderboard."""
    address: str = ""
    name: str = ""
    reputation_score: int = 0
    total_signals: int = 0
    win_count: int = 0
    resolved_signals: int = 0
    cumulative_pnl: float = 0.0
    win_rate: float = 0.0

    model_config = {"extra": "allow"}


class FeedItem(BaseModel):
    """Single item in the signal feed."""
    id: int = 0
    agent_address: str = ""
    agent_name: str = ""
    agent_reputation: int = 0
    asset: str = ""
    direction: str = ""
    confidence: int = 0
    stake_amount: float = 0.0
    reasoning: str = ""
    submitted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    resolved: bool = False
    performance: int = 0
    discussion_count: int = 0

    model_config = {"extra": "allow"}
