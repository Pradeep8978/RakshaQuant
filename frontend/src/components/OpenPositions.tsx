import { LayoutList, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Position } from '../types';

interface OpenPositionsProps {
  positions: Position[];
}

export function OpenPositions({ positions }: OpenPositionsProps) {
  return (
    <div className="glass-panel">
      <h2 className="text-xl mb-5 text-primary flex items-center gap-2">
        <LayoutList size={20} className="text-accent" />
        Open Positions
      </h2>

      {positions.length === 0 ? (
        <div className="text-secondary p-8 text-center border border-white/5 border-dashed rounded-xl">
          No open positions. RakshaQuant is currently flat.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-secondary uppercase border-b border-white/5">
              <tr>
                <th className="pb-3 pr-4">Symbol</th>
                <th className="pb-3 px-4 text-center">Qty</th>
                <th className="pb-3 px-4 text-right">Entry</th>
                <th className="pb-3 px-4 text-right">CMP</th>
                <th className="pb-3 pl-4 text-right">Unrealized P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {positions.map((pos) => (
                <tr key={pos.position_id} className="group hover:bg-white/5 transition-colors">
                  <td className="py-4 pr-4 font-semibold text-primary">
                    <div className="flex flex-col">
                      <span>{pos.symbol}</span>
                      <span className={`text-[10px] w-fit px-1.5 rounded ${pos.side === 'BUY' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                        {pos.side}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center text-secondary font-mono">{pos.quantity}</td>
                  <td className="py-4 px-4 text-right text-secondary font-mono">₹{pos.entry_price.toLocaleString()}</td>
                  <td className="py-4 px-4 text-right text-primary font-mono">₹{pos.current_price.toLocaleString()}</td>
                  <td className={`py-4 pl-4 text-right font-bold font-mono ${pos.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                    <div className="flex items-center justify-end gap-1">
                      {pos.unrealized_pnl >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      ₹{Math.abs(pos.unrealized_pnl).toLocaleString()}
                      <span className="text-[10px] ml-1 opacity-70">({pos.unrealized_pnl_pct.toFixed(2)}%)</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
