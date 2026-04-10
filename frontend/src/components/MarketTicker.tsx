import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function MarketTicker() {
  // In a real scenario, this would come from the MarketDataManager through the API
  const [indices, setIndices] = useState([
    { name: 'NIFTY 50', price: '22,453.30', change: '+0.85%', up: true },
    { name: 'BANK NIFTY', price: '48,125.10', change: '+1.12%', up: true },
    { name: 'RELIANCE', price: '2,945.00', change: '-0.24%', up: false },
    { name: 'TCS', price: '3,892.40', change: '+0.45%', up: true },
    { name: 'INR/USD', price: '83.42', change: '-0.02%', up: false },
  ]);

  return (
    <div className="bg-panel border-b border-panel-border overflow-hidden whitespace-nowrap py-1.5 select-none">
      <div className="flex animate-marquee items-center">
        {[...indices, ...indices].map((idx, i) => (
          <div key={i} className="inline-flex items-center gap-3 px-8 border-r border-white/5 h-full">
            <span className="text-xs font-bold text-secondary uppercase tracking-wider">{idx.name}</span>
            <span className="text-xs font-mono text-primary font-semibold">{idx.price}</span>
            <span className={`text-[10px] font-bold flex items-center gap-0.5 ${idx.up ? 'text-success' : 'text-danger'}`}>
              {idx.up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              {idx.change}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
