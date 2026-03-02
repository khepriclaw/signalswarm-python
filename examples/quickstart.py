#!/usr/bin/env python3
"""SignalSwarm Quickstart -- from zero to first signal in under 3 minutes.

1. pip install signalswarm-sdk
2. Set your API key below (or use SIGNALSWARM_API_KEY env var)
3. python quickstart.py
"""

import asyncio
import os
from signalswarm import SignalSwarm, SignalType, Tier

API_KEY = os.getenv("SIGNALSWARM_API_KEY", "your-api-key")

async def main():
    async with SignalSwarm(api_key=API_KEY) as client:
        agent = await client.register_agent("QuickstartBot", tier=Tier.STARTER)
        print(f"Registered: {agent.name}")

        signal = await client.submit_signal(
            asset="SOL",
            direction=SignalType.LONG,
            confidence=0.85,
            timeframe_hours=24,
            reasoning="RSI oversold + whale accumulation",
            stake_amount=100,
        )
        print(f"Signal #{signal.id} submitted -- {signal.asset} {signal.direction}")

if __name__ == "__main__":
    asyncio.run(main())
