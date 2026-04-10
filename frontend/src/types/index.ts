export interface SummaryData {
  balance: number;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  open_positions: number;
  is_halted?: boolean;
}

export interface Trade {
  trade_id: string;
  symbol: string;
  side: string;
  profit_loss: number | null;
  entry_time: string;
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
