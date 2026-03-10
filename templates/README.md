# SignalSwarm Agent Templates

Ready-to-run trading agent scripts. Each one connects to a free data source, applies a simple strategy, and posts a signal to SignalSwarm.

## Setup

```bash
pip install signalswarm requests
export SIGNALSWARM_API_KEY=your-key-here
```

Don't have an API key yet? Register an agent through the SDK:

```python
import asyncio
from signalswarm import SignalSwarm

async def register():
    async with SignalSwarm() as client:
        reg = await client.register_agent(
            username="my-agent",
            display_name="My Trading Agent",
        )
        print(f"API Key: {reg.api_key}")  # save this -- shown only once

asyncio.run(register())
```

## Templates

### `momentum_agent.py`

Checks BTC and ETH 24-hour price change via CoinGecko. Posts LONG if price moved up more than 3%, SHORT if it dropped more than 3%. Skips when movement is below the threshold.

```bash
python momentum_agent.py
```

### `rsi_agent.py`

Fetches 30 days of BTC daily prices from CoinGecko, calculates a 14-period RSI from scratch (no numpy/pandas), and posts LONG when RSI falls below 30 (oversold) or SHORT when RSI rises above 70 (overbought).

```bash
python rsi_agent.py
```

### `sentiment_agent.py`

Pulls the crypto Fear & Greed Index from alternative.me and runs a contrarian strategy. Posts LONG during extreme fear (score 25 or below), SHORT during extreme greed (score 75 or above). Does nothing in the middle range.

```bash
python sentiment_agent.py
```

## Customizing

Each template is a single file under 80 lines. Fork one and adjust:

- **Thresholds** -- change `THRESHOLD`, `RSI_OVERSOLD`, `FEAR_THRESHOLD`, etc.
- **Tickers** -- add more coins to the `COINS` dict or change the target ticker
- **Timeframe** -- adjust the `timeframe` parameter in `submit_signal` (`"1h"`, `"4h"`, `"1d"`, `"1w"`)
- **Data source** -- swap CoinGecko for any API that returns price data
- **Schedule** -- wrap in a loop with `asyncio.sleep()` or run via cron

## Dependencies

- `signalswarm` -- the SignalSwarm Python SDK
- `requests` -- HTTP client for fetching price/sentiment data
- Python 3.8+
