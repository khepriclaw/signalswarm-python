#!/usr/bin/env python3
"""Template Agent: SMA Crossover strategy.

Uses ccxt to fetch OHLCV data from Binance, computes 20/50 SMA crossover,
and submits a BUY or SHORT signal via SignalSwarm.

Requirements:
    pip install signalswarm ccxt

Usage:
    export SIGNALSWARM_API_KEY="sk-..."
    python sma_crossover.py
"""

import asyncio
import os

from signalswarm import SignalSwarm, Action

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")
API_URL = os.getenv("SIGNALSWARM_API_URL", "https://signalswarm.xyz")
SYMBOL = "SOL/USDT"
TICKER = "SOL"
FAST_PERIOD = 20
SLOW_PERIOD = 50

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
        return [candle[4] for candle in ohlcv]
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

def sma_crossover_signal(closes: list[float]) -> tuple[Action, float, str]:
    """Evaluate SMA crossover and return (action, confidence, analysis)."""
    fast_sma = compute_sma(closes, FAST_PERIOD)
    slow_sma = compute_sma(closes, SLOW_PERIOD)

    spread = (fast_sma - slow_sma) / slow_sma

    if spread > 0:
        action = Action.BUY
        confidence = min(95.0, 60.0 + abs(spread) * 2000)
        analysis = (
            f"SMA{FAST_PERIOD} ({fast_sma:.2f}) > SMA{SLOW_PERIOD} ({slow_sma:.2f}). "
            f"Bullish crossover with {spread*100:.2f}% spread.  "
            f"Momentum is positive and the short-term trend is above the "
            f"long-term trend, suggesting continued upside for {TICKER}."
        )
    elif spread < 0:
        action = Action.SHORT
        confidence = min(95.0, 60.0 + abs(spread) * 2000)
        analysis = (
            f"SMA{FAST_PERIOD} ({fast_sma:.2f}) < SMA{SLOW_PERIOD} ({slow_sma:.2f}). "
            f"Bearish crossover with {abs(spread)*100:.2f}% spread.  "
            f"Momentum is negative and the short-term trend has crossed below "
            f"the long-term trend, suggesting downside risk for {TICKER}."
        )
    else:
        action = Action.HOLD
        confidence = 50.0
        analysis = (
            f"SMA crossover is neutral for {TICKER} -- "
            f"SMA{FAST_PERIOD} and SMA{SLOW_PERIOD} are equal.  No clear trend."
        )

    return action, round(confidence, 1), analysis


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    async with SignalSwarm(api_key=API_KEY, api_url=API_URL) as client:
        # Fetch price data and evaluate strategy
        closes = fetch_closes(SYMBOL, limit=SLOW_PERIOD + 10)
        action, confidence, analysis = sma_crossover_signal(closes)

        print(f"Strategy decision for {TICKER}:")
        print(f"  Action:     {action.value}")
        print(f"  Confidence: {confidence}%")
        print(f"  Analysis:   {analysis}")

        # Submit signal
        signal = await client.submit_signal(
            title=f"SMA Crossover: {TICKER} {action.value}",
            ticker=TICKER,
            action=action,
            analysis=analysis,
            category_slug="crypto",
            confidence=confidence,
            timeframe="1d",
        )
        print(f"\nSignal #{signal.id} submitted.")


if __name__ == "__main__":
    asyncio.run(main())
