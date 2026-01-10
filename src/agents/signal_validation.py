"""
Signal Validation Agent Module

Validates raw trading signals using context, memory lessons, and LLM reasoning.
Acts as a filter between raw signals and risk management.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from src.config import get_settings
from .state import TradingState

logger = logging.getLogger(__name__)


VALIDATION_SYSTEM_PROMPT = """You are a Signal Validation Agent for an automated trading system.

Your role is to evaluate raw trading signals and decide whether to approve or reject them.
You are the quality control layer before trades go to risk management.

For each signal, consider:
1. Does the signal align with the current market regime?
2. Is the signal from an active strategy (selected by Strategy Agent)?
3. Does the signal have sufficient confidence and risk-reward ratio?
4. Are there memory lessons warning against similar trades?
5. Is the timing appropriate (not chasing, not against major trend)?

You will receive:
- Current market regime and confidence
- Active strategies list
- Raw signals with their details
- Relevant memory lessons

For EACH signal, respond with JSON:
{
    "validations": [
        {
            "signal_id": "the signal ID",
            "decision": "approve" or "reject",
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation",
            "modifications": {
                "stop_loss": optional new value,
                "target_price": optional new value,
                "position_size_pct": optional new value
            }
        }
    ]
}

Be selective - it's better to miss a trade than take a bad one.
Quality over quantity."""


def create_validation_agent() -> ChatGroq:
    """Create the signal validation agent."""
    settings = get_settings()
    
    return ChatGroq(
        api_key=settings.groq_api_key.get_secret_value(),
        model_name=settings.groq_model_primary,
        temperature=settings.groq_temperature,
        max_tokens=2048,
    )


def signal_validation_node(state: TradingState) -> dict[str, Any]:
    """
    LangGraph node for signal validation.
    
    Validates raw signals and filters out low-quality opportunities.
    
    Args:
        state: Current trading state with signals and context
        
    Returns:
        State updates with validated and rejected signals
    """
    logger.info("Running Signal Validation Agent...")
    
    try:
        signals = state.get("signals", [])
        
        if not signals:
            logger.info("No signals to validate")
            return {
                "validated_signals": [],
                "rejected_signals": [],
            }
        
        regime = state.get("regime", "unknown")
        regime_confidence = state.get("regime_confidence", 0.0)
        active_strategies = state.get("active_strategies", [])
        memory_lessons = state.get("memory_lessons", [])
        
        # Filter relevant lessons
        timing_lessons = [
            lesson for lesson in memory_lessons
            if lesson.get("category") in ["poor_timing", "signal_quality"]
        ]
        
        # Build context
        context = _build_validation_context(
            signals, regime, regime_confidence, active_strategies, timing_lessons
        )
        
        # Create and run agent
        agent = create_validation_agent()
        
        messages = [
            SystemMessage(content=VALIDATION_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ]
        
        response = agent.invoke(messages)
        result = _parse_validation_response(response.content, signals)
        
        validated = result["validated"]
        rejected = result["rejected"]
        
        logger.info(f"Validated: {len(validated)}, Rejected: {len(rejected)}")
        
        return {
            "validated_signals": validated,
            "rejected_signals": rejected,
            "messages": [response],
        }
        
    except Exception as e:
        logger.error(f"Signal Validation Agent error: {e}")
        # Reject all signals on error (safety first)
        return {
            "validated_signals": [],
            "rejected_signals": state.get("signals", []),
            "errors": state.get("errors", []) + [f"Validation Agent: {str(e)}"],
        }


def _build_validation_context(
    signals: list[dict[str, Any]],
    regime: str,
    regime_confidence: float,
    active_strategies: list[str],
    lessons: list[dict[str, Any]],
) -> str:
    """Build context for signal validation."""
    
    context_parts = [
        "## Current Context\n",
        f"- Market Regime: **{regime}** (confidence: {regime_confidence:.2f})",
        f"- Active Strategies: {', '.join(active_strategies) or 'None'}",
    ]
    
    # Add signals
    context_parts.append(f"\n## Signals to Validate ({len(signals)} total)\n")
    
    for signal in signals:
        context_parts.append(f"\n### Signal: {signal.get('signal_id', 'N/A')}")
        context_parts.append(f"- Symbol: {signal.get('symbol', 'N/A')}")
        context_parts.append(f"- Type: {signal.get('signal_type', 'N/A')}")
        context_parts.append(f"- Strategy: {signal.get('strategy', 'N/A')}")
        context_parts.append(f"- Strength: {signal.get('strength', 'N/A')}")
        context_parts.append(f"- Confidence: {signal.get('confidence', 0):.2f}")
        context_parts.append(f"- Entry: {signal.get('entry_price', 0):.2f}")
        context_parts.append(f"- Stop Loss: {signal.get('stop_loss', 0):.2f}")
        context_parts.append(f"- Target: {signal.get('target_price', 0):.2f}")
        context_parts.append(f"- R:R Ratio: {signal.get('risk_reward_ratio', 0):.2f}")
        context_parts.append(f"- Position Size: {signal.get('position_size_pct', 0):.1f}%")
        
        if signal.get("reasons"):
            context_parts.append(f"- Reasons: {'; '.join(signal['reasons'][:3])}")
    
    # Add lessons
    if lessons:
        context_parts.append("\n## Past Lessons (Consider Carefully)\n")
        for lesson in lessons[:5]:
            context_parts.append(
                f"- [{lesson.get('severity', 'N/A')}] {lesson.get('description', 'N/A')}"
            )
    
    return "\n".join(context_parts)


def _parse_validation_response(
    content: str,
    original_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Parse validation response and categorize signals."""
    
    validated = []
    rejected = []
    
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
        validations = result.get("validations", [])
        
        # Create lookup for original signals
        signal_lookup = {s.get("signal_id"): s for s in original_signals}
        
        for validation in validations:
            signal_id = validation.get("signal_id")
            decision = validation.get("decision", "reject")
            
            if signal_id in signal_lookup:
                signal = signal_lookup[signal_id].copy()
                signal["validation"] = validation
                
                # Apply modifications if approved
                if decision == "approve":
                    mods = validation.get("modifications", {})
                    if mods.get("stop_loss"):
                        signal["stop_loss"] = mods["stop_loss"]
                    if mods.get("target_price"):
                        signal["target_price"] = mods["target_price"]
                    if mods.get("position_size_pct"):
                        signal["position_size_pct"] = mods["position_size_pct"]
                    validated.append(signal)
                else:
                    rejected.append(signal)
        
        # Any signals not in response are rejected
        processed_ids = {v.get("signal_id") for v in validations}
        for signal in original_signals:
            if signal.get("signal_id") not in processed_ids:
                signal["validation"] = {"decision": "reject", "reasoning": "Not processed"}
                rejected.append(signal)
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse validation response: {e}")
        # Reject all on parse error
        for signal in original_signals:
            signal["validation"] = {"decision": "reject", "reasoning": "Parse error"}
            rejected.append(signal)
    
    return {"validated": validated, "rejected": rejected}
