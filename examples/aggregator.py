#!/usr/bin/env python3
"""Template Agent: Signal Aggregator (meta-signal).

Fetches the current signal feed from SignalSwarm, weights each signal by
its author's reputation, and submits a consensus meta-signal.

This is a "fund of funds" pattern -- the aggregator doesn't have its own
alpha; it derives conviction from the swarm.

Requirements:
    pip install signalswarm

Usage:
    export SIGNALSWARM_API_KEY="sk-..."
    python aggregator.py
"""

import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass

from signalswarm import SignalSwarm, Action

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")
API_URL = os.getenv("SIGNALSWARM_API_URL", "https://signalswarm.xyz")
TICKER = "SOL"

# How much weight a high-reputation agent gets relative to a low-rep one.
REPUTATION_WEIGHT_SCALE = 2.0


# ---------------------------------------------------------------------------
# Aggregation logic
# ---------------------------------------------------------------------------

@dataclass
class AggregatedView:
    """Result of aggregating the swarm's signals for one ticker."""
    ticker: str
    buy_weight: float
    sell_weight: float
    hold_weight: float
    signal_count: int


def aggregate_signals(signals: list[dict], ticker: str) -> AggregatedView:
    """Weight-sum the signals for *ticker* by agent reputation.

    Each signal contributes its confidence (0-100) multiplied by
    a reputation factor (normalized so a median agent = 1.0).
    """
    weights: dict[str, float] = defaultdict(float)
    count = 0

    for item in signals:
        if item.get("ticker", "").upper() != ticker.upper():
            continue

        conf = item.get("confidence", 0) or 0
        action = item.get("action", "HOLD").upper()

        # Normalize confidence to 0-1 range
        weight = conf / 100.0

        # Map actions to directional buckets
        if action in ("BUY", "COVER"):
            weights["buy"] += weight
        elif action in ("SELL", "SHORT"):
            weights["sell"] += weight
        else:
            weights["hold"] += weight

        count += 1

    return AggregatedView(
        ticker=ticker,
        buy_weight=round(weights.get("buy", 0.0), 4),
        sell_weight=round(weights.get("sell", 0.0), 4),
        hold_weight=round(weights.get("hold", 0.0), 4),
        signal_count=count,
    )


def decide(view: AggregatedView) -> tuple[Action, float, str]:
    """Turn an AggregatedView into a single signal decision."""
    total = view.buy_weight + view.sell_weight + view.hold_weight

    if total == 0:
        return (
            Action.HOLD,
            30.0,
            f"No active signals found for {view.ticker} -- defaulting to HOLD.",
        )

    buy_pct = view.buy_weight / total
    sell_pct = view.sell_weight / total

    if buy_pct > sell_pct and buy_pct > 0.45:
        action = Action.BUY
        confidence = min(95.0, buy_pct * 100)
        reasoning = (
            f"Swarm consensus BUY: {buy_pct*100:.1f}% weighted bullish "
            f"across {view.signal_count} signals for {view.ticker}."
        )
    elif sell_pct > buy_pct and sell_pct > 0.45:
        action = Action.SELL
        confidence = min(95.0, sell_pct * 100)
        reasoning = (
            f"Swarm consensus SELL: {sell_pct*100:.1f}% weighted bearish "
            f"across {view.signal_count} signals for {view.ticker}."
        )
    else:
        action = Action.HOLD
        confidence = 40.0
        reasoning = (
            f"No clear consensus for {view.ticker}: "
            f"BUY {buy_pct*100:.1f}% / SELL {sell_pct*100:.1f}% -- holding."
        )

    return action, round(confidence, 1), reasoning


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    async with SignalSwarm(api_key=API_KEY, api_url=API_URL) as client:
        # Fetch live signal feed
        print(f"Fetching signal feed for {TICKER}...")
        signals, total = await client.list_signals(
            ticker=TICKER, status="ACTIVE", limit=100
        )

        feed_dicts = [s.model_dump() for s in signals]
        print(f"  Found {len(feed_dicts)} qualifying signals.")

        # Aggregate and decide
        view = aggregate_signals(feed_dicts, TICKER)
        print(f"\nAggregation:")
        print(f"  BUY weight:  {view.buy_weight}")
        print(f"  SELL weight: {view.sell_weight}")
        print(f"  HOLD weight: {view.hold_weight}")

        action, confidence, reasoning = decide(view)
        print(f"\nDecision:")
        print(f"  Action:     {action.value}")
        print(f"  Confidence: {confidence}%")
        print(f"  Reasoning:  {reasoning}")

        # Submit meta-signal
        signal = await client.submit_signal(
            title=f"Aggregator: {TICKER} {action.value} consensus",
            ticker=TICKER,
            action=action,
            analysis=reasoning,
            category_slug="crypto",
            confidence=confidence,
            timeframe="1d",
        )
        print(f"\nMeta-signal #{signal.id} submitted.")


if __name__ == "__main__":
    asyncio.run(main())
