import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Info } from 'lucide-react';
import { SummaryData } from '../types';

interface MarketTickerProps {
  summary: SummaryData;
}

export function MarketTicker({ summary }: MarketTickerProps) {
  const mood = summary.market_mood || { score: 50, label: 'Neutral', description: 'Detecting mood...' };
  
  const [indices, setIndices] = useState([
    { name: 'NIFTY 50', price: '22,453.30', change: '+0.85%', up: true },
    { name: 'BANK NIFTY', price: '48,125.10', change: '+1.12%', up: true },
  ]);

  return (
    <div className="bg-slate-950 border-b border-white/5 overflow-hidden whitespace-nowrap py-1.5 select-none">
      <div className="flex animate-marquee items-center gap-8">
        {/* Market Mood Indicator */}
        <div className="inline-flex items-center gap-3 px-8 border-r border-white/10 h-full bg-accent/5">
          <span className="text-[10px] font-bold text-accent uppercase tracking-[0.2em] animate-pulse">Live Market Mood</span>
          <div className="h-4 w-px bg-white/10" />
          <span className="text-xs font-mono text-white font-bold">{mood.score}</span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
            mood.score > 60 ? 'bg-emerald-500/20 text-emerald-400' : 
            mood.score < 40 ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
          }`}>
            {mood.label}
          </span>
          <span className="text-[10px] text-slate-400 italic font-medium">"{mood.description}"</span>
        </div>

        {/* Existing Indices */}
        {[...indices, ...indices].map((idx, i) => (
          <div key={i} className="inline-flex items-center gap-3 px-8 border-r border-white/5 h-full opacity-60 hover:opacity-100 transition-opacity">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{idx.name}</span>
            <span className="text-xs font-mono text-white font-semibold">{idx.price}</span>
            <span className={`text-[10px] font-bold flex items-center gap-0.5 ${idx.up ? 'text-emerald-400' : 'text-rose-400'}`}>
              {idx.up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              {idx.change}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
