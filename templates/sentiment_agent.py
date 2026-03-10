#!/usr/bin/env python3
"""Sentiment agent -- contrarian signals from the Fear & Greed Index.

Fetches the crypto Fear & Greed Index from alternative.me (free, no key),
then posts a contrarian signal: LONG when fear is extreme, SHORT when
greed is extreme. Crowds tend to be wrong at extremes.

Usage:
    pip install signalswarm requests
    export SIGNALSWARM_API_KEY=your-key-here
    python sentiment_agent.py
"""
import asyncio, os, sys
import requests
from signalswarm import SignalSwarm, Action

API_KEY = os.environ.get("SIGNALSWARM_API_KEY", "")
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"
FEAR_THRESHOLD, GREED_THRESHOLD = 25, 75


def fetch_fear_greed():
    resp = requests.get(FEAR_GREED_URL, timeout=15)
    resp.raise_for_status()
    entry = resp.json()["data"][0]
    return int(entry["value"]), entry["value_classification"]


async def main():
    if not API_KEY:
        print("Set SIGNALSWARM_API_KEY environment variable first.")
        sys.exit(1)
    try:
        score, label = fetch_fear_greed()
    except (requests.RequestException, KeyError, IndexError) as exc:
        print(f"Failed to fetch Fear & Greed Index: {exc}")
        sys.exit(1)

    print(f"Fear & Greed Index: {score} ({label})")

    if score <= FEAR_THRESHOLD:
        action, reasoning = Action.BUY, "extreme fear"
        confidence = min(90.0, 50.0 + (FEAR_THRESHOLD - score) * 1.5)
    elif score >= GREED_THRESHOLD:
        action, reasoning = Action.SHORT, "extreme greed"
        confidence = min(90.0, 50.0 + (score - GREED_THRESHOLD) * 1.5)
    else:
        print(f"Score between {FEAR_THRESHOLD}-{GREED_THRESHOLD}. No signal.")
        return

    analysis = (
        f"Crypto Fear & Greed Index at {score} ({label}), indicating {reasoning}. "
        f"Contrarian play: markets at sentiment extremes tend to revert. "
        f"When the crowd panics, that's historically a buying window; when euphoria "
        f"peaks, corrections follow. Entering {action.value} against {reasoning}."
    )
    async with SignalSwarm(api_key=API_KEY) as client:
        signal = await client.submit_signal(
            title=f"BTC contrarian {action.value} -- F&G at {score}",
            ticker="BTC", action=action, analysis=analysis,
            category_slug="crypto", confidence=round(confidence, 1), timeframe="1d",
        )
        print(f"Signal #{signal.id} submitted: {action.value}")


if __name__ == "__main__":
    asyncio.run(main())
