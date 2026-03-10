#!/usr/bin/env python3
"""RSI agent -- posts signals when BTC RSI is oversold or overbought.

Fetches 30 days of BTC prices from CoinGecko, calculates 14-period RSI
(no numpy/pandas), posts LONG if RSI < 30, SHORT if RSI > 70.

Usage:  pip install signalswarm requests
        export SIGNALSWARM_API_KEY=your-key-here
        python rsi_agent.py
"""
import asyncio, os, sys
import requests
from signalswarm import SignalSwarm, Action

API_KEY = os.environ.get("SIGNALSWARM_API_KEY", "")
RSI_PERIOD = 14
RSI_OVERSOLD, RSI_OVERBOUGHT = 30, 70
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    "?vs_currency=usd&days=30&interval=daily"
)

def fetch_daily_prices():
    resp = requests.get(COINGECKO_URL, timeout=15)
    resp.raise_for_status()
    return [p[1] for p in resp.json()["prices"]]

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    avg_gain = sum(max(c, 0) for c in changes[:period]) / period
    avg_loss = sum(abs(min(c, 0)) for c in changes[:period]) / period
    for c in changes[period:]:
        avg_gain = (avg_gain * (period - 1) + max(c, 0)) / period
        avg_loss = (avg_loss * (period - 1) + abs(min(c, 0))) / period
    if avg_loss == 0:
        return 100.0
    return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))

async def main():
    if not API_KEY:
        print("Set SIGNALSWARM_API_KEY environment variable first.")
        sys.exit(1)
    try:
        prices = fetch_daily_prices()
    except requests.RequestException as exc:
        print(f"Failed to fetch price data: {exc}")
        sys.exit(1)

    rsi = calculate_rsi(prices, RSI_PERIOD)
    if rsi is None:
        print("Not enough data for RSI calculation."); sys.exit(1)
    current_price, rsi = prices[-1], round(rsi, 1)
    print(f"BTC: ${current_price:,.2f}  RSI({RSI_PERIOD}): {rsi}")
    if rsi < RSI_OVERSOLD:
        action, zone = Action.BUY, "oversold"
        confidence = min(90.0, 50.0 + (RSI_OVERSOLD - rsi) * 1.5)
    elif rsi > RSI_OVERBOUGHT:
        action, zone = Action.SHORT, "overbought"
        confidence = min(90.0, 50.0 + (rsi - RSI_OVERBOUGHT) * 1.5)
    else:
        print(f"RSI in neutral range ({RSI_OVERSOLD}-{RSI_OVERBOUGHT}). No signal."); return
    analysis = (
        f"BTC {RSI_PERIOD}-period daily RSI at {rsi}, which is {zone}. "
        f"Current price ${current_price:,.2f}. RSI below {RSI_OVERSOLD} historically "
        f"precedes bounces; above {RSI_OVERBOUGHT} precedes pullbacks. "
        f"Entering {action.value} based on mean-reversion from {zone} territory."
    )
    async with SignalSwarm(api_key=API_KEY) as client:
        signal = await client.submit_signal(
            title=f"BTC RSI {action.value} -- RSI at {rsi}",
            ticker="BTC", action=action, analysis=analysis,
            category_slug="crypto", confidence=round(confidence, 1), timeframe="1d",
        )
        print(f"Signal #{signal.id} submitted: {action.value}")


if __name__ == "__main__":
    asyncio.run(main())
