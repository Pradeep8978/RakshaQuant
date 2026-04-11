import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .state import TradingState

logger = logging.getLogger(__name__)

class VolumeAnalyst:
    """
    Identifies institutional footprints using Volume Profile, 
    Point of Control (POC), and Value Areas.
    """
    
    def __init__(self, n_bins: int = 24):
        self.n_bins = n_bins

    def analyze(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform Volume Profile analysis on the given symbol's data.
        """
        try:
            if df.empty or len(df) < 20:
                return {"symbol": symbol, "error": "Insufficient data"}

            # Get latest 100 bars for profile
            recent_df = df.tail(100).copy()
            
            # 1. Calculate Volume Profile
            price_min = recent_df['close'].min()
            price_max = recent_df['close'].max()
            
            if price_min == price_max:
                return {"symbol": symbol, "error": "No price movement"}
                
            bins = np.linspace(price_min, price_max, self.n_bins + 1)
            recent_df['bin'] = pd.cut(recent_df['close'], bins=bins, include_lowest=True)
            
            volume_profile = recent_df.groupby('bin', observed=False)['volume'].sum()
            
            # 2. Identify POC (Point of Control)
            poc_bin = volume_profile.idxmax()
            poc_price = (poc_bin.left + poc_bin.right) / 2
            
            # 3. Value Area (70% of volume)
            total_volume = volume_profile.sum()
            sorted_profile = volume_profile.sort_values(ascending=False)
            cumulative_volume = sorted_profile.cumsum()
            value_area_bins = sorted_profile[cumulative_volume <= total_volume * 0.7].index
            
            if len(value_area_bins) > 0:
                vah = max([b.right for b in value_area_bins])
                val = min([b.left for b in value_area_bins])
            else:
                vah = price_max
                val = price_min

            # 4. Institutional Activity Detection
            # Look for volume spikes (> 2 std devs) on price consolidation
            avg_vol = df['volume'].rolling(20).mean().iloc[-1]
            std_vol = df['volume'].rolling(20).std().iloc[-1]
            last_vol = df['volume'].iloc[-1]
            
            activity_label = "Neutral"
            intensity = 0.0
            
            if last_vol > avg_vol + (2 * std_vol):
                last_close = df['close'].iloc[-1]
                last_open = df['open'].iloc[-1]
                
                if last_close > last_open:
                    activity_label = "Institutional Accumulation"
                    intensity = float((last_vol - avg_vol) / std_vol)
                else:
                    activity_label = "Institutional Distribution"
                    intensity = float((last_vol - avg_vol) / std_vol)

            # 5. Trend vs Volume Divergence
            price_change = df['close'].pct_change(5).iloc[-1]
            vol_change = df['volume'].pct_change(5).iloc[-1]
            
            divergence = "None"
            if price_change > 0 and vol_change < -0.2:
                divergence = "Bearish (Price up, Volume down)"
            elif price_change < 0 and vol_change < -0.2:
                divergence = "Weakening (Price down, Volume down)"

            return {
                "symbol": symbol,
                "poc": round(float(poc_price), 2),
                "vah": round(float(vah), 2),
                "val": round(float(val), 2),
                "current_price": round(float(df['close'].iloc[-1]), 2),
                "position_relative_to_poc": "Above" if df['close'].iloc[-1] > poc_price else "Below",
                "institutional_activity": activity_label,
                "activity_intensity": round(float(intensity), 2),
                "divergence": divergence,
                "summary": f"{activity_label} detected at {round(float(poc_price), 2)} POC bar."
            }
            
        except Exception as e:
            logger.error(f"Error in volume analysis for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}

def volume_analyst_node(state: TradingState) -> Dict[str, Any]:
    """
    LangGraph node for Institutional Footprint analysis.
    """
    logger.info("--- VOLUMETRIC FOOTPRINT ANALYSIS ---")
    
    market_data = state.get("market_data", {})
    validated_signals = state.get("validated_signals", [])
    
    if not validated_signals:
        return {"volume_analysis": {}}

    analyst = VolumeAnalyst()
    results = {}
    
    # Analyze symbols that passed validation
    for signal in validated_signals:
        symbol = signal.get("symbol")
        if symbol in market_data:
            df = market_data[symbol]
            analysis = analyst.analyze(symbol, df)
            results[symbol] = analysis
            
    return {"volume_analysis": results}
