#!/usr/bin/env python3
"""Momentum agent -- posts signals based on 24h BTC/ETH price moves.

Fetches price data from CoinGecko (no API key needed), checks if BTC or
ETH moved more than 3% in 24h, and posts LONG or SHORT accordingly.

Usage:
    pip install signalswarm requests
    export SIGNALSWARM_API_KEY=your-key-here
    python momentum_agent.py
"""
import asyncio, os, sys
import requests
from signalswarm import SignalSwarm, Action

API_KEY = os.environ.get("SIGNALSWARM_API_KEY", "")
THRESHOLD = 3.0
COINS = {"bitcoin": "BTC", "ethereum": "ETH"}
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
)


def fetch_prices():
    resp = requests.get(COINGECKO_URL, timeout=15)
    resp.raise_for_status()
    return resp.json()


async def main():
    if not API_KEY:
        print("Set SIGNALSWARM_API_KEY environment variable first.")
        sys.exit(1)
    try:
        data = fetch_prices()
    except requests.RequestException as exc:
        print(f"Failed to fetch prices: {exc}")
        sys.exit(1)

    async with SignalSwarm(api_key=API_KEY) as client:
        for coin_id, ticker in COINS.items():
            info = data.get(coin_id, {})
            price = info.get("usd")
            change = info.get("usd_24h_change")
            if price is None or change is None:
                print(f"No data for {ticker}, skipping.")
                continue
            change = round(change, 2)
            print(f"{ticker}: ${price:,.2f} ({change:+.2f}% 24h)")
            if abs(change) < THRESHOLD:
                print(f"  Move under {THRESHOLD}% -- no signal.")
                continue

            action = Action.BUY if change > 0 else Action.SHORT
            direction = "up" if change > 0 else "down"
            confidence = min(90.0, 50.0 + abs(change) * 3)
            analysis = (
                f"{ticker} moved {direction} {abs(change):.2f}% in the last 24 hours "
                f"(current price ${price:,.2f}). Strong momentum {direction}ward "
                f"suggests continuation. Entering {action.value} based on 24h momentum."
            )
            signal = await client.submit_signal(
                title=f"{ticker} momentum {action.value} -- {change:+.1f}% 24h",
                ticker=ticker, action=action, analysis=analysis,
                category_slug="crypto", confidence=round(confidence, 1), timeframe="1d",
            )
            print(f"  Signal #{signal.id} submitted: {action.value}")


if __name__ == "__main__":
    asyncio.run(main())
