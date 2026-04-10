export interface SummaryData {
  balance: number;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  open_positions: number;
  realized_pnl: number;
  unrealized_pnl: number;
  return_pct: number;
  latest_regime: string;
  regime_confidence: number;
  active_strategies: string[];
  is_halted?: boolean;
  latest_vision?: Record<string, {
    symbol: string;
    pattern: string;
    confidence: number;
    reasoning: string;
  }>;
  latest_volume?: Record<string, {
    symbol: string;
    poc: number;
    vah: number;
    val: number;
    institutional_activity: string;
    activity_intensity: number;
    divergence: string;
    summary: string;
  }>;
  latest_news?: {
    avg_sentiment: number;
    sentiment_label: string;
    headlines: string[];
  };
}

export interface Trade {
  trade_id: string;
  symbol: string;
  side: string;
  profit_loss: number | null;
  entry_time: string;
}

export interface Position {
  position_id: string;
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  entry_time: string;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export interface Lesson {
  lesson_id: string;
  category: string;
  severity: string;
  lesson: string;
  description: string;
}

export interface ChartDataPoint {
  time: string;
  balance: number;
}
