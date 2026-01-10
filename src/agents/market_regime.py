"""
Market Regime Agent Module

Classifies the current market regime based on volatility, trend, and market conditions.
Runs on a slow cadence and provides context for strategy selection.
"""

import json
import logging
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import get_settings
from .state import MarketRegime, TradingState

logger = logging.getLogger(__name__)


REGIME_SYSTEM_PROMPT = """You are a Market Regime Classification Agent for an automated trading system.

Your role is to analyze market conditions and classify the current regime into one of these categories:
- trending_up: Strong bullish trend with consistent higher highs and higher lows
- trending_down: Strong bearish trend with consistent lower highs and lower lows  
- ranging: Price moving sideways within a defined range, no clear trend
- volatile: High volatility with erratic price movements, uncertain direction

You will receive:
1. Market indicators (ADX, RSI, volatility metrics, moving averages)
2. Recent price action summary
3. Any relevant memory lessons from past regime misclassifications

Respond with a JSON object containing:
{
    "regime": "one of: trending_up, trending_down, ranging, volatile",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this regime was chosen",
    "key_factors": ["list", "of", "key", "indicators", "considered"]
}

Be conservative - if unsure, prefer "ranging" or lower confidence scores.
Consider the memory lessons carefully to avoid past mistakes."""


def create_regime_agent() -> ChatGroq:
    """Create the market regime classification agent."""
    settings = get_settings()
    
    return ChatGroq(
        api_key=settings.groq_api_key.get_secret_value(),
        model_name=settings.groq_model_primary,
        temperature=settings.groq_temperature,
        max_tokens=1024,
    )


def market_regime_node(state: TradingState) -> dict[str, Any]:
    """
    LangGraph node for market regime classification.
    
    Analyzes current market conditions and classifies the regime.
    
    Args:
        state: Current trading state with market data and indicators
        
    Returns:
        State updates with regime classification
    """
    logger.info("Running Market Regime Agent...")
    
    try:
        # Extract relevant data for regime analysis
        indicators = state.get("indicators", {})
        market_data = state.get("market_data", {})
        memory_lessons = state.get("memory_lessons", [])
        
        # Filter lessons relevant to regime classification
        regime_lessons = [
            lesson for lesson in memory_lessons
            if lesson.get("category") == "regime_mismatch"
        ]
        
        # Build context for the agent
        context = _build_regime_context(indicators, market_data, regime_lessons)
        
        messages = [
            SystemMessage(content=REGIME_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]
        
        # Try primary model first, fallback on rate limit
        settings = get_settings()
        models_to_try = [settings.groq_model_primary, settings.groq_model_fallback]
        
        response = None
        for model_name in models_to_try:
            try:
                agent = ChatGroq(
                    api_key=settings.groq_api_key.get_secret_value(),
                    model_name=model_name,
                    temperature=settings.groq_temperature,
                    max_tokens=1024,
                )
                response = agent.invoke(messages)
                logger.info(f"Regime agent using model: {model_name}")
                break
            except Exception as model_error:
                if "rate_limit" in str(model_error).lower() or "429" in str(model_error):
                    logger.warning(f"Rate limit on {model_name}, trying fallback...")
                    continue
                raise model_error
        
        if response is None:
            raise Exception("All models rate limited")
        
        # Parse response
        result = _parse_regime_response(response.content)
        
        logger.info(f"Regime classified as: {result['regime']} (confidence: {result['confidence']:.2f})")
        
        return {
            "regime": result["regime"],
            "regime_confidence": result["confidence"],
            "regime_reasoning": result["reasoning"],
            "messages": [response],
        }
        
    except Exception as e:
        logger.error(f"Market Regime Agent error: {e}")
        # Return a default trending regime based on market data
        market_data = state.get("market_data", {})
        avg_change = 0.0
        for data in market_data.values():
            if isinstance(data, dict):
                avg_change += data.get("change_percent", 0)
        if market_data:
            avg_change /= len(market_data)
        
        # Infer regime from average market change
        if avg_change > 0.5:
            regime = "trending_up"
            confidence = 0.5
        elif avg_change < -0.5:
            regime = "trending_down"
            confidence = 0.5
        else:
            regime = "ranging"
            confidence = 0.4
            
        logger.info(f"Using fallback regime: {regime} (inferred from avg change: {avg_change:.2f}%)")
        
        return {
            "regime": regime,
            "regime_confidence": confidence,
            "regime_reasoning": f"Fallback: Inferred from average market change ({avg_change:.2f}%)",
            "errors": state.get("errors", []) + [f"Regime Agent fallback: {str(e)}"],
        }


def _build_regime_context(
    indicators: dict[str, Any],
    market_data: dict[str, Any],
    lessons: list[dict[str, Any]],
) -> str:
    """Build context string for regime classification."""
    
    context_parts = ["## Current Market Analysis\n"]
    
    # Add indicator summary
    if indicators:
        context_parts.append("### Technical Indicators\n")
        for symbol, ind in indicators.items():
            context_parts.append(f"\n**{symbol}**:")
            
            # Trend indicators
            if "trend" in ind:
                trend = ind["trend"]
                context_parts.append(f"- ADX: {trend.get('adx', 'N/A')}")
                context_parts.append(f"- +DI: {trend.get('plus_di', 'N/A')}, -DI: {trend.get('minus_di', 'N/A')}")
            
            # Momentum
            if "momentum" in ind:
                mom = ind["momentum"]
                context_parts.append(f"- RSI: {mom.get('rsi', 'N/A')}")
            
            # Moving averages
            if "moving_averages" in ind:
                ma = ind["moving_averages"]
                if "sma" in ma:
                    sma_str = ", ".join([f"SMA{k}={v:.2f}" for k, v in ma["sma"].items()])
                    context_parts.append(f"- {sma_str}")
            
            # Volatility
            if "volatility" in ind:
                vol = ind["volatility"]
                context_parts.append(f"- ATR: {vol.get('atr', 'N/A')}")
                context_parts.append(f"- BB Width: {vol.get('bb_percent', 'N/A')}")
    
    # Add price summary
    if market_data:
        context_parts.append("\n### Price Summary\n")
        for symbol, data in market_data.items():
            if isinstance(data, dict):
                context_parts.append(
                    f"- {symbol}: Close={data.get('close', 'N/A')}, "
                    f"Change={data.get('change_percent', 'N/A')}%"
                )
    
    # Add memory lessons
    if lessons:
        context_parts.append("\n### Past Lessons (Avoid These Mistakes)\n")
        for lesson in lessons[:3]:  # Top 3 most relevant
            context_parts.append(
                f"- [{lesson.get('severity', 'N/A')}] {lesson.get('description', 'N/A')}"
            )
    
    return "\n".join(context_parts)


def _parse_regime_response(content: str) -> dict[str, Any]:
    """Parse the agent's JSON response."""
    
    try:
        # Try to extract JSON from the response
        content = content.strip()
        
        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        result = json.loads(content)
        
        # Validate regime value
        valid_regimes = [r.value for r in MarketRegime]
        if result.get("regime") not in valid_regimes:
            result["regime"] = MarketRegime.UNKNOWN.value
        
        # Ensure confidence is in range
        confidence = float(result.get("confidence", 0.5))
        result["confidence"] = max(0.0, min(1.0, confidence))
        
        # Ensure reasoning exists
        if "reasoning" not in result:
            result["reasoning"] = "No reasoning provided"
        
        return result
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse regime response as JSON: {e}")
        return {
            "regime": MarketRegime.UNKNOWN.value,
            "confidence": 0.0,
            "reasoning": f"Failed to parse response: {content[:200]}",
        }
