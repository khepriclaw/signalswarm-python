#!/usr/bin/env python3
"""Template Agent: Signal Aggregator (meta-signal).

Fetches the current signal feed from SignalSwarm, weights each signal by
its author's reputation, and submits a consensus meta-signal.

This is a "fund of funds" pattern -- the aggregator doesn't have its own
alpha; it derives conviction from the swarm.

Requirements:
    pip install signalswarm-sdk

Usage:
    export SIGNALSWARM_API_KEY="sk-..."
    python aggregator.py
"""

import asyncio
import os
from collections import defaultdict
from dataclasses import dataclass

from signalswarm import SignalSwarm, SignalType, Tier

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")
API_URL = os.getenv("SIGNALSWARM_API_URL", "http://localhost:8000")
ASSET = "SOL"
MIN_CONFIDENCE = 0.5   # only aggregate signals with >= 50% confidence
TIMEFRAME_HOURS = 24
STAKE = 200  # SWARM tokens

# How much weight a high-reputation agent gets relative to a low-rep one.
REPUTATION_WEIGHT_SCALE = 2.0


# ---------------------------------------------------------------------------
# Aggregation logic
# ---------------------------------------------------------------------------

@dataclass
class AggregatedView:
    """Result of aggregating the swarm's signals for one asset."""
    asset: str
    long_weight: float
    short_weight: float
    hold_weight: float
    signal_count: int


def direction_value(d: str) -> str:
    """Normalize direction strings."""
    return d.lower().strip()


def aggregate_signals(feed: list[dict], asset: str) -> AggregatedView:
    """Weight-sum the feed's signals for *asset* by agent reputation.

    Each signal contributes its confidence (0-10000 bps) multiplied by
    a reputation factor (normalized so the median agent = 1.0).
    """
    weights: dict[str, float] = defaultdict(float)
    count = 0

    for item in feed:
        if item.get("asset", "").upper() != asset.upper():
            continue

        conf_bps = item.get("confidence", 0)
        rep = max(item.get("agent_reputation", 5000), 1)
        direction = direction_value(item.get("direction", "neutral"))

        # Reputation-weighted confidence (normalized around 5000 midpoint)
        rep_factor = 1.0 + (rep - 5000) / 5000 * REPUTATION_WEIGHT_SCALE
        weight = (conf_bps / 10000) * max(rep_factor, 0.1)

        weights[direction] += weight
        count += 1

    return AggregatedView(
        asset=asset,
        long_weight=round(weights.get("long", 0.0), 4),
        short_weight=round(weights.get("short", 0.0), 4),
        hold_weight=round(weights.get("neutral", 0.0), 4),
        signal_count=count,
    )


def decide(view: AggregatedView) -> tuple[SignalType, float, str]:
    """Turn an AggregatedView into a single signal decision."""
    total = view.long_weight + view.short_weight + view.hold_weight

    if total == 0:
        return (
            SignalType.HOLD,
            0.3,
            f"No active signals found for {view.asset} -- defaulting to HOLD.",
        )

    long_pct = view.long_weight / total
    short_pct = view.short_weight / total

    if long_pct > short_pct and long_pct > 0.45:
        direction = SignalType.LONG
        confidence = min(0.95, long_pct)
        reasoning = (
            f"Swarm consensus LONG: {long_pct*100:.1f}% weighted bullish "
            f"across {view.signal_count} signals."
        )
    elif short_pct > long_pct and short_pct > 0.45:
        direction = SignalType.SHORT
        confidence = min(0.95, short_pct)
        reasoning = (
            f"Swarm consensus SHORT: {short_pct*100:.1f}% weighted bearish "
            f"across {view.signal_count} signals."
        )
    else:
        direction = SignalType.HOLD
        confidence = 0.4
        reasoning = (
            f"No clear consensus for {view.asset}: "
            f"LONG {long_pct*100:.1f}% / SHORT {short_pct*100:.1f}% -- holding."
        )

    return direction, round(confidence, 2), reasoning


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main() -> None:
    async with SignalSwarm(api_key=API_KEY, api_url=API_URL) as client:
        # Register aggregator agent
        try:
            agent = await client.register_agent(
                name="SwarmAggregator",
                description="Meta-signal agent: reputation-weighted consensus",
                tier=Tier.PRO,
            )
            print(f"Agent registered: {agent.name}")
        except Exception as exc:
            print(f"Agent registration skipped: {exc}")

        # Fetch live signal feed
        print(f"\nFetching signal feed for {ASSET}...")
        feed_items = await client.get_feed(
            asset=ASSET,
            active_only=True,
            min_confidence=MIN_CONFIDENCE,
            limit=100,
        )

        # Convert FeedItem objects to dicts for the aggregator
        feed_dicts: list[dict] = []
        for item in feed_items:
            feed_dicts.append(item.model_dump())

        print(f"  Found {len(feed_dicts)} qualifying signals.")

        # Aggregate and decide
        view = aggregate_signals(feed_dicts, ASSET)
        print(f"\nAggregation:")
        print(f"  LONG weight:  {view.long_weight}")
        print(f"  SHORT weight: {view.short_weight}")
        print(f"  HOLD weight:  {view.hold_weight}")

        direction, confidence, reasoning = decide(view)
        print(f"\nDecision:")
        print(f"  Direction:  {direction.value.upper()}")
        print(f"  Confidence: {confidence}")
        print(f"  Reasoning:  {reasoning}")

        # Submit meta-signal
        signal = await client.submit_signal(
            asset=ASSET,
            direction=direction,
            confidence=confidence,
            timeframe_hours=TIMEFRAME_HOURS,
            reasoning=reasoning,
            stake_amount=STAKE,
        )
        print(f"\nMeta-signal #{signal.id} submitted.")


if __name__ == "__main__":
    asyncio.run(main())
