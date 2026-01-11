"""
Price Prediction Agent

Uses simple machine learning to predict next candle direction.
Based on Linear Regression on recent OHLC data.

Features:
- Direction prediction (up/down)
- Confidence scoring
- Historical pattern analysis
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    LinearRegression = None
    StandardScaler = None

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PredictionSignal:
    """Price prediction signal."""
    
    symbol: str
    direction: str  # "up" or "down"
    confidence: float  # 0-1
    predicted_change_pct: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "confidence": self.confidence,
            "predicted_change_pct": self.predicted_change_pct,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


class PredictionAgent:
    """
    Predicts price direction using simple ML.
    
    Uses Linear Regression on recent price data to predict next movement.
    """
    
    def __init__(self, lookback_periods: int = 20):
        """
        Initialize prediction agent.
        
        Args:
            lookback_periods: Number of candles to use for prediction
        """
        self.lookback = lookback_periods
        self.settings = get_settings()
    
    def _create_features(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """
        Create features from OHLCV data for ML.
        
        Features:
        - Price changes (returns)
        - Moving average ratios
        - Volume changes
        """
        if len(df) < self.lookback + 5:
            return None, None
        
        # Calculate features
        df = df.copy()
        df["returns"] = df["Close"].pct_change()
        df["sma_5"] = df["Close"].rolling(5).mean()
        df["sma_10"] = df["Close"].rolling(10).mean()
        df["sma_ratio"] = df["sma_5"] / df["sma_10"]
        df["vol_change"] = df["Volume"].pct_change()
        df["high_low_range"] = (df["High"] - df["Low"]) / df["Close"]
        
        # Target: next day return direction
        df["target"] = df["returns"].shift(-1)
        
        # Drop NaN
        df = df.dropna()
        
        if len(df) < 10:
            return None, None
        
        # Feature columns
        feature_cols = ["returns", "sma_ratio", "vol_change", "high_low_range"]
        X = df[feature_cols].values
        y = df["target"].values
        
        return X, y
    
    def predict(
        self,
        historical_data: pd.DataFrame | dict[str, Any],
        symbol: str = "UNKNOWN",
    ) -> PredictionSignal:
        """
        Predict next candle direction.
        
        Args:
            historical_data: DataFrame with OHLCV columns or dict
            symbol: Stock symbol
            
        Returns:
            PredictionSignal with direction and confidence
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, using fallback prediction")
            return self._fallback_predict(historical_data, symbol)
        
        try:
            # Convert dict to DataFrame if needed
            if isinstance(historical_data, dict):
                df = pd.DataFrame(historical_data)
            else:
                df = historical_data.copy()
            
            # Ensure required columns
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing columns for {symbol}, using fallback")
                return self._fallback_predict(historical_data, symbol)
            
            # Create features
            X, y = self._create_features(df)
            
            if X is None or len(X) < 10:
                logger.warning(f"Insufficient data for {symbol}, using fallback")
                return self._fallback_predict(historical_data, symbol)
            
            # Train/test split (use last 5 for validation)
            X_train, y_train = X[:-5], y[:-5]
            X_test, y_test = X[-5:], y[-5:]
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # Predict on last data point
            last_features = X[-1:].reshape(1, -1)
            last_scaled = scaler.transform(last_features)
            prediction = model.predict(last_scaled)[0]
            
            # Calculate confidence from R² on test set
            r2 = model.score(X_test_scaled, y_test)
            confidence = max(0.3, min(0.9, r2 + 0.3))  # Clamp between 0.3 and 0.9
            
            # Determine direction
            direction = "up" if prediction > 0 else "down"
            
            # Build reasoning
            recent_returns = df["Close"].pct_change().tail(5).mean() * 100
            trend = "upward" if recent_returns > 0 else "downward"
            
            reasoning = (
                f"Based on {len(X)} historical patterns. "
                f"Recent trend: {trend} ({recent_returns:+.2f}% avg). "
                f"Model predicts {abs(prediction)*100:.2f}% move {direction}."
            )
            
            logger.info(f"Prediction for {symbol}: {direction} ({confidence:.1%} confidence)")
            
            return PredictionSignal(
                symbol=symbol,
                direction=direction,
                confidence=confidence,
                predicted_change_pct=prediction * 100,
                reasoning=reasoning,
            )
            
        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            return self._fallback_predict(historical_data, symbol)
    
    def _fallback_predict(
        self,
        data: Any,
        symbol: str,
    ) -> PredictionSignal:
        """Fallback prediction using simple momentum."""
        try:
            if isinstance(data, pd.DataFrame) and "Close" in data.columns:
                recent_change = data["Close"].pct_change().tail(3).mean()
            elif isinstance(data, dict) and "close" in data:
                closes = data["close"]
                if len(closes) >= 3:
                    recent_change = (closes[-1] - closes[-3]) / closes[-3]
                else:
                    recent_change = 0
            else:
                recent_change = 0
        except:
            recent_change = 0
        
        direction = "up" if recent_change > 0 else "down"
        
        return PredictionSignal(
            symbol=symbol,
            direction=direction,
            confidence=0.4,  # Low confidence for fallback
            predicted_change_pct=recent_change * 100,
            reasoning=f"Fallback momentum prediction based on recent trend ({recent_change*100:+.2f}%)",
        )


def prediction_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph node for price prediction.
    
    Generates prediction signals for validated signals.
    """
    agent = PredictionAgent()
    
    # Get historical data from market data manager (if available)
    from src.market.yfinance_feed import YFinanceFeed
    
    validated_signals = state.get("validated_signals", [])
    predictions = []
    
    for signal in validated_signals[:3]:  # Limit to top 3
        symbol = signal.get("symbol", "")
        if not symbol:
            continue
        
        try:
            # Fetch historical data
            feed = YFinanceFeed(symbols=[symbol])
            hist = feed.get_historical(symbol, period="1mo")
            
            if hist is not None and not hist.empty:
                pred = agent.predict(hist, symbol)
                predictions.append(pred.to_dict())
        except Exception as e:
            logger.warning(f"Could not generate prediction for {symbol}: {e}")
    
    return {
        "prediction_signals": predictions,
    }


def test_prediction_agent():
    """Test the prediction agent."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("[PREDICTION] RakshaQuant - Price Prediction Test")
    print("=" * 60)
    
    agent = PredictionAgent()
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    
    # Simulate uptrend
    base_price = 100
    prices = [base_price]
    for i in range(49):
        change = np.random.normal(0.002, 0.02)
        prices.append(prices[-1] * (1 + change))
    
    df = pd.DataFrame({
        "Open": [p * 0.999 for p in prices],
        "High": [p * 1.01 for p in prices],
        "Low": [p * 0.99 for p in prices],
        "Close": prices,
        "Volume": np.random.randint(100000, 1000000, 50),
    }, index=dates)
    
    print("\n[DATA] Generated sample data:")
    print(f"  Start price: ₹{prices[0]:.2f}")
    print(f"  End price: ₹{prices[-1]:.2f}")
    print(f"  Total return: {(prices[-1]/prices[0]-1)*100:.2f}%")
    
    print("\n[PREDICT] Running prediction...")
    prediction = agent.predict(df, "SAMPLE")
    
    print(f"\n  Direction: {prediction.direction.upper()}")
    print(f"  Confidence: {prediction.confidence:.1%}")
    print(f"  Predicted change: {prediction.predicted_change_pct:+.2f}%")
    print(f"  Reasoning: {prediction.reasoning}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Prediction agent working!")
    print("=" * 60)


if __name__ == "__main__":
    test_prediction_agent()
