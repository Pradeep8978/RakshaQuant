import { ShieldCheck, TrendingDown, Percent, BarChart3 } from 'lucide-react';
import { SummaryData } from '../types';

interface RiskMetricsProps {
  summary: SummaryData;
}

export function RiskMetrics({ summary }: RiskMetricsProps) {
  // Mocking some advanced metrics for now, but connecting real P&L
  const profitFactor = summary.total_trades > 0 ? (summary.win_rate / (100 - summary.win_rate + 0.1) * 1.2).toFixed(2) : "0.00";
  const maxDrawdown = "-2.4%"; // This would eventually come from the backend

  return (
    <div className="glass-panel">
      <h2 className="text-xl mb-5 text-primary flex items-center gap-2">
        <ShieldCheck size={20} className="text-accent" />
        Advanced Risk Metrics
      </h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white/5 border border-white/5 p-4 rounded-xl flex flex-col gap-1">
          <span className="text-secondary text-xs uppercase tracking-tighter flex items-center gap-1">
            <BarChart3 size={12} /> Profit Factor
          </span>
          <span className="text-2xl font-bold text-primary">{profitFactor}</span>
        </div>

        <div className="bg-white/5 border border-white/5 p-4 rounded-xl flex flex-col gap-1">
          <span className="text-secondary text-xs uppercase tracking-tighter flex items-center gap-1">
            <TrendingDown size={12} /> Max Drawdown
          </span>
          <span className="text-2xl font-bold text-danger">{maxDrawdown}</span>
        </div>

        <div className="bg-white/5 border border-white/5 p-4 rounded-xl flex flex-col gap-1">
          <span className="text-secondary text-xs uppercase tracking-tighter flex items-center gap-1">
            <Percent size={12} /> Return (Session)
          </span>
          <span className={`text-2xl font-bold ${summary.return_pct >= 0 ? 'text-success' : 'text-danger'}`}>
            {summary.return_pct >= 0 ? '+' : ''}{summary.return_pct.toFixed(2)}%
          </span>
        </div>

        <div className="bg-white/5 border border-white/5 p-4 rounded-xl flex flex-col gap-1">
          <span className="text-secondary text-xs uppercase tracking-tighter flex items-center gap-1">
            <ShieldCheck size={12} /> Sharpe Ratio
          </span>
          <span className="text-2xl font-bold text-primary">1.82</span>
        </div>
      </div>

      <div className="mt-6">
        <div className="flex justify-between text-xs text-secondary mb-2">
          <span>Daily Risk Limit Progress</span>
          <span>42% Used</span>
        </div>
        <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
          <div className="bg-accent h-full w-[42%] shadow-[0_0_10px_var(--color-accent)]"></div>
        </div>
      </div>
    </div>
  );
}
