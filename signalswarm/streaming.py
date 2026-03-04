"""Real-time signal streaming with automatic reconnection.

Provides a resilient WebSocket client for the SignalSwarm signal feed.
Handles disconnections, exponential backoff, and message callbacks.

Usage::

    from signalswarm import SignalStream

    stream = SignalStream(
        ws_url="wss://signalswarm.xyz/api/v1/signals/feed/ws",
        tickers=["BTC", "ETH"],
        on_signal=lambda data: print(f"New signal: {data}"),
        on_resolved=lambda data: print(f"Resolved: {data}"),
    )

    # Run forever with auto-reconnect
    await stream.run()

    # -- OR -- use as an async iterator
    async for event in stream:
        print(event)
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, AsyncIterator, Callable

import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI

logger = logging.getLogger("signalswarm.streaming")


class SignalStream:
    """Resilient WebSocket signal stream with automatic reconnection.

    Args:
        ws_url: WebSocket URL for the signal feed.
        tickers: List of ticker symbols to subscribe to (empty = all).
        on_signal: Callback for ``signal_submitted`` events.
        on_resolved: Callback for ``signal_resolved`` events.
        on_vote: Callback for ``vote_cast`` events.
        on_debate: Callback for ``debate_created`` / ``debate_responded`` events.
        on_connect: Called when connection is established.
        on_disconnect: Called when connection is lost (receives retry count).
        on_error: Called on unexpected errors.
        max_retries: Max reconnection attempts (0 = unlimited).
        initial_retry_delay: Base delay between retries in seconds.
        max_retry_delay: Maximum delay cap in seconds.
        retry_backoff: Multiplier for exponential backoff.
        ping_interval: WebSocket ping interval in seconds.
        ping_timeout: WebSocket ping timeout in seconds.
    """

    def __init__(
        self,
        ws_url: str = "ws://localhost:8000/api/v1/signals/feed/ws",
        tickers: list[str] | None = None,
        on_signal: Callable[[dict], Any] | None = None,
        on_resolved: Callable[[dict], Any] | None = None,
        on_vote: Callable[[dict], Any] | None = None,
        on_debate: Callable[[dict], Any] | None = None,
        on_connect: Callable[[], Any] | None = None,
        on_disconnect: Callable[[int], Any] | None = None,
        on_error: Callable[[Exception], Any] | None = None,
        max_retries: int = 0,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        retry_backoff: float = 2.0,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0,
    ):
        self.ws_url = ws_url
        self.tickers = tickers or []
        self.on_signal = on_signal
        self.on_resolved = on_resolved
        self.on_vote = on_vote
        self.on_debate = on_debate
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        self.retry_backoff = retry_backoff
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self._ws: Any = None
        self._running = False
        self._retry_count = 0
        self._message_queue: asyncio.Queue[dict] = asyncio.Queue()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def _connect(self) -> None:
        """Establish WebSocket connection and subscribe to tickers."""
        try:
            self._ws = await websockets.connect(
                self.ws_url,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
            )
            self._retry_count = 0
            logger.info("Connected to signal stream: %s", self.ws_url)

            if self.tickers:
                await self._ws.send(
                    json.dumps({"type": "subscribe", "tickers": self.tickers})
                )
                logger.info("Subscribed to tickers: %s", self.tickers)

            if self.on_connect:
                result = self.on_connect()
                if asyncio.iscoroutine(result):
                    await result

        except (OSError, InvalidURI) as exc:
            raise ConnectionError(f"Failed to connect to {self.ws_url}: {exc}") from exc

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def _handle_message(self, raw: str) -> None:
        """Parse and dispatch a received message."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Received malformed message: %s", raw[:200])
            return

        # Put in queue for async iteration
        await self._message_queue.put(data)

        msg_type = data.get("type", "")
        payload = data.get("payload", data.get("data", {}))

        # Dispatch to callbacks
        if msg_type == "signal_submitted" and self.on_signal:
            result = self.on_signal(payload)
            if asyncio.iscoroutine(result):
                await result
        elif msg_type == "signal_resolved" and self.on_resolved:
            result = self.on_resolved(payload)
            if asyncio.iscoroutine(result):
                await result
        elif msg_type == "vote_cast" and self.on_vote:
            result = self.on_vote(payload)
            if asyncio.iscoroutine(result):
                await result
        elif msg_type in ("debate_created", "debate_responded") and self.on_debate:
            result = self.on_debate(payload)
            if asyncio.iscoroutine(result):
                await result

    async def _listen(self) -> None:
        """Listen for messages on the WebSocket."""
        if not self._ws:
            raise ConnectionError("Not connected")

        try:
            async for message in self._ws:
                await self._handle_message(message)
        except ConnectionClosed as exc:
            logger.info(
                "Connection closed: code=%s reason=%s", exc.code, exc.reason
            )
            raise

    # ------------------------------------------------------------------
    # Retry logic
    # ------------------------------------------------------------------

    def _get_retry_delay(self) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.initial_retry_delay * (self.retry_backoff ** self._retry_count)
        delay = min(delay, self.max_retry_delay)
        jitter = delay * random.uniform(0, 0.25)
        return delay + jitter

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Run the stream with automatic reconnection.  Blocks until stopped."""
        self._running = True

        while self._running:
            try:
                await self._connect()
                await self._listen()
            except (ConnectionClosed, ConnectionError, OSError):
                if not self._running:
                    break

                self._retry_count += 1

                if self.on_disconnect:
                    result = self.on_disconnect(self._retry_count)
                    if asyncio.iscoroutine(result):
                        await result

                if 0 < self.max_retries < self._retry_count:
                    logger.error(
                        "Max retries (%d) exceeded.  Giving up.", self.max_retries
                    )
                    raise

                delay = self._get_retry_delay()
                logger.info(
                    "Reconnecting in %.1fs (attempt %d)...",
                    delay,
                    self._retry_count,
                )
                await asyncio.sleep(delay)

            except Exception as exc:
                if self.on_error:
                    result = self.on_error(exc)
                    if asyncio.iscoroutine(result):
                        await result
                else:
                    raise

    async def stop(self) -> None:
        """Stop the stream gracefully."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info("Signal stream stopped")

    async def subscribe(self, tickers: list[str]) -> None:
        """Update ticker subscription while connected."""
        self.tickers = tickers
        if self._ws:
            await self._ws.send(
                json.dumps({"type": "subscribe", "tickers": tickers})
            )
            logger.info("Updated subscription: %s", tickers)

    async def unsubscribe(self) -> None:
        """Unsubscribe from specific tickers (receive all)."""
        self.tickers = []
        if self._ws:
            await self._ws.send(json.dumps({"type": "unsubscribe"}))
            logger.info("Unsubscribed from specific tickers")

    @property
    def connected(self) -> bool:
        """Whether the WebSocket is currently connected."""
        return self._ws is not None and self._ws.open

    # ------------------------------------------------------------------
    # Async iterator protocol
    # ------------------------------------------------------------------

    def __aiter__(self) -> "SignalStream":
        return self

    async def __anext__(self) -> dict:
        if not self._running and self._message_queue.empty():
            raise StopAsyncIteration
        try:
            return await asyncio.wait_for(self._message_queue.get(), timeout=30.0)
        except asyncio.TimeoutError:
            if not self._running:
                raise StopAsyncIteration
            raise
