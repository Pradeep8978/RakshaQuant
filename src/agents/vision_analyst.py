"""
Vision Analyst Agent

Captures chart snapshots and uses LLM Vision models to identify geometric patterns.
"""

import logging
import base64
import os
from io import BytesIO
from typing import Any
import plotly.graph_objects as go
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from src.config import get_settings
from src.agents.state import TradingState

logger = logging.getLogger(__name__)

class VisionAnalyst:
    def __init__(self):
        self.settings = get_settings()
        self._llm = None

    def _get_llm(self) -> ChatGroq:
        if self._llm is None:
            self._llm = ChatGroq(
                api_key=self.settings.groq_api_key.get_secret_value(),
                model_name="llama-3.2-11b-vision-pixtral",
                temperature=0.1,
            )
        return self._llm

    def generate_chart_image(self, symbol: str, prices: list[float]) -> str:
        """Generates a base64 encoded PNG of a price chart."""
        try:
            fig = go.Figure(data=[go.Scatter(y=prices, mode='lines+markers', name=symbol)])
            fig.update_layout(
                title=f"Price Action: {symbol}",
                template="plotly_dark",
                margin=dict(l=20, r=20, t=40, b=20),
                height=400,
                width=600
            )
            
            img_bytes = fig.to_image(format="png")
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating chart for {symbol}: {e}")
            return ""

    async def analyze_chart(self, symbol: str, b64_image: str) -> dict[str, Any]:
        """Sends the chart image to Groq-Vision for pattern detection."""
        if not b64_image:
            return {"pattern": "None", "confidence": 0, "reasoning": "No image available"}

        llm = self._get_llm()
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"Analyze this technical chart for {symbol}. Identify any geometric patterns (Support/Resistance, Flags, Head and Shoulders). Return JSON: {{'pattern': string, 'confidence': float (0-1), 'reasoning': string}}"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                },
            ]
        )
        
        try:
            response = await llm.ainvoke([message])
            # Simple extraction (assuming LLM returns JSON or we help it)
            import json
            content = response.content.strip()
            # Basic cleanup if LLM adds markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"Vision analysis failed for {symbol}: {e}")
            return {"pattern": "Error", "confidence": 0, "reasoning": str(e)}

async def vision_analyst_node(state: TradingState) -> dict[str, Any]:
    """LangGraph node for visual chart analysis."""
    logger.info("Running Vision Analyst Agent")
    analyst = VisionAnalyst()
    
    # Analyze signals that passed preliminary validation
    signals = state.get("validated_signals", [])
    if not signals:
        logger.info("No validated signals for vision analysis")
        return {"vision_analysis": {}}

    results = {}
    # analyze up to 3 signals to manage API usage and latency
    for signal in signals[:3]:
        symbol = signal.get("symbol")
        logger.info(f"Visualizing chart for {symbol}")
        
        # Pull history from market data
        market_data = state.get("market_data", {}).get(symbol, {})
        history = market_data.get("history", [])
        
        if not history or len(history) < 10:
            logger.warning(f"Insufficient history for {symbol} vision analysis")
            prices = [float(market_data.get("last_price", 100.0))] * 20
        else:
            prices = [float(p) for p in history]
        
        b64_img = analyst.generate_chart_image(symbol, prices)
        analysis = await analyst.analyze_chart(symbol, b64_img)
        
        results[symbol] = {
            "pattern": analysis.get("pattern"),
            "confidence": analysis.get("confidence"),
            "reasoning": analysis.get("reasoning")
        }
    
    return {"vision_analysis": results}
