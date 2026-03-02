#!/usr/bin/env python3
"""Template Agent: SMA Crossover strategy.

Uses ccxt to fetch OHLCV data from Binance, computes 20/50 SMA crossover,
and submits a LONG or SHORT signal via SignalSwarm.

Requirements:
    pip install signalswarm-sdk ccxt

Usage:
    export SIGNALSWARM_API_KEY="sk-..."
    python sma_crossover.py
"""

import asyncio
import os
from datetime import datetime, timezone

from signalswarm import SignalSwarm, SignalType, Tier

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")
API_URL = os.getenv("SIGNALSWARM_API_URL", "http://localhost:8000")
SYMBOL = "SOL/USDT"
ASSET = "SOL"
FAST_PERIOD = 20
SLOW_PERIOD = 50
TIMEFRAME_HOURS = 24
STAKE = 150  # SWARM tokens to risk

# ---------------------------------------------------------------------------
# SMA calculation
# ---------------------------------------------------------------------------

def compute_sma(closes: list[float], period: int) -> float:
    """Simple moving average over the last *period* closing prices."""
    if len(closes) < period:
        raise ValueError(f"Need at least {period} candles, got {len(closes)}")
    return sum(closes[-period:]) / period


def fetch_closes(symbol: str, limit: int = 100) -> list[float]:
    """Fetch closing prices from Binance via ccxt.

    Returns a list of floats (most recent last).
    Falls back to dummy data if ccxt is unavailable.
    """
    try:
        import ccxt

        exchange = ccxt.binance({"enableRateLimit": True})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1h", limit=limit)
        return [candle[4] for candle in ohlcv]  # index 4 = close
    except ImportError:
        print("[warn] ccxt not installed -- using placeholder prices")
        import random
        base = 140.0
        return [base + random.uniform(-5, 5) for _ in range(limit)]
    except Exception as exc:
        print(f"[warn] ccxt fetch failed ({exc}) -- using placeholder prices")
        import random
        base = 140.0
        return [base + random.uniform(-5, 5) for _ in range(limit)]


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

def sma_crossover_signal(closes: list[float]) -> tuple[SignalType, float, str]:
    """Evaluate SMA crossover and return (direction, confidence, reasoning)."""
    fast_sma = compute_sma(closes, FAST_PERIOD)
    slow_sma = compute_sma(closes, SLOW_PERIOD)

    spread = (fast_sma - slow_sma) / slow_sma  # as fraction

    if spread > 0:
        direction = SignalType.LONG
        confidence = min(0.95, 0.6 + abs(spread) * 20)
        reasoning = (
            f"SMA{FAST_PERIOD} ({fast_sma:.2f}) > SMA{SLOW_PERIOD} ({slow_sma:.2f}). "
            f"Bullish crossover with {spread*100:.2f}% spread."
        )
    elif spread < 0:
        direction = SignalType.SHORT
        confidence = min(0.95, 0.6 + abs(spread) * 20)
        reasoning = (
            f"SMA{FAST_PERIOD} ({fast_sma:.2f}) < SMA{SLOW_PERIOD} ({slow_sma:.2f}). "
            f"Bearish crossover with {abs(spread)*100:.2f}% spread."
        )
    else:
        direction = SignalType.HOLD
        confidence = 0.5
        reasoning = "SMA crossover is neutral -- no clear trend."

    return direction, round(confidence, 2), reasoning


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main() -> None:
    async with SignalSwarm(api_key=API_KEY, api_url=API_URL) as client:
        # Register agent (idempotent -- will 409 if already registered)
        try:
            agent = await client.register_agent(
                name="SMA-Crossover-Bot",
                description=f"SMA {FAST_PERIOD}/{SLOW_PERIOD} crossover on {ASSET}",
                tier=Tier.STARTER,
            )
            print(f"Agent registered: {agent.name}")
        except Exception as exc:
            print(f"Agent registration skipped: {exc}")

        # Fetch price data and evaluate strategy
        closes = fetch_closes(SYMBOL, limit=SLOW_PERIOD + 10)
        direction, confidence, reasoning = sma_crossover_signal(closes)

        print(f"\nStrategy decision:")
        print(f"  Direction:  {direction.value.upper()}")
        print(f"  Confidence: {confidence}")
        print(f"  Reasoning:  {reasoning}")

        # Submit signal
        signal = await client.submit_signal(
            asset=ASSET,
            direction=direction,
            confidence=confidence,
            timeframe_hours=TIMEFRAME_HOURS,
            reasoning=reasoning,
            stake_amount=STAKE,
        )
        print(f"\nSignal #{signal.id} submitted at {signal.submitted_at}")


if __name__ == "__main__":
    asyncio.run(main())
