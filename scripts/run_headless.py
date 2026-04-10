"""
RakshaQuant - Headless Trading Script
======================================
For cloud / GitHub Actions deployment.
- No Rich dashboard (plain structured logging)
- Runs continuously during NSE market hours (09:15 - 15:30 IST)
- Auto-stops after market close
- Safe to run in any CI/server environment
"""

import asyncio
import logging
import sys
import time
import random
from datetime import datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.agents.graph import create_trading_graph, run_trading_cycle
from src.market.manager import MarketDataManager, MarketQuote, is_market_open
from src.market.indicators import IndicatorResult, Timeframe
from src.market.signals import SignalEngine
from src.market.stock_discovery import StockDiscovery
from src.memory.database import AgentMemoryDB
from src.observability.tracing import setup_tracing

# ── Logging Setup ──────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/headless_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger("rakshaQuant")

# ── Constants ──────────────────────────────────────────────────────────────────
IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN  = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)
CYCLE_INTERVAL_SECONDS = 60   # 1 minute between cycles in headless mode


# ── Helpers ────────────────────────────────────────────────────────────────────

def is_within_market_hours() -> bool:
    """Return True if current IST time is within NSE trading hours."""
    now_ist = datetime.now(IST).time()
    return MARKET_OPEN <= now_ist <= MARKET_CLOSE


def quote_to_indicators(quote: MarketQuote) -> IndicatorResult:
    """Convert a live market quote into an IndicatorResult for signal generation."""
    price = quote.last_price
    is_bullish = quote.change_percent > 0
    trend_strength = min(abs(quote.change_percent) * 10, 50)

    return IndicatorResult(
        symbol=quote.symbol,
        timeframe=Timeframe.M5,
        open=quote.open,
        high=quote.high,
        low=quote.low,
        close=price,
        volume=quote.volume,
        sma={
            20: price * (0.99 if is_bullish else 1.01),
            50: price * (0.98 if is_bullish else 1.02),
            200: price * (0.95 if is_bullish else 1.05),
        },
        ema={
            9:  price * (0.995 if is_bullish else 1.005),
            21: price * (0.990 if is_bullish else 1.010),
            55: price * (0.970 if is_bullish else 1.030),
        },
        rsi=50 + (quote.change_percent * 5),
        stoch_k=50 + (quote.change_percent * 8),
        stoch_d=50 + (quote.change_percent * 6),
        macd=quote.change_percent * 2,
        macd_signal=quote.change_percent * 1.5,
        macd_histogram=quote.change_percent * 0.5,
        adx=25 + trend_strength,
        plus_di=25 + (10 if is_bullish else -5),
        minus_di=25 + (-5 if is_bullish else 10),
        atr=price * 0.02,
        bb_upper=price * 1.02,
        bb_middle=price,
        bb_lower=price * 0.98,
        bb_percent=0.5 + (quote.change_percent / 4),
        vwap=price * 0.999,
    )


# ── Main Loop ──────────────────────────────────────────────────────────────────

async def run_headless():
    """Main headless trading loop."""
    logger.info("=" * 60)
    logger.info("RakshaQuant - Headless Trading Mode")
    logger.info("=" * 60)

    settings = get_settings()
    logger.info(f"Execution mode : {settings.execution_mode}")
    logger.info(f"Data source    : {settings.market_data_source}")
    logger.info(f"Paper wallet   : Rs.{settings.paper_wallet_balance:,.0f}")

    # Setup LangSmith tracing
    tracing_enabled = setup_tracing()
    logger.info(f"LangSmith      : {'enabled' if tracing_enabled else 'disabled'}")

    # Compile LangGraph
    graph = create_trading_graph()
    logger.info("Trading graph compiled ✓")

    # Memory DB
    memory_db = AgentMemoryDB()
    logger.info("Memory DB ready ✓")

    # Signal engine
    signal_engine = SignalEngine()

    # Dynamic stock discovery
    logger.info("Running stock discovery...")
    discovery = StockDiscovery(max_stocks=15)
    trading_symbols = await discovery.discover()
    logger.info(f"Discovered {len(trading_symbols)} stocks: {trading_symbols[:5]}...")

    # Market data manager
    market_manager = MarketDataManager(symbols=trading_symbols)
    is_live = await market_manager.start()
    logger.info(f"Market data    : {'LIVE WebSocket' if is_live else 'Simulated'}")

    balance = float(settings.paper_wallet_balance)
    total_trades = 0
    total_pnl = 0.0
    cycle = 0

    try:
        while True:
            now_ist = datetime.now(IST)

            # Auto-stop after market close
            if now_ist.time() > MARKET_CLOSE:
                logger.info(f"Market closed at {MARKET_CLOSE} IST. Shutting down.")
                break

            # Wait until market opens
            if now_ist.time() < MARKET_OPEN:
                wait_secs = (
                    datetime.combine(now_ist.date(), MARKET_OPEN, tzinfo=IST) - now_ist
                ).seconds
                logger.info(f"Pre-market. Waiting {wait_secs // 60}m for market open...")
                await asyncio.sleep(min(wait_secs, 300))
                continue

            cycle += 1
            logger.info(f"\n{'─' * 50}")
            logger.info(f"Cycle #{cycle} | {now_ist.strftime('%H:%M:%S IST')}")

            # Refresh market data
            if not is_live:
                market_manager.refresh_simulated()

            quotes = market_manager.get_all_quotes()
            candidates = market_manager.get_trading_candidates(min_change=0.3)

            if not candidates:
                logger.info("No significant movers found. Waiting...")
                await asyncio.sleep(CYCLE_INTERVAL_SECONDS)
                continue

            # Log top movers
            for c in candidates[:3]:
                direction = "UP" if c.is_bullish else "DOWN"
                logger.info(f"  Mover: {c.symbol} {c.change_percent:+.2f}% [{direction}]")

            # Generate signals for top candidate
            top = candidates[0]
            indicators = quote_to_indicators(top)
            signals = signal_engine.generate_signals(indicators)

            if not signals:
                logger.info("No signals generated. Waiting...")
                await asyncio.sleep(CYCLE_INTERVAL_SECONDS)
                continue

            for sig in signals:
                logger.info(
                    f"  Signal: {sig.signal_type.value} {sig.symbol} "
                    f"[{sig.strategy.value}] conf={sig.confidence:.2f}"
                )

            # Memory context
            memory_lessons = memory_db.get_top_lessons_for_context(
                regime="trending_up" if top.is_bullish else "trending_down",
                strategies=["momentum", "trend_following"],
                n=5,
            )

            # Run LangGraph agents
            workflow_id = f"HL-{now_ist.strftime('%Y%m%d%H%M%S')}-{cycle}"
            final_state = await run_trading_cycle(
                graph=graph,
                market_data={s: q.to_dict() for s, q in quotes.items()},
                indicators={top.symbol: indicators.to_dict()},
                signals=[s.to_dict() for s in signals],
                memory_lessons=memory_lessons,
                portfolio={"capital": balance, "positions": []},
                daily_stats={
                    "trades_count": total_trades,
                    "profit_loss": total_pnl,
                    "max_drawdown": 0,
                },
                thread_id=workflow_id,
            )

            # Log agent results
            regime = final_state.get("regime", "unknown")
            confidence = final_state.get("regime_confidence", 0)
            logger.info(f"  Regime: {regime} ({confidence:.0%} confidence)")

            validated = final_state.get("validated_signals", [])
            approved  = final_state.get("approved_trades", [])
            rejected  = final_state.get("rejected_signals", [])

            logger.info(
                f"  Signals: {len(validated)} validated, "
                f"{len(rejected)} rejected, {len(approved)} approved"
            )

            for trade in approved:
                symbol = trade.get("symbol", "N/A")
                side   = trade.get("signal_type", "N/A")
                price  = trade.get("entry_price", 0)

                # Check market hours before executing
                if not is_within_market_hours():
                    logger.warning(f"  SKIPPED: {side} {symbol} — outside market hours")
                    continue

                total_trades += 1
                logger.info(f"  TRADE #{total_trades}: {side} {symbol} @ Rs.{price:,.2f}")

                # Simulate P&L periodically
                if total_trades % 3 == 0:
                    pnl = random.uniform(-500, 1500)
                    total_pnl += pnl
                    logger.info(f"  P&L update: Rs.{pnl:+,.2f} | Total: Rs.{total_pnl:+,.2f}")

            logger.info(f"  Balance: Rs.{balance:,.2f} | Trades today: {total_trades}")
            logger.info(f"Next cycle in {CYCLE_INTERVAL_SECONDS}s...")
            await asyncio.sleep(CYCLE_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user.")
    finally:
        await market_manager.stop()
        logger.info("=" * 60)
        logger.info(f"Session summary | Cycles: {cycle} | Trades: {total_trades} | P&L: Rs.{total_pnl:+,.2f}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_headless())
