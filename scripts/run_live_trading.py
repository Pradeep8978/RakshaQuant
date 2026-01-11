"""
RakshaQuant Live Trading Dashboard

Runs the agentic trading system with:
- Real-time WebSocket data during market hours
- Simulated data after hours
- Multi-stock analysis (20 NSE stocks)
- Live CLI dashboard
"""

import asyncio
import sys
import time
import random
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.live import Live

from src.config import get_settings
from src.agents.graph import create_trading_graph, run_trading_cycle
from src.market.manager import MarketDataManager, MarketQuote, is_market_open
from src.market.indicators import IndicatorResult, Timeframe
from src.market.signals import SignalEngine
from src.market.stock_discovery import StockDiscovery
from src.memory.database import AgentMemoryDB
from src.observability.tracing import setup_tracing
from src.dashboard.cli import TradingDashboard, create_dashboard_layout

console = Console()


def quote_to_indicators(quote: MarketQuote) -> IndicatorResult:
    """Convert market quote to indicator result for signal generation."""
    
    # Generate synthetic indicators from price data
    price = quote.last_price
    
    # Trend indicators based on price movement
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
        # Moving averages - synthetic based on current price
        sma={
            20: price * (0.99 if is_bullish else 1.01),
            50: price * (0.98 if is_bullish else 1.02),
            200: price * (0.95 if is_bullish else 1.05),
        },
        ema={
            9: price * (0.995 if is_bullish else 1.005),
            21: price * (0.99 if is_bullish else 1.01),
            55: price * (0.97 if is_bullish else 1.03),
        },
        # Momentum - based on change percent
        rsi=50 + (quote.change_percent * 5),  # Bullish = higher RSI
        stoch_k=50 + (quote.change_percent * 8),
        stoch_d=50 + (quote.change_percent * 6),
        # MACD
        macd=quote.change_percent * 2,
        macd_signal=quote.change_percent * 1.5,
        macd_histogram=quote.change_percent * 0.5,
        # Trend
        adx=25 + trend_strength,
        plus_di=25 + (10 if is_bullish else -5),
        minus_di=25 + (-5 if is_bullish else 10),
        # Volatility
        atr=price * 0.02,
        bb_upper=price * 1.02,
        bb_middle=price,
        bb_lower=price * 0.98,
        bb_percent=0.5 + (quote.change_percent / 4),
        vwap=price * 0.999,
    )


async def run_live_trading():
    """Run trading with live/simulated market data."""
    
    settings = get_settings()
    
    # Initialize dashboard
    data_source = "live" if is_market_open() else "simulated"
    dashboard = TradingDashboard()
    dashboard.start(balance=1000000.0, mode=settings.trading_mode, data_source=data_source)
    
    # Setup tracing
    tracing_enabled = setup_tracing()
    dashboard.stats.log_activity(
        f"LangSmith: {'enabled' if tracing_enabled else 'disabled'}", 
        "INFO"
    )
    
    # Create trading graph
    graph = create_trading_graph()
    dashboard.stats.log_activity("Trading graph compiled", "SUCCESS")
    
    # Initialize memory
    memory_db = AgentMemoryDB()
    dashboard.stats.log_activity("Memory database ready", "INFO")
    
    # Signal engine
    signal_engine = SignalEngine()
    
    # Market data
    market_mode = "LIVE" if is_market_open() else "SIMULATED"
    dashboard.stats.log_activity(f"Market mode: {market_mode}", "INFO")
    
    # Dynamic Stock Discovery (NEW - Free Tier)
    # Discovers stocks from news mentions and market movers
    dashboard.stats.log_activity("Running dynamic stock discovery...", "INFO")
    discovery = StockDiscovery(max_stocks=15)
    trading_symbols = await discovery.discover()
    
    # Log discovered stocks
    report = discovery.get_discovery_report()
    for item in report[:5]:  # Top 5
        dashboard.stats.log_activity(
            f"Discovered: {item['symbol']} ({item['source']}: {item['reason'][:30]}...)",
            "INFO"
        )
    
    market_manager = MarketDataManager(symbols=trading_symbols)
    
    console.print("\n[bold green]RakshaQuant Live Trading System Starting...[/]")
    console.print(f"[dim]Mode: {market_mode} | Discovered Stocks: {len(trading_symbols)} | Press Ctrl+C to stop[/]\n")
    time.sleep(1)
    
    # Start market data
    is_live = await market_manager.start()
    data_source = "WebSocket LIVE" if is_live else "Simulated"
    dashboard.stats.log_activity(f"Data source: {data_source}", "SUCCESS")
    
    with Live(create_dashboard_layout(dashboard.stats), console=console, refresh_per_second=4) as live:
        
        try:
            cycle = 0
            
            while True:
                cycle += 1
                dashboard.stats.log_activity(f"=== Trading Cycle #{cycle} ===", "INFO")
                live.update(create_dashboard_layout(dashboard.stats))
                
                # Refresh market data
                if not is_live:
                    market_manager.refresh_simulated()
                
                quotes = market_manager.get_all_quotes()
                
                # Update dashboard with market data
                dashboard.update_market_data({s: q.to_dict() for s, q in quotes.items()})
                
                # Find trading candidates (significant movers)
                candidates = market_manager.get_trading_candidates(min_change=0.3)
                
                if not candidates:
                    dashboard.stats.log_activity("No trading candidates found", "INFO")
                    live.update(create_dashboard_layout(dashboard.stats))
                    
                    # Wait and retry
                    for _ in range(15):
                        time.sleep(1)
                        live.update(create_dashboard_layout(dashboard.stats))
                    continue
                
                # Log top movers
                for c in candidates[:3]:
                    direction = "UP" if c.is_bullish else "DOWN"
                    dashboard.stats.log_activity(
                        f"Mover: {c.symbol} {c.change_percent:+.2f}% [{direction}]",
                        "INFO"
                    )
                
                live.update(create_dashboard_layout(dashboard.stats))
                
                # Generate signals for top candidate
                top_candidate = candidates[0]
                indicators = quote_to_indicators(top_candidate)
                signals = signal_engine.generate_signals(indicators)
                
                # Set current signal info for dashboard
                if signals:
                    sig = signals[0]
                    dashboard.set_current_signal(
                        sig.signal_type.value,
                        sig.symbol,
                        sig.strategy.value,
                        sig.confidence,
                    )
                    
                    # Generate decision reason
                    direction = "bullish" if top_candidate.is_bullish else "bearish"
                    reason = f"{direction.title()} momentum ({top_candidate.change_percent:+.2f}%) with {sig.strategy.value} strategy"
                    dashboard.set_decision_reason(reason)
                
                dashboard.stats.signals_generated += len(signals)
                
                for signal in signals:
                    dashboard.stats.log_activity(
                        f"Signal: {signal.signal_type.value} {signal.symbol} [{signal.strategy.value}]",
                        "INFO"
                    )
                
                live.update(create_dashboard_layout(dashboard.stats))
                
                if not signals:
                    dashboard.stats.log_activity("No signals generated", "INFO")
                    
                    for _ in range(15):
                        time.sleep(1)
                        live.update(create_dashboard_layout(dashboard.stats))
                    continue
                
                # Build market data for agent
                market_data = {
                    s: q.to_dict() for s, q in quotes.items()
                }
                
                indicators_dict = {
                    top_candidate.symbol: indicators.to_dict()
                }
                
                # Get memory lessons
                memory_lessons = memory_db.get_top_lessons_for_context(
                    regime="trending_up" if top_candidate.is_bullish else "trending_down",
                    strategies=["momentum", "trend_following"],
                    n=5,
                )
                
                # Run trading cycle
                workflow_id = f"LIVE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{cycle}"
                
                final_state = await run_trading_cycle(
                    graph=graph,
                    market_data=market_data,
                    indicators=indicators_dict,
                    signals=[s.to_dict() for s in signals],
                    memory_lessons=memory_lessons,
                    portfolio={"capital": dashboard.stats.current_balance, "positions": []},
                    daily_stats={
                        "trades_count": dashboard.stats.total_trades, 
                        "profit_loss": dashboard.stats.realized_pnl,
                        "max_drawdown": 0
                    },
                    thread_id=workflow_id,
                )
                
                # Update dashboard with results
                regime = final_state.get("regime", "unknown")
                confidence = final_state.get("regime_confidence", 0)
                strategies = final_state.get("active_strategies", [])
                
                dashboard.update_regime(regime, confidence, strategies)
                live.update(create_dashboard_layout(dashboard.stats))
                
                # Log validated/rejected signals
                validated = final_state.get("validated_signals", [])
                rejected = final_state.get("rejected_signals", [])
                
                dashboard.stats.signals_validated += len(validated)
                dashboard.stats.signals_rejected += len(rejected)
                
                for sig in validated:
                    dashboard.stats.log_activity(
                        f"VALIDATED: {sig.get('signal_type')} {sig.get('symbol')}",
                        "SUCCESS"
                    )
                
                for sig in rejected:
                    dashboard.stats.log_activity(
                        f"REJECTED: {sig.get('signal_type')} {sig.get('symbol')}",
                        "WARNING"
                    )
                
                live.update(create_dashboard_layout(dashboard.stats))
                
                # Log approved/risk-rejected trades
                approved = final_state.get("approved_trades", [])
                risk_rejected = final_state.get("risk_rejected", [])
                
                dashboard.stats.trades_approved += len(approved)
                dashboard.stats.trades_risk_rejected += len(risk_rejected)
                
                for trade in approved:
                    symbol = trade.get("symbol", "N/A")
                    side = trade.get("signal_type", "N/A")
                    price = trade.get("entry_price", 0)
                    
                    dashboard.stats.log_activity(
                        f"TRADE: {side} {symbol} @ Rs. {price:,.2f}",
                        "TRADE"
                    )
                    
                    # Add position
                    dashboard.add_position(symbol, side, 10, price)
                
                live.update(create_dashboard_layout(dashboard.stats))
                
                # Increment cycle
                dashboard.increment_cycle()
                live.update(create_dashboard_layout(dashboard.stats))
                
                # Simulate trade closure periodically
                if approved and cycle % 3 == 0:
                    pnl = random.uniform(-500, 1500)
                    dashboard.close_trade(pnl)
                    dashboard.stats.open_positions = []
                    live.update(create_dashboard_layout(dashboard.stats))
                
                # Wait before next cycle
                wait_time = 20  # 20 seconds between cycles
                dashboard.stats.log_activity(f"Next cycle in {wait_time}s...", "INFO")
                live.update(create_dashboard_layout(dashboard.stats))
                
                for _ in range(wait_time):
                    time.sleep(1)
                    live.update(create_dashboard_layout(dashboard.stats))
                    
        except KeyboardInterrupt:
            dashboard.stats.log_activity("Shutdown requested", "WARNING")
            live.update(create_dashboard_layout(dashboard.stats))
            
        finally:
            await market_manager.stop()
            console.print("\n[yellow]Trading stopped[/]")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_live_trading())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise


if __name__ == "__main__":
    main()
