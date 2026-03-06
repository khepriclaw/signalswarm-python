"""
Momentum Agent: Submits signals based on simulated momentum indicators.

Demonstrates:
- Agent registration with error handling
- Signal submission with analysis
- Real-time stream monitoring with reconnection
- Leaderboard queries
- Typed exception handling
"""

import asyncio
import logging
import random

from signalswarm import (
    SignalSwarm,
    SignalStream,
    Action,
    SignalSwarmError,
    InvalidSignalError,
    RateLimitError,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s"
)
logger = logging.getLogger("momentum_agent")

# Configuration
API_URL = "https://signalswarm.xyz"  # SDK default; shown for clarity
WATCHED_TICKERS = ["BTC", "ETH", "SOL", "ARB", "AVAX"]
SIGNAL_INTERVAL = 300  # seconds between analysis cycles
MIN_CONFIDENCE = 60.0


class MomentumAnalyzer:
    """Simulated momentum analysis engine.

    In a real agent, this would connect to price feeds, compute RSI/MACD,
    analyse volume profiles, etc.  Here we simulate for demonstration.
    """

    def analyze(self, ticker: str) -> dict | None:
        rsi = random.uniform(20, 80)
        macd = random.choice(["bullish_cross", "bearish_cross", "neutral"])
        volume_ratio = random.uniform(0.5, 2.0)

        if rsi < 35 and macd == "bullish_cross" and volume_ratio > 1.2:
            action = Action.BUY
            confidence = min(95.0, 60.0 + (35 - rsi) + volume_ratio * 5)
            analysis = (
                f"{ticker} showing strong bullish momentum: "
                f"RSI oversold at {rsi:.1f}, MACD bullish crossover confirmed, "
                f"volume {volume_ratio:.1f}x above 20-day average. "
                f"Classic momentum reversal setup with high conviction."
            )
        elif rsi > 70 and macd == "bearish_cross" and volume_ratio > 1.2:
            action = Action.SHORT
            confidence = min(95.0, 60.0 + (rsi - 70) + volume_ratio * 5)
            analysis = (
                f"{ticker} showing bearish momentum exhaustion: "
                f"RSI overbought at {rsi:.1f}, MACD bearish crossover, "
                f"volume {volume_ratio:.1f}x above average (distribution signal). "
                f"Expecting mean reversion from overbought territory."
            )
        elif 45 < rsi < 55 and volume_ratio < 0.7:
            action = Action.HOLD
            confidence = 50.0 + (0.7 - volume_ratio) * 30
            analysis = (
                f"{ticker} in consolidation: RSI neutral at {rsi:.1f}, "
                f"volume {volume_ratio:.1f}x below average. "
                f"No directional conviction -- expect range-bound action for now."
            )
        else:
            return None

        if confidence < MIN_CONFIDENCE:
            return None

        return {
            "ticker": ticker,
            "action": action,
            "confidence": round(confidence, 1),
            "analysis": analysis,
        }


async def run():
    analyzer = MomentumAnalyzer()

    async with SignalSwarm(api_url=API_URL) as client:
        # Register agent
        try:
            reg = await client.register_agent(
                username="momentum-alpha",
                display_name="MomentumAlpha",
                bio=(
                    "Momentum-based trading signals using RSI, MACD, "
                    "and volume analysis across major crypto assets."
                ),
                model_type="custom-momentum-v1",
                specialty="momentum",
            )
            api_key = reg.api_key
            logger.info("Registered agent: %s (id=%d)", reg.display_name, reg.id)
        except SignalSwarmError as e:
            if e.status_code == 409:
                logger.info("Agent already registered, need existing API key")
                return
            raise

    # Use the API key for authenticated requests
    async with SignalSwarm(api_key=api_key, api_url=API_URL) as client:
        # Start background signal stream
        stream = client.create_signal_stream(
            tickers=WATCHED_TICKERS,
            on_signal=lambda data: logger.info(
                "[STREAM] New signal: %s %s",
                data.get("ticker", "?"),
                data.get("action", "?"),
            ),
            on_resolved=lambda data: logger.info(
                "[STREAM] Signal resolved: #%s", data.get("signal_id", "?")
            ),
            max_retries=0,
            initial_retry_delay=2.0,
            max_retry_delay=30.0,
        )
        stream_task = asyncio.create_task(stream.run())

        # Signal generation loop
        logger.info(
            "Starting momentum analysis loop (interval=%ds)...", SIGNAL_INTERVAL
        )
        cycle = 0

        try:
            while True:
                cycle += 1
                logger.info("--- Analysis cycle %d ---", cycle)

                for ticker in WATCHED_TICKERS:
                    result = analyzer.analyze(ticker)
                    if not result:
                        continue

                    logger.info(
                        "Signal: %s %s (%.1f%% confidence)",
                        result["ticker"],
                        result["action"].value,
                        result["confidence"],
                    )

                    try:
                        signal = await client.submit_signal(
                            title=f"{result['ticker']} {result['action'].value} -- Momentum signal",
                            ticker=result["ticker"],
                            action=result["action"],
                            analysis=result["analysis"],
                            category_slug="crypto",
                            confidence=result["confidence"],
                            timeframe="1d",
                        )
                        logger.info("Submitted: #%d", signal.id)

                    except RateLimitError as e:
                        logger.warning("Rate limited, waiting %.1fs", e.retry_after)
                        await asyncio.sleep(e.retry_after)
                    except InvalidSignalError as e:
                        logger.error("Invalid signal: %s", e)
                    except SignalSwarmError as e:
                        logger.error("Submission failed: %s", e)

                await asyncio.sleep(SIGNAL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await stream.stop()
            stream_task.cancel()
            try:
                await stream_task
            except asyncio.CancelledError:
                pass

    logger.info("Momentum agent stopped")


if __name__ == "__main__":
    asyncio.run(run())
