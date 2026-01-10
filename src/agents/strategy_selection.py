"""
Strategy Selection Agent Module

Selects active trading strategies based on the current market regime
and historical performance data.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import get_settings
from .state import TradingState

logger = logging.getLogger(__name__)


STRATEGY_SYSTEM_PROMPT = """You are a Strategy Selection Agent for an automated trading system.

Your role is to select which trading strategies should be active based on:
1. The current market regime (trending_up, trending_down, ranging, volatile)
2. Historical performance of each strategy in similar conditions
3. Memory lessons from past strategy selection mistakes

Available strategies:
- momentum: Best in trending markets with strong directional moves
- mean_reversion: Best in ranging markets with clear support/resistance
- breakout: Best when volatility is low and a breakout is anticipated
- trend_following: Best in established trends with high ADX

Consider:
- Avoid strategies that historically underperformed in the current regime
- Don't be too aggressive - selecting 1-2 strategies is often better than all 4
- Weight memory lessons heavily - past mistakes should inform current decisions

Respond with JSON:
{
    "active_strategies": ["list", "of", "strategy", "names"],
    "reasoning": "Explanation of selection with specific reference to regime and lessons",
    "strategy_notes": {
        "strategy_name": "why selected or rejected"
    }
}"""


def create_strategy_agent() -> ChatGroq:
    """Create the strategy selection agent."""
    settings = get_settings()
    
    return ChatGroq(
        api_key=settings.groq_api_key.get_secret_value(),
        model_name=settings.groq_model_primary,
        temperature=settings.groq_temperature,
        max_tokens=1024,
    )


def strategy_selection_node(state: TradingState) -> dict[str, Any]:
    """
    LangGraph node for strategy selection.
    
    Selects which strategies should be active based on regime and memory.
    
    Args:
        state: Current trading state with regime and memory lessons
        
    Returns:
        State updates with active strategies
    """
    logger.info("Running Strategy Selection Agent...")
    
    try:
        regime = state.get("regime", "unknown")
        regime_confidence = state.get("regime_confidence", 0.0)
        memory_lessons = state.get("memory_lessons", [])
        daily_stats = state.get("daily_stats", {})
        
        # Filter relevant lessons
        strategy_lessons = [
            lesson for lesson in memory_lessons
            if lesson.get("category") in ["strategy_mismatch", "overtrading"]
        ]
        
        # Build context
        context = _build_strategy_context(
            regime, regime_confidence, strategy_lessons, daily_stats
        )
        
        # Create and run agent
        agent = create_strategy_agent()
        
        messages = [
            SystemMessage(content=STRATEGY_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]
        
        response = agent.invoke(messages)
        result = _parse_strategy_response(response.content)
        
        logger.info(f"Selected strategies: {result['active_strategies']}")
        
        return {
            "active_strategies": result["active_strategies"],
            "strategy_reasoning": result["reasoning"],
            "messages": [response],
        }
        
    except Exception as e:
        logger.error(f"Strategy Selection Agent error: {e}")
        # Default to conservative strategies
        return {
            "active_strategies": ["trend_following"],
            "strategy_reasoning": f"Error occurred, defaulting to conservative: {str(e)}",
            "errors": state.get("errors", []) + [f"Strategy Agent: {str(e)}"],
        }


def _build_strategy_context(
    regime: str,
    regime_confidence: float,
    lessons: list[dict[str, Any]],
    daily_stats: dict[str, Any],
) -> str:
    """Build context for strategy selection."""
    
    context_parts = [
        f"## Current Market Regime\n",
        f"- Regime: **{regime}**",
        f"- Confidence: {regime_confidence:.2f}",
        f"\n## Today's Trading Stats\n",
        f"- Trades executed: {daily_stats.get('trades_count', 0)}",
        f"- P&L: {daily_stats.get('profit_loss', 0):.2f}",
    ]
    
    # Historical performance by regime (simplified - would come from DB in production)
    context_parts.append("\n## Historical Strategy Performance by Regime\n")
    performance_data = {
        "trending_up": {"momentum": 0.72, "trend_following": 0.68, "breakout": 0.45, "mean_reversion": 0.35},
        "trending_down": {"momentum": 0.65, "trend_following": 0.62, "breakout": 0.40, "mean_reversion": 0.38},
        "ranging": {"mean_reversion": 0.71, "breakout": 0.55, "momentum": 0.32, "trend_following": 0.28},
        "volatile": {"breakout": 0.48, "momentum": 0.42, "mean_reversion": 0.35, "trend_following": 0.30},
    }
    
    if regime in performance_data:
        for strategy, win_rate in performance_data[regime].items():
            context_parts.append(f"- {strategy}: {win_rate:.0%} win rate")
    
    # Add lessons
    if lessons:
        context_parts.append("\n## Past Mistakes to Avoid\n")
        for lesson in lessons[:3]:
            context_parts.append(
                f"- [{lesson.get('severity', 'N/A')}] {lesson.get('description', 'N/A')}"
            )
    
    return "\n".join(context_parts)


def _parse_strategy_response(content: str) -> dict[str, Any]:
    """Parse strategy selection response."""
    
    try:
        content = content.strip()
        
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        result = json.loads(content)
        
        # Validate strategies
        valid_strategies = ["momentum", "mean_reversion", "breakout", "trend_following"]
        result["active_strategies"] = [
            s for s in result.get("active_strategies", [])
            if s in valid_strategies
        ]
        
        if not result["active_strategies"]:
            result["active_strategies"] = ["trend_following"]
        
        if "reasoning" not in result:
            result["reasoning"] = "No reasoning provided"
        
        return result
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse strategy response: {e}")
        return {
            "active_strategies": ["trend_following"],
            "reasoning": f"Parse error, defaulting to trend_following: {content[:200]}",
        }
