<div align="center">

# 🛡️ RakshaQuant

### Agentic Paper Trading System for NSE

_My first journey into building AI-powered financial systems_

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Powered-orange.svg)](https://github.com/langchain-ai/langgraph)
[![LangSmith](https://img.shields.io/badge/LangSmith-Observable-green.svg)](https://smith.langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 🎯 About This Project

**RakshaQuant** (रक्षा = Protection in Sanskrit) is an agentic paper trading system designed for the Indian NSE market. Built as a solo developer project to explore the intersection of **Large Language Models** and **Financial Technology (BFSI)**.

This project represents my first deep dive into:

- 🤖 **Multi-agent orchestration** with LangGraph
- 📊 **Algorithmic trading concepts** and technical analysis
- 🔍 **LLM observability** with LangSmith
- 🧠 **Learning feedback loops** that improve over time

> _"The goal isn't just to build a trading bot, but to understand how AI agents can reason about complex, real-time financial decisions."_

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RakshaQuant Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│   │  Market     │───▶│  Technical  │───▶│  Signal Generation      │ │
│   │  Data Feed  │    │  Indicators │    │  (4 Strategies)         │ │
│   └─────────────┘    └─────────────┘    └───────────┬─────────────┘ │
│         │                                           │               │
│         ▼                                           ▼               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    LangGraph Agent Orchestration             │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │   │
│   │  │ Market Regime│─▶│  Strategy    │─▶│   Signal     │       │   │
│   │  │    Agent     │  │  Selection   │  │  Validation  │       │   │
│   │  │   (LLM)      │  │   Agent      │  │    Agent     │       │   │
│   │  └──────────────┘  └──────────────┘  └──────┬───────┘       │   │
│   │                                             │                │   │
│   │                                    ┌────────▼────────┐       │   │
│   │                                    │ Risk & Compliance│      │   │
│   │                                    │  (Deterministic) │      │   │
│   │                                    └────────┬─────────┘      │   │
│   └─────────────────────────────────────────────┼────────────────┘   │
│                                                 │                    │
│         ┌───────────────────────────────────────┼──────────────┐     │
│         │                                       ▼              │     │
│         │   ┌─────────────┐         ┌──────────────────────┐  │     │
│         │   │   Memory    │◀────────│   Trade Execution    │  │     │
│         │   │  Database   │         │   (Paper Trading)    │  │     │
│         │   └──────┬──────┘         └──────────────────────┘  │     │
│         │          │                                          │     │
│         │          ▼                                          │     │
│         │   ┌─────────────┐         ┌──────────────────────┐  │     │
│         │   │  Mistake    │────────▶│    Trade Journal     │  │     │
│         │   │ Classifier  │         │   (PostgreSQL)       │  │     │
│         │   └─────────────┘         └──────────────────────┘  │     │
│         │          Feedback & Learning Loop                   │     │
│         └─────────────────────────────────────────────────────┘     │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    LangSmith Observability                    │  │
│   │        Full trace of every agent decision for debugging       │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🤖 Multi-Agent Decision Making

| Agent                  | Purpose                                        | Technology          |
| ---------------------- | ---------------------------------------------- | ------------------- |
| **Market Regime**      | Classifies market as trending/ranging/volatile | LLM (Groq)          |
| **Strategy Selection** | Chooses active strategies based on regime      | LLM (Groq)          |
| **Signal Validation**  | Filters low-quality signals                    | LLM (Groq)          |
| **Risk & Compliance**  | Enforces position limits, kill switch          | Deterministic Rules |

### 📈 Trading Strategies

- **Momentum**: Rides strong directional moves
- **Mean Reversion**: Trades oversold/overbought conditions
- **Breakout**: Captures volatility expansions
- **Trend Following**: Follows established trends with ADX confirmation

### 🧠 Learning Feedback Loop

- Analyzes trade outcomes (MAE/MFE, efficiency)
- Classifies mistakes using LLM + rules
- Stores lessons with time-decay relevance
- Injects past lessons into agent context

### 🛡️ Safety Features

- **Kill Switch**: Halts trading on daily loss limit
- **Position Limits**: Max 10% per position
- **Daily Trade Cap**: Configurable max trades
- **Trading Hours**: Respects NSE market hours
- **Paper-First**: Default mode uses simulated funds

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL database (or free cloud: [Neon](https://neon.tech))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/RakshaQuant.git
cd RakshaQuant

# Install dependencies
uv sync

# Copy environment template
cp .env.example .env
```

### Configuration

Edit `.env` with your API keys:

| Service        | Get API Key                                                 | Free Tier       |
| -------------- | ----------------------------------------------------------- | --------------- |
| **Groq**       | [console.groq.com/keys](https://console.groq.com/keys)      | ✅ Free         |
| **DhanHQ**     | [developer.dhan.co](https://developer.dhan.co)              | ✅ Sandbox      |
| **LangSmith**  | [smith.langchain.com](https://smith.langchain.com/settings) | ✅ 5K traces/mo |
| **PostgreSQL** | [neon.tech](https://neon.tech)                              | ✅ 0.5GB free   |

### Run Demo

```bash
uv run python scripts/run_trading.py
```

### Run Tests

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 📁 Project Structure

```
RakshaQuant/
├── src/
│   ├── agents/              # LangGraph agents
│   │   ├── graph.py         # Agent orchestration
│   │   ├── market_regime.py # Regime classification
│   │   ├── strategy_selection.py
│   │   ├── signal_validation.py
│   │   └── risk_compliance.py
│   ├── market/              # Market data & signals
│   │   ├── data_feed.py     # WebSocket ingestion
│   │   ├── indicators.py    # Technical indicators
│   │   └── signals.py       # Strategy signal engine
│   ├── execution/           # Trade execution
│   │   ├── adapter.py       # DhanHQ integration
│   │   └── journal.py       # Trade journal (PostgreSQL)
│   ├── memory/              # Learning system
│   │   ├── analyzer.py      # Outcome analysis
│   │   ├── classifier.py    # Mistake classification
│   │   ├── database.py      # Memory storage
│   │   └── injection.py     # Context injection
│   └── observability/       # LangSmith integration
│       └── tracing.py
├── tests/                   # Unit tests
├── scripts/
│   └── run_trading.py       # Entry point
├── logs/                    # Trading logs (gitignored)
├── pyproject.toml
└── README.md
```

---

## 🔍 Observability

Every agent decision is traced in **LangSmith**:

```
LangGraph (5.80s)
├── market_regime (2.85s)
│   └── ChatGroq llama-3.3-70b-versatile
├── should_continue_after_regime
├── strategy_selection (1.65s)
│   └── ChatGroq llama-3.3-70b-versatile
├── signal_validation (1.16s)
│   └── ChatGroq llama-3.3-70b-versatile
├── should_continue_after_validation
└── risk_compliance (0.00s)
```

View traces at: [smith.langchain.com](https://smith.langchain.com)

---

## 🎓 What I Learned

Building RakshaQuant taught me:

1. **LangGraph Patterns**: StateGraph, conditional edges, checkpointing
2. **Agent Design**: When to use LLM vs deterministic rules
3. **Financial Domain**: Technical indicators, risk management, trading psychology
4. **Observability**: The importance of tracing every decision for debugging
5. **Memory Systems**: Time-decay relevance, context injection

---

## ⚠️ Disclaimer

> **This is a learning project for educational purposes only.**
>
> - Not financial advice
> - Paper trading only (no real money by default)
> - Past performance doesn't guarantee future results
> - Always consult a financial advisor for real investments

---

## 🛣️ Roadmap

- [ ] Live market data integration
- [ ] Backtesting framework
- [ ] Multi-symbol portfolio management
- [ ] Options trading support
- [ ] Telegram/Discord alerts
- [ ] Web dashboard

---

## 🤝 Contributing

This is a personal learning project, but suggestions and feedback are welcome! Feel free to open issues or PRs.

---

## 📄 License

MIT License - feel free to use this for your own learning journey!

---

<div align="center">

**Built with ❤️ by a solo developer exploring the BFSI × AI frontier**

_RakshaQuant - Where AI meets Markets_

</div>
