import asyncio
import logging
from typing import Any
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import AgentMemoryDB
from src.execution.journal import TradeJournal
from src.execution.paper_engine import LocalPaperEngine
from src.market.manager import MarketDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard_api")

# Minimal global state referencing the database and systems
memory_db = None
journal = None
paper_engine = None
market_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory_db, journal, paper_engine, market_manager
    logger.info("Initializing services for API...")
    memory_db = AgentMemoryDB()
    journal = TradeJournal()
    paper_engine = LocalPaperEngine()
    # Let's get the market manager initialized with default top symbols
    market_manager = MarketDataManager(symbols=["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"])
    # Not starting the full lifecycle but able to get simulated data
    yield
    # Cleanup
    logger.info("Shutting down API...")

app = FastAPI(title="RakshaQuant Dashboard API", lifespan=lifespan)

# Allow React app to fetch from this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/dashboard/summary")
async def get_summary():
    """Get high-level statistics for the dashboard."""
    try:
        # P&L Stats from TradeJournal
        perf = journal.get_performance_summary()
        
        # Paper Wallet Status
        balance = paper_engine.balance
        positions = paper_engine.positions
        
        # Format the numbers nicely
        win_rate = perf.get("win_rate", 0)
        total_pnl = perf.get("total_pnl", 0)
        total_trades = perf.get("total_trades", 0)
        
        return {
            "balance": balance,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "open_positions": len(positions),
        }
    except Exception as e:
        logger.error(f"Error serving summary: {e}")
        return {"error": str(e)}

@app.get("/api/dashboard/trades")
async def get_recent_trades(limit: int = 20):
    """Get recent trades."""
    try:
        # In this simplistic layout, just fetch closed trades
        # Or better query your DB directly
        from src.execution.journal import TradeRecord
        session = journal._session
        from sqlalchemy import desc
        
        records = session.query(TradeRecord).order_by(desc(TradeRecord.entry_time)).limit(limit).all()
        return [journal._record_to_dict(r) for r in records]
    except Exception as e:
        logger.error(f"Error serving trades: {e}")
        return []

@app.get("/api/dashboard/lessons")
async def get_recent_lessons(limit: int = 10):
    """Get recent learning lessons."""
    try:
        lessons = memory_db.get_lessons(limit=limit, include_expired=False)
        return lessons
    except Exception as e:
        logger.error(f"Error serving lessons: {e}")
        return []

if __name__ == "__main__":
    uvicorn.run("scripts.dashboard_api:app", host="127.0.0.1", port=8000, reload=True)
