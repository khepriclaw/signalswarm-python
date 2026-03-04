"""Unit tests for signalswarm.types."""

import pytest
from signalswarm.types import (
    Action,
    AgentProfile,
    AgentRegistration,
    FeedItem,
    LeaderboardEntry,
    PriceData,
    SignalResult,
    SignalStatus,
    Tier,
    Timeframe,
    VoteResult,
    timeframe_to_hours,
)


class TestAction:
    def test_values(self):
        assert Action.BUY.value == "BUY"
        assert Action.SELL.value == "SELL"
        assert Action.SHORT.value == "SHORT"
        assert Action.COVER.value == "COVER"
        assert Action.HOLD.value == "HOLD"

    def test_is_string(self):
        assert isinstance(Action.BUY, str)
        assert Action.BUY == "BUY"


class TestTier:
    def test_values(self):
        assert Tier.OBSERVER.value == "observer"
        assert Tier.STARTER.value == "starter"
        assert Tier.PRO.value == "pro"
        assert Tier.ELITE.value == "elite"


class TestTimeframe:
    def test_values(self):
        assert Timeframe.M15.value == "15m"
        assert Timeframe.H1.value == "1h"
        assert Timeframe.H4.value == "4h"
        assert Timeframe.D1.value == "1d"
        assert Timeframe.W1.value == "1w"


class TestTimeframeToHours:
    def test_valid(self):
        assert timeframe_to_hours("1h") == 1
        assert timeframe_to_hours("4h") == 4
        assert timeframe_to_hours("1d") == 24
        assert timeframe_to_hours("1w") == 168
        assert timeframe_to_hours("15m") == 0.25

    def test_from_enum(self):
        assert timeframe_to_hours(Timeframe.D1) == 24

    def test_invalid(self):
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            timeframe_to_hours("3d")


class TestSignalStatus:
    def test_values(self):
        assert SignalStatus.ACTIVE.value == "ACTIVE"
        assert SignalStatus.CLOSED_WIN.value == "CLOSED_WIN"
        assert SignalStatus.CLOSED_LOSS.value == "CLOSED_LOSS"
        assert SignalStatus.EXPIRED.value == "EXPIRED"
        assert SignalStatus.CANCELLED.value == "CANCELLED"


class TestAgentProfile:
    def test_from_dict(self):
        data = {
            "id": 1,
            "username": "test-bot",
            "display_name": "Test Bot",
            "reputation": 500,
            "signals_posted": 10,
            "win_rate": 65.0,
            "tier": "starter",
        }
        agent = AgentProfile(**data)
        assert agent.id == 1
        assert agent.username == "test-bot"
        assert agent.display_name == "Test Bot"
        assert agent.reputation == 500
        assert agent.win_rate == 65.0

    def test_defaults(self):
        agent = AgentProfile(id=1, username="x", display_name="X")
        assert agent.reputation == 0
        assert agent.signals_posted == 0
        assert agent.win_rate == 0.0
        assert agent.tier == "observer"

    def test_extra_fields_allowed(self):
        agent = AgentProfile(
            id=1, username="x", display_name="X", future_field="yes"
        )
        assert agent.future_field == "yes"


class TestAgentRegistration:
    def test_from_dict(self):
        data = {
            "id": 42,
            "username": "new-bot",
            "display_name": "New Bot",
            "api_key": "sk-abc123",
            "tier": "observer",
        }
        reg = AgentRegistration(**data)
        assert reg.id == 42
        assert reg.api_key == "sk-abc123"
        assert reg.tier == "observer"


class TestSignalResult:
    def test_from_dict(self):
        data = {
            "id": 100,
            "agent_id": 1,
            "title": "BTC buy",
            "ticker": "BTC",
            "action": "BUY",
            "analysis": "test analysis",
            "confidence": 85.0,
            "status": "ACTIVE",
            "upvotes": 3,
            "downvotes": 1,
        }
        sig = SignalResult(**data)
        assert sig.id == 100
        assert sig.ticker == "BTC"
        assert sig.action == "BUY"
        assert sig.confidence == 85.0
        assert not sig.is_resolved
        assert not sig.is_win

    def test_is_resolved(self):
        sig = SignalResult(id=1, agent_id=1, status="CLOSED_WIN")
        assert sig.is_resolved
        assert sig.is_win

    def test_is_loss(self):
        sig = SignalResult(id=1, agent_id=1, status="CLOSED_LOSS")
        assert sig.is_resolved
        assert not sig.is_win


class TestLeaderboardEntry:
    def test_from_dict(self):
        data = {
            "rank": 1,
            "agent_id": 5,
            "username": "alpha-bot",
            "display_name": "Alpha Bot",
            "reputation": 9000,
            "win_rate": 78.5,
            "mining_score": 42.3,
        }
        entry = LeaderboardEntry(**data)
        assert entry.rank == 1
        assert entry.mining_score == 42.3


class TestPriceData:
    def test_from_dict(self):
        data = {
            "asset": "BTC",
            "price": 73000.50,
            "timestamp": 1709568000.0,
            "source": "pyth",
            "confidence": 0.99,
        }
        price = PriceData(**data)
        assert price.asset == "BTC"
        assert price.price == 73000.50


class TestVoteResult:
    def test_from_dict(self):
        data = {"message": "Upvoted", "vote_action": "upvoted"}
        vote = VoteResult(**data)
        assert vote.message == "Upvoted"
        assert vote.vote_action == "upvoted"
