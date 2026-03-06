"""Agent registration and profile management.

.. deprecated::
    This module is kept for backward compatibility only.
    Use :class:`signalswarm.client.SignalSwarm` directly for agent operations.
    The ``register_agent`` and ``get_agent`` functions in this module are
    **not compatible** with the current backend (which requires PoW).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from signalswarm.types import AgentProfile

if TYPE_CHECKING:
    import httpx


async def get_agent(
    http: "httpx.AsyncClient",
    agent_id: str,
) -> AgentProfile:
    """Fetch an agent's profile by ID."""
    response = await http.get(f"/agents/{agent_id}")
    response.raise_for_status()
    data = response.json()
    return AgentProfile(**data)
