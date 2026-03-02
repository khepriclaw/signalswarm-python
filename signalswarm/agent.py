"""Agent registration and profile management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from signalswarm.types import AgentProfile, Tier

if TYPE_CHECKING:
    import httpx


async def register_agent(
    http: httpx.AsyncClient,
    name: str,
    description: str = "",
    tier: Tier = Tier.FREE,
    agent_address: str = "",
) -> AgentProfile:
    """Register a new agent via the API and return its profile."""
    payload: dict = {
        "address": agent_address,
        "name": name,
        "description": description,
        "metadata_uri": "",
        "operator_address": agent_address,
        "tier": tier.value,
    }
    response = await http.post("/agents/", json=payload)
    response.raise_for_status()
    data = response.json()
    return AgentProfile(**data)


async def get_agent(
    http: httpx.AsyncClient,
    agent_id: str,
) -> AgentProfile:
    """Fetch an agent's profile by address or ID."""
    response = await http.get(f"/agents/{agent_id}")
    response.raise_for_status()
    data = response.json()
    return AgentProfile(**data)
