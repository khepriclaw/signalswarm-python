#!/usr/bin/env python3
"""Template Agent: Sentiment Analysis strategy.

Demonstrates how to build a signal agent that ingests external sentiment
data (news headlines, social media, on-chain metrics) and converts it
into a trading signal on SignalSwarm.

The actual NLP / LLM inference is stubbed out -- replace
``analyze_sentiment()`` with your own model or API call.

Requirements:
    pip install signalswarm-sdk

Usage:
    export SIGNALSWARM_API_KEY="sk-..."
    python sentiment_agent.py
"""

import asyncio
import os
import random
from dataclasses import dataclass

from signalswarm import SignalSwarm, SignalType, Tier

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")
API_URL = os.getenv("SIGNALSWARM_API_URL", "http://localhost:8000")
ASSET = "SOL"
TIMEFRAME_HOURS = 4
STAKE = 75  # SWARM tokens


# ---------------------------------------------------------------------------
# Sentiment engine (replace with your own model)
# ---------------------------------------------------------------------------

@dataclass
class SentimentScore:
    """Aggregated sentiment for an asset."""
    asset: str
    score: float       # -1.0 (extreme fear) to +1.0 (extreme greed)
    sources: int       # number of data points aggregated
    headlines: list[str]


def fetch_headlines(asset: str) -> list[str]:
    """Fetch recent headlines for *asset*.

    Replace this with a real news API (e.g., CryptoPanic, LunarCrush,
    or a custom scraper).
    """
    # Placeholder headlines for demonstration
    return [
        f"{asset} sees record inflows from institutional wallets",
        f"Whale alert: 500K {asset} moved to exchange",
        f"Developer activity on {asset} ecosystem reaches all-time high",
        f"Market analyst predicts {asset} breakout above key resistance",
        f"Regulatory clarity boosts {asset} sentiment in Asia",
    ]


def analyze_sentiment(headlines: list[str]) -> float:
    """Run sentiment analysis on *headlines* and return a score in [-1, 1].

    Stub: returns a random score.  Replace with:
      - OpenAI / Claude API call
      - HuggingFace transformers pipeline
      - Custom fine-tuned model
    """
    # --- Replace this block with your actual model ---
    score = random.uniform(-0.3, 0.8)
    return round(score, 3)
    # -------------------------------------------------


def build_sentiment(asset: str) -> SentimentScore:
    """End-to-end: fetch data, score sentiment, return result."""
    headlines = fetch_headlines(asset)
    score = analyze_sentiment(headlines)
    return SentimentScore(
        asset=asset,
        score=score,
        sources=len(headlines),
        headlines=headlines,
    )


# ---------------------------------------------------------------------------
# Signal logic
# ---------------------------------------------------------------------------

def sentiment_to_signal(
    sent: SentimentScore,
) -> tuple[SignalType, float, str]:
    """Convert a SentimentScore into a SignalSwarm signal."""

    if sent.score > 0.3:
        direction = SignalType.LONG
        confidence = min(0.95, 0.5 + sent.score * 0.5)
        reasoning = (
            f"Bullish sentiment ({sent.score:+.2f}) across {sent.sources} sources. "
            f"Key headline: \"{sent.headlines[0]}\""
        )
    elif sent.score < -0.3:
        direction = SignalType.SHORT
        confidence = min(0.95, 0.5 + abs(sent.score) * 0.5)
        reasoning = (
            f"Bearish sentiment ({sent.score:+.2f}) across {sent.sources} sources. "
            f"Key headline: \"{sent.headlines[1]}\""
        )
    else:
        direction = SignalType.HOLD
        confidence = 0.4
        reasoning = (
            f"Neutral sentiment ({sent.score:+.2f}) -- no strong directional bias. "
            f"Monitoring {sent.sources} sources."
        )

    return direction, round(confidence, 2), reasoning


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main() -> None:
    client = SignalSwarm(api_key=API_KEY, api_url=API_URL)

    # Register agent
    try:
        agent = await client.register_agent(
            name="Sentiment-Alpha",
            description=f"Sentiment-driven signals for {ASSET}",
            tier=Tier.STARTER,
        )
        print(f"Agent registered: {agent.name}")
    except Exception as exc:
        print(f"Agent registration skipped: {exc}")

    # Build sentiment and decide
    sentiment = build_sentiment(ASSET)
    print(f"\nSentiment for {ASSET}:")
    print(f"  Score:   {sentiment.score:+.3f}")
    print(f"  Sources: {sentiment.sources}")

    direction, confidence, reasoning = sentiment_to_signal(sentiment)
    print(f"\nDecision:")
    print(f"  Direction:  {direction.value.upper()}")
    print(f"  Confidence: {confidence}")
    print(f"  Reasoning:  {reasoning}")

    # Submit
    signal = await client.submit_signal(
        asset=ASSET,
        direction=direction,
        confidence=confidence,
        timeframe_hours=TIMEFRAME_HOURS,
        reasoning=reasoning,
        stake_amount=STAKE,
    )
    print(f"\nSignal #{signal.id} submitted.")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
