import asyncio
import logging
from typing import Any
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.database import AgentMemoryDB
from src.execution.journal import TradeJournal
from src.execution.paper_engine import LocalPaperEngine
from src.market.manager import MarketDataManager
from sqlalchemy import desc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard_api")

memory_db = None
journal = None
paper_engine = None
market_manager = None

# Track active websocket connections
active_connections: list[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory_db, journal, paper_engine, market_manager
    logger.info("Initializing services for API...")
    memory_db = AgentMemoryDB()
    journal = TradeJournal()
    paper_engine = LocalPaperEngine()
    market_manager = MarketDataManager(symbols=["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"])
    yield
    logger.info("Shutting down API...")

app = FastAPI(title="RakshaQuant Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_summary_data():
    try:
        perf = journal.get_performance_summary()
        balance = paper_engine.balance
        positions = paper_engine.positions
        
        return {
            "balance": balance,
            "total_trades": perf.get("total_trades", 0),
            "win_rate": perf.get("win_rate", 0),
            "total_pnl": perf.get("total_pnl", 0),
            "open_positions": len(positions),
            "is_halted": memory_db.get_state("trading_halted") == "true"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/dashboard/summary")
async def get_summary():
    return _get_summary_data()

@app.get("/api/dashboard/trades")
async def get_recent_trades(limit: int = 20):
    try:
        from src.execution.journal import TradeRecord
        session = journal._session
        records = session.query(TradeRecord).order_by(desc(TradeRecord.entry_time)).limit(limit).all()
        return [journal._record_to_dict(r) for r in records]
    except Exception as e:
        logger.error(f"Error serving trades: {e}")
        return []

@app.get("/api/dashboard/lessons")
async def get_recent_lessons(limit: int = 10):
    try:
        return memory_db.get_lessons(limit=limit, include_expired=False)
    except Exception as e:
        logger.error(f"Error serving lessons: {e}")
        return []

@app.get("/api/dashboard/chart")
async def get_chart_data():
    """Build equity curve from historical trades."""
    try:
        from src.execution.journal import TradeRecord
        session = journal._session
        # Get all closed trades, ordered by time
        trades = session.query(TradeRecord).filter_by(status="closed").order_by(TradeRecord.exit_time.asc()).all()
        
        # Start at initial balance (assume 1000000 for paper default)
        # Using the engine's initial balance or just a default baseline
        current_balance = 1000000
        data_points = []
        
        for t in trades:
            if t.profit_loss is not None:
                current_balance += t.profit_loss
                time_str = t.exit_time.strftime("%H:%M")
                data_points.append({"time": time_str, "balance": current_balance})
        
        # Add current state to end
        if data_points:
            data_points.append({"time": "Now", "balance": current_balance})
        else:
            data_points = [{"time": "Start", "balance": current_balance}]
            
        return data_points
    except Exception as e:
        logger.error(f"Error serving chart data: {e}")
        return []

class HaltRequest(BaseModel):
    halted: bool

@app.post("/api/dashboard/halt")
async def toggle_halt(req: HaltRequest):
    """Toggle the master kill switch."""
    try:
        val = "true" if req.halted else "false"
        success = memory_db.set_state("trading_halted", val)
        return {"success": success, "is_halted": req.halted}
    except Exception as e:
        logger.error(f"Failed to toggle halt: {e}")
        return {"success": False, "error": str(e)}

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Stream real-time dashboard updates."""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Poll state and push. A smarter app would use PubSub.
            await asyncio.sleep(2)
            if not active_connections:
                break
                
            summary = _get_summary_data()
            await websocket.send_json({"type": "summary", "data": summary})
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("scripts.dashboard_api:app", host="127.0.0.1", port=8000, reload=True)
