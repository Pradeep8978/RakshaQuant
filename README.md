# 🤖 Agentic Paper Trading System for NSE

A production-grade **agentic paper trading system** for the Indian National Stock Exchange (NSE) with:

- 🧠 **LangGraph-orchestrated multi-agent decision layer**
- 📚 **Learning feedback loop** via agent memory
- 🔍 **Full observability** via LangSmith
- 📈 **Paper-first design** with upgrade path to live trading

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Agentic Paper Trading System                         │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────-──┤
│ Market Data     │ Decision Layer  │ Execution       │ Memory & Learning     │
│ Layer           │ (LangGraph)     │ Layer           │ Layer                 │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ • WebSocket     │ • Regime Agent  │ • Paper Adapter │ • Outcome Analyzer    │
│ • Indicators    │ • Strategy Agent│ • Trade Journal │ • Mistake Classifier  │
│ • Signals       │ • Signal Agent  │ • Replay        │ • Memory Database     │
│                 │ • Risk Agent    │                 │ • Memory Injection    │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   LangSmith       │
                    │   Observability   │
                    └───────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- PostgreSQL (for agent memory)
- Redis (optional, for market data caching)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/trading-agent.git
cd trading-agent

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
# Required API Keys
GROQ_API_KEY=your_groq_api_key
DHAN_CLIENT_ID=your_dhan_client_id
DHAN_ACCESS_TOKEN=your_dhan_access_token
LANGSMITH_API_KEY=your_langsmith_api_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_agent
```

### Running

```bash
# Run the trading system (paper mode)
uv run python scripts/run_trading.py

# Run tests
uv run pytest tests/ -v
```

## 📁 Project Structure

```
src/
├── config/          # Configuration management
├── market/          # Market data & signals
│   ├── data_feed.py     # WebSocket data ingestion
│   ├── indicators.py    # Technical indicators
│   └── signals.py       # Signal generation
├── agents/          # LangGraph agents
│   ├── state.py         # Shared state definition
│   ├── graph.py         # Agent workflow orchestration
│   ├── market_regime.py # Market regime classification
│   ├── strategy_selection.py
│   ├── signal_validation.py
│   └── risk_compliance.py
├── execution/       # Trade execution
│   ├── adapter.py       # DhanHQ integration
│   └── journal.py       # Trade logging
├── memory/          # Learning feedback loop
│   ├── analyzer.py      # Outcome analysis
│   ├── classifier.py    # Mistake classification
│   ├── database.py      # PostgreSQL storage
│   └── injection.py     # Memory injection
└── observability/   # LangSmith tracing
    └── tracing.py
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## 📊 Observability

All agent decisions are traced in LangSmith with:

- Regime classification
- Strategy selection
- Signal validation
- Risk decisions
- Trade outcomes

View traces at: https://smith.langchain.com

## ⚠️ Disclaimer

This is a **paper trading system** for educational and research purposes. No real capital is at risk. Always perform thorough testing before considering live trading.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
