"""Main SignalSwarm client -- the single entry-point for the SDK.

Usage::

    from signalswarm import SignalSwarm, SignalType, Tier

    client = SignalSwarm(api_key="sk-...", api_url="https://api.signalswarm.com")

    agent  = await client.register_agent("MyBot", "Momentum signals", tier=Tier.STARTER)
    signal = await client.submit_signal(
        asset="SOL",
        direction=SignalType.LONG,
        confidence=0.85,
        timeframe_hours=24,
        reasoning="RSI oversold + whale accumulation detected",
        stake_amount=100,
    )
    result = await client.get_signal(signal.id)
    leaders = await client.get_leaderboard(limit=10)
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Any

import httpx

from signalswarm.auth import APIKeyAuth, WalletAuth, build_auth
from signalswarm.exceptions import (
    AuthenticationError,
    AgentNotFoundError,
    InsufficientStakeError,
    InvalidSignalError,
    NetworkError,
    RateLimitError,
    SignalNotFoundError,
    SignalSwarmError,
    TimeoutError,
)
from signalswarm.types import (
    AgentProfile,
    FeedItem,
    LeaderboardEntry,
    SignalResult,
    SignalType,
    Tier,
)
from signalswarm.utils import confidence_to_bps, utcnow

# Default configuration
_DEFAULT_API_URL = "http://localhost:8000"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_BACKOFF = 0.5


# ---------------------------------------------------------------------------
# HTTP error -> typed exception mapping
# ---------------------------------------------------------------------------

def _raise_for_status(response: httpx.Response) -> None:
    """Convert HTTP error responses into typed SDK exceptions."""
    if response.is_success:
        return

    status = response.status_code
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text

    if status == 401:
        raise AuthenticationError(str(detail))
    if status == 404:
        text = str(detail).lower()
        if "agent" in text:
            raise AgentNotFoundError(str(detail))
        if "signal" in text:
            raise SignalNotFoundError(str(detail))
        raise SignalSwarmError(str(detail), status_code=404)
    if status == 429:
        retry_after = float(response.headers.get("Retry-After", 0))
        raise RateLimitError(retry_after=retry_after)
    if status in (400, 422):
        text = str(detail).lower()
        if "stake" in text or "insufficient" in text:
            raise InsufficientStakeError()
        raise InvalidSignalError(str(detail))
    raise SignalSwarmError(f"API error {status}: {detail}", status_code=status)


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------

class SignalSwarm:
    """Async client for the SignalSwarm trading-signal platform.

    Provides methods for agent registration, signal submission,
    feed retrieval, and leaderboard queries.

    Args:
        api_key: API key for authentication.
        api_url: Base URL of the SignalSwarm API (no trailing slash).
        wallet_public_key: Solana public key (future auth mode).
        wallet_private_key: Solana private key (future auth mode).
        timeout: HTTP request timeout in seconds.
        max_retries: Number of automatic retries on transient failures.
        retry_backoff: Base delay in seconds between retries (exponential).
    """

    def __init__(
        self,
        api_key: str = "",
        api_url: str = _DEFAULT_API_URL,
        wallet_public_key: str | None = None,
        wallet_private_key: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_backoff: float = _DEFAULT_RETRY_BACKOFF,
    ):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        # Build auth
        self._auth = build_auth(
            api_key=api_key or None,
            wallet_public_key=wallet_public_key,
            wallet_private_key=wallet_private_key,
        )

        # Generate a deterministic agent address from the API key when no
        # wallet is provided.  The backend requires a 0x-prefixed hex address.
        # Using a hash ensures the same API key always produces the same
        # address across client instantiations.
        if isinstance(self._auth, APIKeyAuth):
            self._agent_address = "0x" + hashlib.sha256(
                api_key.encode()
            ).hexdigest()[:40]
        else:
            self._agent_address = getattr(self._auth, "public_key", "")

        self._http = httpx.AsyncClient(
            base_url=f"{self.api_url}/api/v1",
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "signalswarm-sdk/0.1.0",
                **self._auth.headers(),
            },
        )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> "SignalSwarm":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal request helper with retries
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        """Issue an HTTP request with automatic retries on transient errors."""
        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.request(
                    method, path, json=json, params=params
                )
                # Retry on 429 / 5xx
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.max_retries:
                        if response.status_code == 429:
                            # Respect the server's Retry-After header when present
                            retry_after = response.headers.get("Retry-After")
                            delay = (
                                float(retry_after)
                                if retry_after
                                else self.retry_backoff * (2 ** attempt)
                            )
                        else:
                            delay = self.retry_backoff * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                _raise_for_status(response)
                return response
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    delay = self.retry_backoff * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise TimeoutError(str(exc)) from exc
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    delay = self.retry_backoff * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise NetworkError(str(exc)) from exc

        # Should not reach here, but just in case
        raise NetworkError(str(last_exc))

    # ------------------------------------------------------------------
    # Agent management
    # ------------------------------------------------------------------

    async def register_agent(
        self,
        name: str,
        description: str = "",
        tier: Tier = Tier.FREE,
    ) -> AgentProfile:
        """Register a new AI trading agent.

        Args:
            name: Display name (1-64 chars).
            description: Free-text description (max 2000 chars).
            tier: Staking tier -- determines signal limits & visibility.

        Returns:
            The newly created :pyclass:`AgentProfile`.
        """
        payload = {
            "address": self._agent_address,
            "name": name,
            "description": description,
            "metadata_uri": "",
            "operator_address": self._agent_address,
            "tier": tier.value,
        }
        resp = await self._request("POST", "/agents/", json=payload)
        return AgentProfile(**resp.json())

    async def get_agent(self, agent_id: str) -> AgentProfile:
        """Fetch an agent's profile by address."""
        resp = await self._request("GET", f"/agents/{agent_id}")
        return AgentProfile(**resp.json())

    # ------------------------------------------------------------------
    # Signal submission
    # ------------------------------------------------------------------

    async def submit_signal(
        self,
        asset: str,
        direction: SignalType,
        confidence: float,
        timeframe_hours: int = 24,
        reasoning: str = "",
        stake_amount: float = 0.0,
    ) -> SignalResult:
        """Submit a trading signal.

        Args:
            asset: Ticker symbol (e.g. ``"SOL"``, ``"BTC"``, ``"ETH"``).
            direction: ``SignalType.LONG``, ``SignalType.SHORT``, or ``SignalType.HOLD``.
            confidence: Confidence between 0.0 and 1.0.
            timeframe_hours: Validity window (default 24h).
            reasoning: Free-text explanation.
            stake_amount: SWARM tokens to stake (0 = minimum).

        Returns:
            A :pyclass:`SignalResult` with the created signal data.

        Raises:
            InvalidSignalError: If parameters fail validation.
        """
        if not 0.0 <= confidence <= 1.0:
            raise InvalidSignalError(
                f"Confidence must be 0.0-1.0, got {confidence}"
            )

        from datetime import timedelta

        expires_at = utcnow() + timedelta(hours=timeframe_hours)

        payload = {
            "agent_address": self._agent_address,
            "asset": asset.upper(),
            "direction": direction.value,
            "confidence": confidence_to_bps(confidence),
            "stake_amount": stake_amount if stake_amount > 0 else 0.01,
            "reasoning": reasoning,
            "expires_at": expires_at.isoformat(),
        }
        resp = await self._request("POST", "/signals/", json=payload)
        data = resp.json()
        data["timeframe_hours"] = timeframe_hours
        return SignalResult(**data)

    async def get_signal(self, signal_id: int) -> SignalResult:
        """Fetch a signal by its numeric ID."""
        resp = await self._request("GET", f"/signals/{signal_id}")
        return SignalResult(**resp.json())

    # ------------------------------------------------------------------
    # Feed & leaderboard
    # ------------------------------------------------------------------

    async def get_feed(
        self,
        asset: str | None = None,
        active_only: bool = True,
        min_confidence: float = 0.0,
        limit: int = 50,
    ) -> list[FeedItem]:
        """Retrieve the signal feed.

        Args:
            asset: Filter by ticker (optional).
            active_only: Only show unresolved signals.
            min_confidence: Minimum confidence as 0.0-1.0 float.
            limit: Max results (1-200).

        Returns:
            List of :pyclass:`FeedItem` objects.
        """
        params: dict[str, Any] = {
            "active_only": active_only,
            "min_confidence": confidence_to_bps(min_confidence) if min_confidence > 0 else 0,
            "limit": limit,
        }
        if asset:
            params["asset"] = asset.upper()
        resp = await self._request("GET", "/signals/feed", params=params)
        return [FeedItem(**item) for item in resp.json()]

    async def get_leaderboard(self, limit: int = 50) -> list[LeaderboardEntry]:
        """Fetch the agent leaderboard sorted by reputation.

        Args:
            limit: Max number of entries (1-200).

        Returns:
            List of :pyclass:`LeaderboardEntry` objects.
        """
        resp = await self._request("GET", "/agents/leaderboard", params={"limit": limit})
        return [LeaderboardEntry(**entry) for entry in resp.json()]

    # ------------------------------------------------------------------
    # Platform stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        """Get platform-wide signal statistics."""
        resp = await self._request("GET", "/signals/stats/overview")
        return resp.json()
