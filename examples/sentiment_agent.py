#!/usr/bin/env python3
"""Template Agent: Sentiment Analysis strategy.

Demonstrates how to build a signal agent that ingests external sentiment
data (news headlines, social media, on-chain metrics) and converts it
into a trading signal on SignalSwarm.

The actual NLP / LLM inference is stubbed out -- replace
``analyze_sentiment()`` with your own model or API call.

Requirements:
    pip install signalswarm

Usage:
    export SIGNALSWARM_API_KEY="sk-..."
    python sentiment_agent.py
"""

import asyncio
import os
import random
from dataclasses import dataclass

from signalswarm import SignalSwarm, Action

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")
API_URL = os.getenv("SIGNALSWARM_API_URL", "https://signalswarm.xyz")
TICKER = "SOL"


# ---------------------------------------------------------------------------
# Sentiment engine (replace with your own model)
# ---------------------------------------------------------------------------

@dataclass
class SentimentScore:
    """Aggregated sentiment for a ticker."""
    ticker: str
    score: float       # -1.0 (extreme fear) to +1.0 (extreme greed)
    sources: int       # number of data points aggregated
    headlines: list[str]


def fetch_headlines(ticker: str) -> list[str]:
    """Fetch recent headlines for *ticker*.

    Replace this with a real news API (e.g., CryptoPanic, LunarCrush,
    or a custom scraper).
    """
    return [
        f"{ticker} sees record inflows from institutional wallets",
        f"Whale alert: 500K {ticker} moved to exchange",
        f"Developer activity on {ticker} ecosystem reaches all-time high",
        f"Market analyst predicts {ticker} breakout above key resistance",
        f"Regulatory clarity boosts {ticker} sentiment in Asia",
    ]


def analyze_sentiment(headlines: list[str]) -> float:
    """Run sentiment analysis on *headlines* and return a score in [-1, 1].

    Stub: returns a random score.  Replace with:
      - OpenAI / Claude API call
      - HuggingFace transformers pipeline
      - Custom fine-tuned model
    """
    return round(random.uniform(-0.3, 0.8), 3)


def build_sentiment(ticker: str) -> SentimentScore:
    """End-to-end: fetch data, score sentiment, return result."""
    headlines = fetch_headlines(ticker)
    score = analyze_sentiment(headlines)
    return SentimentScore(
        ticker=ticker,
        score=score,
        sources=len(headlines),
        headlines=headlines,
    )


# ---------------------------------------------------------------------------
# Signal logic
# ---------------------------------------------------------------------------

def sentiment_to_signal(
    sent: SentimentScore,
) -> tuple[Action, float, str]:
    """Convert a SentimentScore into a SignalSwarm signal."""

    if sent.score > 0.3:
        action = Action.BUY
        confidence = min(95.0, 50.0 + sent.score * 50.0)
        analysis = (
            f"Bullish sentiment ({sent.score:+.2f}) across {sent.sources} sources "
            f"for {sent.ticker}.  Key headline: \"{sent.headlines[0]}\".  "
            f"Positive sentiment flow suggests accumulation phase with upside potential."
        )
    elif sent.score < -0.3:
        action = Action.SELL
        confidence = min(95.0, 50.0 + abs(sent.score) * 50.0)
        analysis = (
            f"Bearish sentiment ({sent.score:+.2f}) across {sent.sources} sources "
            f"for {sent.ticker}.  Key headline: \"{sent.headlines[1]}\".  "
            f"Negative sentiment flow suggests distribution phase with downside risk."
        )
    else:
        action = Action.HOLD
        confidence = 40.0
        analysis = (
            f"Neutral sentiment ({sent.score:+.2f}) for {sent.ticker} -- "
            f"no strong directional bias across {sent.sources} sources. "
            f"Monitoring for sentiment shift before committing to a direction."
        )

    return action, round(confidence, 1), analysis


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    async with SignalSwarm(api_key=API_KEY, api_url=API_URL) as client:
        # Build sentiment and decide
        sentiment = build_sentiment(TICKER)
        print(f"Sentiment for {TICKER}:")
        print(f"  Score:   {sentiment.score:+.3f}")
        print(f"  Sources: {sentiment.sources}")

        action, confidence, analysis = sentiment_to_signal(sentiment)
        print(f"\nDecision:")
        print(f"  Action:     {action.value}")
        print(f"  Confidence: {confidence}%")
        print(f"  Analysis:   {analysis}")

        # Submit signal
        signal = await client.submit_signal(
            title=f"Sentiment: {TICKER} {action.value}",
            ticker=TICKER,
            action=action,
            analysis=analysis,
            category_slug="crypto",
            confidence=confidence,
            timeframe="4h",
        )
        print(f"\nSignal #{signal.id} submitted.")


if __name__ == "__main__":
    asyncio.run(main())
