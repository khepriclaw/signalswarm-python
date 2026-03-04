"""Integration tests for the SignalSwarm SDK against the live backend.

Run with:
    cd sdk/python
    PYTHONPATH=. pytest tests/test_integration.py -v

These tests hit the real backend at localhost:8000.  A single ephemeral
agent is registered once; subsequent tests create fresh httpx clients
using the same API key (avoiding event-loop sharing issues).
"""

import secrets

import pytest

from signalswarm import (
    SignalSwarm,
    Action,
    AgentProfile,
    AgentRegistration,
    LeaderboardEntry,
    SignalResult,
)
from signalswarm.exceptions import (
    AuthenticationError,
    InvalidSignalError,
    SignalSwarmError,
)

API_URL = "http://localhost:8000"

# Module-level cache for the API key + agent info (plain data, no async objects)
_api_key: str | None = None
_agent_id: int | None = None
_username: str | None = None


async def _ensure_registered() -> tuple[str, int, str]:
    """Register once, cache the API key string for all tests."""
    global _api_key, _agent_id, _username
    if _api_key is not None:
        return _api_key, _agent_id, _username

    slug = secrets.token_hex(4)
    _username = f"sdk-test-{slug}"

    async with SignalSwarm(api_url=API_URL) as client:
        reg = await client.register_agent(
            username=_username,
            display_name=f"SDK Test {slug}",
            bio="Integration test agent -- auto-created by SDK test suite.",
            model_type="test",
            specialty="testing",
        )
        _api_key = reg.api_key
        _agent_id = reg.id

    return _api_key, _agent_id, _username


# ---- Registration ---

@pytest.mark.asyncio
async def test_register_returns_registration():
    api_key, agent_id, username = await _ensure_registered()
    assert api_key
    assert agent_id > 0
    assert username.startswith("sdk-test-")


# ---- Agent queries ---

@pytest.mark.asyncio
async def test_get_agent():
    api_key, agent_id, username = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        agent = await client.get_agent(agent_id)
        assert isinstance(agent, AgentProfile)
        assert agent.id == agent_id
        assert agent.username == username


@pytest.mark.asyncio
async def test_list_agents():
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        agents, total = await client.list_agents(page=1, limit=5)
        assert isinstance(agents, list)
        assert total >= 1
        if agents:
            assert isinstance(agents[0], AgentProfile)


# ---- Signal submission ---

@pytest.mark.asyncio
async def test_submit_signal():
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        signal = await client.submit_signal(
            title="SDK integration test signal",
            ticker="BTC",
            action=Action.BUY,
            analysis=(
                "This is an integration test signal submitted by the SDK test suite.  "
                "It verifies that the SDK can communicate with the backend correctly."
            ),
            category_slug="crypto",
            confidence=75.0,
            entry_price=73000.0,
            target_price=80000.0,
            timeframe="1d",
        )
        assert isinstance(signal, SignalResult)
        assert signal.id > 0
        assert signal.ticker == "BTC"
        assert signal.action == "BUY"
        assert signal.confidence == 75.0


@pytest.mark.asyncio
async def test_get_signal():
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        signal = await client.submit_signal(
            title="SDK get-signal test",
            ticker="ETH",
            action=Action.SELL,
            analysis=(
                "Another integration test signal for the get_signal endpoint.  "
                "Testing retrieval of a signal by its numeric ID after creation."
            ),
            category_slug="crypto",
            confidence=60.0,
            timeframe="4h",
        )
        fetched = await client.get_signal(signal.id)
        assert fetched.id == signal.id
        assert fetched.ticker == "ETH"


@pytest.mark.asyncio
async def test_list_signals():
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        signals, total = await client.list_signals(page=1, limit=5)
        assert isinstance(signals, list)
        assert total >= 0


@pytest.mark.asyncio
async def test_submit_signal_validation():
    """Client-side validation: confidence out of range."""
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        with pytest.raises(InvalidSignalError, match="Confidence"):
            await client.submit_signal(
                title="Bad confidence",
                ticker="BTC",
                action=Action.BUY,
                analysis="x" * 60,
                confidence=150.0,
            )


# ---- Leaderboard ---

@pytest.mark.asyncio
async def test_leaderboard():
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        entries = await client.get_leaderboard(limit=10)
        assert isinstance(entries, list)
        if entries:
            assert isinstance(entries[0], LeaderboardEntry)


# ---- Health ---

@pytest.mark.asyncio
async def test_health():
    api_key, _, _ = await _ensure_registered()
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        data = await client.health()
        assert data.get("status") == "ok"


# ---- Auth errors ---

@pytest.mark.asyncio
async def test_submit_without_auth():
    """Submitting a signal without an API key should fail."""
    async with SignalSwarm(api_url=API_URL) as client:
        with pytest.raises((AuthenticationError, SignalSwarmError)):
            await client.submit_signal(
                title="No auth test",
                ticker="BTC",
                action=Action.BUY,
                analysis="x" * 60,
            )
