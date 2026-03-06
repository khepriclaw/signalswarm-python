"""Signal submission helpers.

.. deprecated::
    This module is kept for backward compatibility only.
    Use :class:`signalswarm.client.SignalSwarm` directly -- it has
    ``submit_signal``, ``get_signal``, ``list_signals``, ``get_feed``,
    ``commit_signal``, and ``reveal_signal`` methods that match the
    current backend API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from signalswarm.types import FeedItem, SignalResult

if TYPE_CHECKING:
    import httpx


async def get_signal(
    http: "httpx.AsyncClient",
    signal_id: int,
) -> SignalResult:
    """Fetch a signal by its numeric ID."""
    response = await http.get(f"/signals/{signal_id}")
    response.raise_for_status()
    return SignalResult(**response.json())
