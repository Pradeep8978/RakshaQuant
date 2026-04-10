"""
Agent Graph Module

LangGraph workflow orchestration for the trading agent system.
Defines the state graph and agent connections.
"""

import logging
from typing import Any, Literal

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from .state import TradingState, create_initial_state
from .market_regime import market_regime_node
from .news_analyst import news_sentiment_node
from .vision_analyst import vision_analyst_node
from .volume_analyst import volume_analyst_node
from .prediction import prediction_node
from .sentiment import sentiment_analysis_node
from .strategy_selection import strategy_selection_node
from .signal_validation import signal_validation_node
from .risk_compliance import risk_compliance_node, check_kill_switch

logger = logging.getLogger(__name__)


def should_continue_after_regime(state: TradingState) -> Literal["strategy_selection", "end"]:
    """
    Decide whether to continue after regime classification.
    
    Returns "end" if:
    - Regime confidence is too low
    - Kill switch is triggered
    """
    if check_kill_switch(state):
        logger.warning("Kill switch triggered - ending workflow")
        return "end"
    
    regime_confidence = state.get("regime_confidence", 0)
    if regime_confidence < 0.3:
        logger.info(f"Regime confidence too low ({regime_confidence:.2f}) - skipping trading")
        return "end"
    
    return "strategy_selection"


def should_continue_after_validation(state: TradingState) -> Literal["risk_compliance", "end"]:
    """
    Decide whether to continue to risk checks.
    
    Returns "end" if no signals were validated.
    """
    validated_signals = state.get("validated_signals", [])
    
    if not validated_signals:
        logger.info("No validated signals - ending workflow")
        return "end"
    
    return "risk_compliance"


def create_trading_graph(
    checkpointer: Any = None,
    with_memory: bool = True,
) -> StateGraph:
    """
    Create the trading agent workflow graph.
    
    The graph flows as:
    1. Market Regime Agent -> classifies market conditions
    2. Strategy Selection Agent -> picks active strategies
    3. Signal Validation Agent -> filters signals
    4. Prediction Analysis Agent -> forecasts outcomes
    5. Vision Analysis Agent -> visual validation
    6. Risk & Compliance Agent -> final approval
    
    Args:
        checkpointer: Optional checkpointer for state persistence
        with_memory: Whether to include memory saver (default True)
        
    Returns:
        Compiled StateGraph ready for execution
    """
    
    # Create the graph with TradingState
    workflow = StateGraph(TradingState)
    
    # Add nodes
    workflow.add_node("news_sentiment", news_sentiment_node)
    workflow.add_node("market_mood", sentiment_analysis_node)
    workflow.add_node("volume_analysis", volume_analyst_node)
    workflow.add_node("market_regime", market_regime_node)
    workflow.add_node("strategy_selection", strategy_selection_node)
    workflow.add_node("signal_validation", signal_validation_node)
    workflow.add_node("prediction_analysis", prediction_node)
    workflow.add_node("vision_analysis", vision_analyst_node)
    workflow.add_node("risk_compliance", risk_compliance_node)
    
    # ---------------------------------------------------------
    # PARALLEL STEP 1: Context Gathering (Fan-out from START)
    # ---------------------------------------------------------
    workflow.add_edge(START, "news_sentiment")
    workflow.add_edge(START, "market_mood")
    workflow.add_edge(START, "volume_analysis")
    
    # ---------------------------------------------------------
    # JOIN STEP 1: Process Context into Regime (Fan-in to Regime)
    # ---------------------------------------------------------
    workflow.add_edge("news_sentiment", "market_regime")
    workflow.add_edge("market_mood", "market_regime")
    workflow.add_edge("volume_analysis", "market_regime")
    
    # Market Regime -> (conditional) -> Strategy Selection or End
    workflow.add_conditional_edges(
        "market_regime",
        should_continue_after_regime,
        {
            "strategy_selection": "strategy_selection",
            "end": END,
        }
    )
    
    # Strategy Selection -> Signal Validation
    workflow.add_edge("strategy_selection", "signal_validation")
    
    # ---------------------------------------------------------
    # PARALLEL STEP 2: Signal Intelligence (Fan-out from Validation)
    # ---------------------------------------------------------
    # We use a conditional edge to decide if we even need signal analysis
    workflow.add_conditional_edges(
        "signal_validation",
        should_continue_after_validation,
        {
            "risk_compliance": ["prediction_analysis", "vision_analysis"],
            "end": END,
        }
    )
    
    # ---------------------------------------------------------
    # JOIN STEP 2: Consolidated Risk Gate (Fan-in to Risk)
    # ---------------------------------------------------------
    workflow.add_edge("prediction_analysis", "risk_compliance")
    workflow.add_edge("vision_analysis", "risk_compliance")
    
    # Risk Compliance -> Final Decision
    workflow.add_edge("risk_compliance", END)
    
    # Compile with optional checkpointer
    if checkpointer is None and with_memory:
        checkpointer = MemorySaver()
    
    compiled = workflow.compile(checkpointer=checkpointer)
    
    logger.info("Trading graph compiled successfully")
    return compiled


async def run_trading_cycle(
    graph: StateGraph,
    market_data: dict[str, Any],
    indicators: dict[str, Any],
    signals: list[dict[str, Any]],
    memory_lessons: list[dict[str, Any]] = None,
    portfolio: dict[str, Any] = None,
    daily_stats: dict[str, Any] = None,
    thread_id: str = "default",
) -> TradingState:
    """
    Run a complete trading cycle through the agent graph.
    
    Args:
        graph: Compiled trading graph
        market_data: Current market data
        indicators: Calculated indicators
        signals: Raw signals from signal engine
        memory_lessons: Lessons from past trades
        portfolio: Current portfolio state
        daily_stats: Today's trading statistics
        thread_id: Thread ID for checkpointing
        
    Returns:
        Final trading state with decisions
    """
    
    # Create initial state with inputs
    state = create_initial_state()
    state["market_data"] = market_data
    state["indicators"] = indicators
    state["signals"] = [s.to_dict() if hasattr(s, 'to_dict') else s for s in signals]
    state["memory_lessons"] = memory_lessons or []
    state["portfolio"] = portfolio or {"capital": 1000000, "positions": []}
    state["daily_stats"] = daily_stats or {"trades_count": 0, "profit_loss": 0, "max_drawdown": 0}
    
    # Configure for tracing
    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "metadata": {
            "workflow_type": "trading_cycle",
            "signals_count": len(signals),
        },
    }
    
    # Run the graph
    logger.info(f"Starting trading cycle with {len(signals)} signals")
    
    final_state = await graph.ainvoke(state, config=config)
    
    # Log results
    approved = len(final_state.get("approved_trades", []))
    rejected_signal = len(final_state.get("rejected_signals", []))
    rejected_risk = len(final_state.get("risk_rejected", []))
    
    logger.info(
        f"Trading cycle complete: "
        f"{approved} approved, {rejected_signal} signal-rejected, {rejected_risk} risk-rejected"
    )
    
    return final_state


def get_graph_visualization(graph: StateGraph) -> str:
    """
    Get a Mermaid diagram of the trading graph.
    
    Returns:
        Mermaid diagram string
    """
    try:
        return graph.get_graph().draw_mermaid()
    except Exception as e:
        logger.warning(f"Could not generate graph visualization: {e}")
        return """
        graph TD
            START --> market_regime
            market_regime --> |high confidence| strategy_selection
            market_regime --> |low confidence| END
            strategy_selection --> signal_validation
            signal_validation --> |has signals| risk_compliance
            signal_validation --> |no signals| END
            risk_compliance --> END
        """
