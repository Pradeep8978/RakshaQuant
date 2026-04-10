import { ExternalLink, Clock } from 'lucide-react';
import { Trade } from '../types';

interface RecentTradesProps {
  trades: Trade[];
}

export function RecentTrades({ trades }: RecentTradesProps) {
  return (
    <div className="glass-panel">
      <h2 className="text-xl mb-5 text-primary flex items-center gap-2">
        <Clock size={20} />
        Recent Executions
      </h2>
      
      {trades.length === 0 ? (
        <div className="text-secondary p-4 text-center border border-white/5 rounded-lg">
          No trades logged in the current session.
        </div>
      ) : (
        <div className="flex flex-col gap-4 max-h-[500px] overflow-y-auto pr-2 activity-feed">
          {trades.map((t, i) => (
            <div key={i} className="flex justify-between items-center p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition-colors">
              <div className="flex flex-col gap-1">
                <span className="font-semibold text-lg hover:text-accent cursor-pointer transition-colors flex items-center gap-1">
                  {t.symbol} <ExternalLink size={12} />
                </span>
                <span className="text-secondary text-sm">
                  {new Date(t.entry_time).toLocaleTimeString()}
                </span>
              </div>
              
              <div className="flex items-center gap-4">
                <span className={`font-semibold text-sm px-2 py-1 rounded-md ${
                  t.side.toUpperCase() === 'BUY' 
                    ? 'bg-emerald-500/15 text-emerald-500' 
                    : 'bg-red-500/15 text-red-500'
                }`}>
                  {t.side.toUpperCase()}
                </span>
                
                {t.profit_loss !== null && (
                  <div className="text-right flex flex-col gap-1">
                    <span className={`font-bold ${t.profit_loss >= 0 ? 'text-success' : 'text-danger'}`}>
                      {t.profit_loss >= 0 ? '+' : ''}₹{t.profit_loss.toFixed(2)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
