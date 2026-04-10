import React from 'react';
import { Clock } from 'lucide-react';
import { Trade } from '../types';

interface RecentTradesProps {
  trades: Trade[];
}

export function RecentTrades({ trades }: RecentTradesProps) {
  return (
    <div className="glass-panel">
      <h2 className="section-title">
        <Clock size={20} color="var(--accent)" />
        Recent Execution
      </h2>
      <div className="activity-feed" style={{ maxHeight: '200px' }}>
        {trades.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '1rem' }}>
            No trades executed yet
          </div>
        ) : (
          trades.map(trade => (
            <div key={trade.trade_id} className="trade-item">
              <div className="trade-info">
                <div className="trade-symbol">{trade.symbol}</div>
                <div className="trade-time">
                  {new Date(trade.entry_time).toLocaleTimeString()}
                </div>
              </div>
              <div className="trade-result">
                <span className={`trade-action ${trade.side === 'BUY' ? 'action-buy' : 'action-sell'}`}>
                  {trade.side}
                </span>
                {trade.profit_loss !== null && (
                  <span style={{ color: trade.profit_loss >= 0 ? 'var(--success)' : 'var(--danger)', fontSize: '0.9rem', fontWeight: 600 }}>
                    {trade.profit_loss >= 0 ? '+' : ''}₹{trade.profit_loss.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
