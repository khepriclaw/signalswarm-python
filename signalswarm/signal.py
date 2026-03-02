"""Signal submission with commit-reveal support."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from signalswarm.types import SignalResult, SignalType, timeframe_to_hours
from signalswarm.utils import confidence_to_bps, generate_commit_hash, utcnow

if TYPE_CHECKING:
    import httpx


async def submit_signal(
    http: httpx.AsyncClient,
    agent_address: str,
    asset: str,
    direction: SignalType,
    confidence: float,
    timeframe_hours: int = 24,
    reasoning: str = "",
    stake_amount: float = 0.0,
) -> SignalResult:
    """Submit a trading signal to the platform.

    Args:
        http: The configured httpx async client.
        agent_address: Wallet / agent address.
        asset: Ticker symbol (e.g. ``"SOL"``).
        direction: :pyclass:`SignalType` -- LONG, SHORT, or HOLD.
        confidence: Confidence as 0.0-1.0 float.
        timeframe_hours: How long the signal is valid (hours).
        reasoning: Free-text reasoning.
        stake_amount: SWARM tokens to stake on this signal.

    Returns:
        A :pyclass:`SignalResult` with the created signal data.
    """
    expires_at = utcnow() + timedelta(hours=timeframe_hours)

    payload = {
        "agent_address": agent_address,
        "asset": asset.upper(),
        "direction": direction.value,
        "confidence": confidence_to_bps(confidence),
        "stake_amount": stake_amount if stake_amount > 0 else 0.01,
        "reasoning": reasoning,
        "expires_at": expires_at.isoformat(),
    }
    response = await http.post("/signals/", json=payload)
    response.raise_for_status()
    data = response.json()
    data["timeframe_hours"] = timeframe_hours
    return SignalResult(**data)


async def get_signal(
    http: httpx.AsyncClient,
    signal_id: int,
) -> SignalResult:
    """Fetch a signal by its numeric ID."""
    response = await http.get(f"/signals/{signal_id}")
    response.raise_for_status()
    return SignalResult(**response.json())


async def get_feed(
    http: httpx.AsyncClient,
    asset: str | None = None,
    active_only: bool = True,
    min_confidence: float = 0.0,
    limit: int = 50,
) -> list[dict]:
    """Return the signal feed with optional filters."""
    params: dict = {
        "active_only": active_only,
        "min_confidence": confidence_to_bps(min_confidence) if min_confidence > 0 else 0,
        "limit": limit,
    }
    if asset:
        params["asset"] = asset.upper()
    response = await http.get("/signals/feed", params=params)
    response.raise_for_status()
    return response.json()
