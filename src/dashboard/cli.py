"""
CLI Trading Dashboard

Real-time terminal dashboard showing trading activity,
agent decisions, and P&L statistics.
"""

import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


console = Console()


@dataclass
class TradingStats:
    """Real-time trading statistics."""
    
    # Session info
    session_start: datetime = field(default_factory=datetime.now)
    trading_mode: str = "paper"
    
    # Account
    starting_balance: float = 1000000.0
    current_balance: float = 1000000.0
    
    # Trades
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Open positions
    open_positions: list = field(default_factory=list)
    
    # Agent activity
    cycles_run: int = 0
    signals_generated: int = 0
    signals_validated: int = 0
    signals_rejected: int = 0
    trades_approved: int = 0
    trades_risk_rejected: int = 0
    
    # Current regime
    current_regime: str = "unknown"
    regime_confidence: float = 0.0
    active_strategies: list = field(default_factory=list)
    
    # Recent activity log
    activity_log: list = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def pnl_percent(self) -> float:
        if self.starting_balance == 0:
            return 0.0
        return (self.total_pnl / self.starting_balance) * 100
    
    def log_activity(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append({
            "time": timestamp,
            "level": level,
            "message": message,
        })
        # Keep last 10 entries
        if len(self.activity_log) > 10:
            self.activity_log = self.activity_log[-10:]


def create_header(stats: TradingStats) -> Panel:
    """Create the header panel."""
    
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right", ratio=1)
    
    # Mode badge
    mode_color = "green" if stats.trading_mode == "paper" else "red"
    mode_text = f"[bold {mode_color}][[{stats.trading_mode.upper()}]][/]"
    
    # Session time
    elapsed = datetime.now() - stats.session_start
    elapsed_str = str(elapsed).split('.')[0]
    
    grid.add_row(
        mode_text,
        "[bold cyan]RakshaQuant Trading Dashboard[/]",
        f"[dim]Session: {elapsed_str}[/]"
    )
    
    return Panel(grid, style="bold white", box=box.DOUBLE)


def create_account_panel(stats: TradingStats) -> Panel:
    """Create the account summary panel."""
    
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Label", style="dim")
    table.add_column("Value", justify="right")
    
    # Balance
    balance_color = "green" if stats.current_balance >= stats.starting_balance else "red"
    table.add_row("Balance", f"[bold {balance_color}]Rs. {stats.current_balance:,.2f}[/]")
    
    # P&L
    pnl_color = "green" if stats.total_pnl >= 0 else "red"
    pnl_sign = "+" if stats.total_pnl >= 0 else ""
    table.add_row(
        "Total P&L",
        f"[bold {pnl_color}]{pnl_sign}Rs. {stats.total_pnl:,.2f} ({pnl_sign}{stats.pnl_percent:.2f}%)[/]"
    )
    
    table.add_row("Realized", f"Rs. {stats.realized_pnl:,.2f}")
    table.add_row("Unrealized", f"Rs. {stats.unrealized_pnl:,.2f}")
    
    return Panel(table, title="[bold]Account[/]", border_style="blue")


def create_trades_panel(stats: TradingStats) -> Panel:
    """Create the trades summary panel."""
    
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Label", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Trades", f"[bold]{stats.total_trades}[/]")
    table.add_row("Winners", f"[green]{stats.winning_trades}[/]")
    table.add_row("Losers", f"[red]{stats.losing_trades}[/]")
    
    # Win rate with color
    wr_color = "green" if stats.win_rate >= 50 else "yellow" if stats.win_rate >= 40 else "red"
    table.add_row("Win Rate", f"[bold {wr_color}]{stats.win_rate:.1f}%[/]")
    
    return Panel(table, title="[bold]Trades[/]", border_style="green")


def create_agent_panel(stats: TradingStats) -> Panel:
    """Create the agent activity panel."""
    
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Label", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Cycles Run", f"[bold]{stats.cycles_run}[/]")
    table.add_row("Signals Generated", f"{stats.signals_generated}")
    table.add_row("Validated", f"[green]{stats.signals_validated}[/]")
    table.add_row("Rejected", f"[red]{stats.signals_rejected}[/]")
    table.add_row("Risk Blocked", f"[yellow]{stats.trades_risk_rejected}[/]")
    
    return Panel(table, title="[bold]Agent Activity[/]", border_style="magenta")


def create_regime_panel(stats: TradingStats) -> Panel:
    """Create the market regime panel."""
    
    regime_colors = {
        "trending_up": "green",
        "trending_down": "red",
        "ranging": "yellow",
        "volatile": "magenta",
        "unknown": "dim",
    }
    
    color = regime_colors.get(stats.current_regime, "white")
    
    content = Text()
    content.append(f"\n  Regime: ", style="dim")
    content.append(f"{stats.current_regime.upper()}\n", style=f"bold {color}")
    content.append(f"  Confidence: ", style="dim")
    content.append(f"{stats.regime_confidence:.0%}\n", style="bold")
    content.append(f"\n  Strategies: ", style="dim")
    
    if stats.active_strategies:
        content.append(", ".join(stats.active_strategies), style="cyan")
    else:
        content.append("None", style="dim")
    
    content.append("\n")
    
    return Panel(content, title="[bold]Market Regime[/]", border_style="cyan")


def create_positions_panel(stats: TradingStats) -> Panel:
    """Create the open positions panel."""
    
    if not stats.open_positions:
        content = Text("\n  No open positions\n", style="dim italic")
        return Panel(content, title="[bold]Open Positions[/]", border_style="yellow")
    
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("Symbol", style="bold")
    table.add_column("Side")
    table.add_column("Qty", justify="right")
    table.add_column("Entry", justify="right")
    table.add_column("P&L", justify="right")
    
    for pos in stats.open_positions[:5]:  # Show max 5
        pnl = pos.get("pnl", 0)
        pnl_color = "green" if pnl >= 0 else "red"
        pnl_sign = "+" if pnl >= 0 else ""
        
        side_color = "green" if pos.get("side") == "BUY" else "red"
        
        table.add_row(
            pos.get("symbol", "N/A"),
            f"[{side_color}]{pos.get('side', 'N/A')}[/]",
            str(pos.get("qty", 0)),
            f"Rs. {pos.get('entry', 0):,.2f}",
            f"[{pnl_color}]{pnl_sign}Rs. {pnl:,.2f}[/]"
        )
    
    return Panel(table, title="[bold]Open Positions[/]", border_style="yellow")


def create_activity_panel(stats: TradingStats) -> Panel:
    """Create the activity log panel."""
    
    if not stats.activity_log:
        content = Text("\n  Waiting for activity...\n", style="dim italic")
        return Panel(content, title="[bold]Activity Log[/]", border_style="white")
    
    lines = []
    for entry in stats.activity_log[-8:]:  # Last 8 entries
        level_color = {
            "INFO": "blue",
            "SUCCESS": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "TRADE": "cyan",
        }.get(entry["level"], "white")
        
        lines.append(f"[dim]{entry['time']}[/] [{level_color}]{entry['level']:7}[/] {entry['message']}")
    
    content = "\n".join(lines)
    
    return Panel(content, title="[bold]Activity Log[/]", border_style="white")


def create_dashboard_layout(stats: TradingStats) -> Layout:
    """Create the full dashboard layout."""
    
    layout = Layout()
    
    # Main structure
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=12),
    )
    
    # Body split
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="middle"),
        Layout(name="right"),
    )
    
    # Left column
    layout["left"].split_column(
        Layout(name="account"),
        Layout(name="trades"),
    )
    
    # Middle column
    layout["middle"].split_column(
        Layout(name="regime"),
        Layout(name="positions"),
    )
    
    # Right column - agent activity
    layout["right"].update(create_agent_panel(stats))
    
    # Populate panels
    layout["header"].update(create_header(stats))
    layout["account"].update(create_account_panel(stats))
    layout["trades"].update(create_trades_panel(stats))
    layout["regime"].update(create_regime_panel(stats))
    layout["positions"].update(create_positions_panel(stats))
    layout["footer"].update(create_activity_panel(stats))
    
    return layout


class TradingDashboard:
    """Live trading dashboard manager."""
    
    def __init__(self):
        self.stats = TradingStats()
        self.live = None
        self.running = False
    
    def start(self, balance: float = 1000000.0, mode: str = "paper"):
        """Start the dashboard."""
        self.stats.starting_balance = balance
        self.stats.current_balance = balance
        self.stats.trading_mode = mode
        self.stats.session_start = datetime.now()
        self.running = True
        
        self.stats.log_activity("Dashboard started", "INFO")
        self.stats.log_activity(f"Trading mode: {mode.upper()}", "INFO")
        self.stats.log_activity(f"Starting balance: Rs. {balance:,.2f}", "INFO")
    
    def update_regime(self, regime: str, confidence: float, strategies: list):
        """Update market regime info."""
        self.stats.current_regime = regime
        self.stats.regime_confidence = confidence
        self.stats.active_strategies = strategies
        self.stats.log_activity(f"Regime: {regime} ({confidence:.0%})", "INFO")
    
    def log_signal(self, symbol: str, signal_type: str, strategy: str, validated: bool):
        """Log a signal."""
        self.stats.signals_generated += 1
        if validated:
            self.stats.signals_validated += 1
            self.stats.log_activity(f"Signal VALIDATED: {signal_type} {symbol} [{strategy}]", "SUCCESS")
        else:
            self.stats.signals_rejected += 1
            self.stats.log_activity(f"Signal REJECTED: {signal_type} {symbol}", "WARNING")
    
    def log_trade(self, symbol: str, side: str, qty: int, price: float, approved: bool):
        """Log a trade decision."""
        if approved:
            self.stats.trades_approved += 1
            self.stats.log_activity(f"TRADE: {side} {qty} {symbol} @ Rs. {price:,.2f}", "TRADE")
        else:
            self.stats.trades_risk_rejected += 1
            self.stats.log_activity(f"Trade BLOCKED by risk: {side} {symbol}", "WARNING")
    
    def add_position(self, symbol: str, side: str, qty: int, entry_price: float):
        """Add an open position."""
        self.stats.open_positions.append({
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry": entry_price,
            "pnl": 0.0,
        })
    
    def close_trade(self, pnl: float):
        """Record a closed trade."""
        self.stats.total_trades += 1
        self.stats.realized_pnl += pnl
        self.stats.current_balance += pnl
        
        if pnl >= 0:
            self.stats.winning_trades += 1
            self.stats.log_activity(f"Trade CLOSED: +Rs. {pnl:,.2f}", "SUCCESS")
        else:
            self.stats.losing_trades += 1
            self.stats.log_activity(f"Trade CLOSED: Rs. {pnl:,.2f}", "ERROR")
    
    def increment_cycle(self):
        """Increment cycle counter."""
        self.stats.cycles_run += 1
        self.stats.log_activity(f"Trading cycle #{self.stats.cycles_run} completed", "INFO")
    
    def render(self) -> Layout:
        """Render the dashboard."""
        return create_dashboard_layout(self.stats)
    
    def run_live(self, refresh_rate: float = 0.5):
        """Run the dashboard with live updates."""
        with Live(self.render(), console=console, refresh_per_second=int(1/refresh_rate)) as live:
            self.live = live
            try:
                while self.running:
                    live.update(self.render())
                    time.sleep(refresh_rate)
            except KeyboardInterrupt:
                self.running = False
                console.print("\n[yellow]Dashboard stopped[/]")


def demo_dashboard():
    """Demo the dashboard with simulated data."""
    
    dashboard = TradingDashboard()
    dashboard.start(balance=1000000.0, mode="paper")
    
    console.print("[bold green]Starting RakshaQuant Trading Dashboard Demo...[/]\n")
    console.print("[dim]Press Ctrl+C to exit[/]\n")
    time.sleep(1)
    
    with Live(dashboard.render(), console=console, refresh_per_second=2) as live:
        dashboard.live = live
        
        try:
            # Simulate activity
            time.sleep(2)
            dashboard.update_regime("trending_up", 0.70, ["momentum", "trend_following"])
            live.update(dashboard.render())
            
            time.sleep(2)
            dashboard.log_signal("RELIANCE", "BUY", "trend_following", True)
            live.update(dashboard.render())
            
            time.sleep(2)
            dashboard.log_trade("RELIANCE", "BUY", 10, 2500.0, True)
            dashboard.add_position("RELIANCE", "BUY", 10, 2500.0)
            live.update(dashboard.render())
            
            time.sleep(2)
            dashboard.increment_cycle()
            live.update(dashboard.render())
            
            time.sleep(3)
            dashboard.close_trade(500.0)
            dashboard.stats.open_positions = []
            live.update(dashboard.render())
            
            # Keep running
            while True:
                time.sleep(0.5)
                live.update(dashboard.render())
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped[/]")


if __name__ == "__main__":
    demo_dashboard()
