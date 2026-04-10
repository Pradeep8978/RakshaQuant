import { Activity, TrendingUp, Wallet, Target, ArrowUpRight, ArrowDownRight, Minus, LayoutDashboard, History, Brain, ShieldAlert, BarChart3 } from 'lucide-react';
import { useState } from 'react';
import { useDashboardData } from './hooks/useDashboardData';
import { Header } from './components/Header';
import { StatCard } from './components/StatCard';
import { PerformanceChart } from './components/PerformanceChart';
import { RecentTrades } from './components/RecentTrades';
import { AgentMemory } from './components/AgentMemory';
import { OpenPositions } from './components/OpenPositions';
import { RiskMetrics } from './components/RiskMetrics';
import { MarketTicker } from './components/MarketTicker';
import { SummaryData } from './types';

function App() {
  const { summary, trades, positions, lessons, chartData, loading, toggleHalt } = useDashboardData();
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis'>('overview');

  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-secondary bg-[#0f1219]">
        <div className="w-10 h-10 border-4 border-white/10 border-t-accent rounded-full animate-spin"></div>
        <p className="font-medium tracking-wide">Connecting to RakshaQuant Core...</p>
      </div>
    );
  }

  // Fallback if backend is not running yet
  const data: SummaryData = summary || {
    balance: 1000000,
    total_trades: 0,
    win_rate: 0,
    total_pnl: 0,
    open_positions: 0,
    realized_pnl: 0,
    unrealized_pnl: 0,
    return_pct: 0,
    latest_regime: 'Searching...',
    regime_confidence: 0,
    active_strategies: [],
    is_halted: false
  };

  const isProfitable = data.total_pnl >= 0;
  
  const displayChartData = chartData.length > 0 ? chartData : [
    { time: 'Start', balance: 1000000 }, 
    { time: 'Now', balance: 1000000 }
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <MarketTicker />
      
      <div className="max-w-7xl w-full mx-auto p-4 md:p-8 flex flex-col gap-8 flex-1">
        <Header isHalted={!!data.is_halted} onToggleHalt={toggleHalt} />

        {/* Tab Navigation */}
        <div className="flex gap-1 p-1 bg-white/5 rounded-xl w-fit border border-white/5">
          <button 
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'overview' ? 'bg-accent text-white shadow-lg' : 'text-secondary hover:text-white'}`}
          >
            <LayoutDashboard size={16} /> Overview
          </button>
          <button 
            onClick={() => setActiveTab('analysis')}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'analysis' ? 'bg-accent text-white shadow-lg' : 'text-secondary hover:text-white'}`}
          >
            <Brain size={16} /> AI Analysis
          </button>
        </div>

        {activeTab === 'overview' ? (
          <>
            {/* Stats Overview omitted for brevity in replace tool, but it will be preserved */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard 
                icon={<Wallet size={16} />} 
                label="Total Balance" 
                value={`₹${data.balance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                trendIcon={isProfitable ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                trendText={`${Math.abs(data.return_pct).toFixed(2)}% Session`}
                trendMode={isProfitable ? 'up' : 'down'}
              />

              <StatCard 
                icon={<Activity size={16} />} 
                label="Net P&L" 
                value={`₹${data.total_pnl > 0 ? '+' : ''}${data.total_pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
                trendText="Unrealized + Realized"
                trendMode={isProfitable ? 'up' : 'down'}
              />

              <StatCard 
                icon={<Target size={16} />} 
                label="Win Rate" 
                value={`${data.win_rate.toFixed(1)}%`}
                trendIcon={<Minus size={16} />}
                trendText={`Out of ${data.total_trades} items`}
              />

              <StatCard 
                icon={<TrendingUp size={16} />} 
                label="Return %" 
                value={`${data.return_pct.toFixed(2)}%`}
                trendText="Quant Quality"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 flex flex-col gap-6">
                <PerformanceChart data={displayChartData} />
                <OpenPositions positions={positions || []} />
              </div>

              <div className="flex flex-col gap-6">
                <RiskMetrics summary={data} />
                <RecentTrades trades={trades} />
              </div>
            </div>
          </>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="glass-panel">
               <h2 className="text-xl mb-6 text-primary flex items-center gap-2">
                 <ShieldAlert size={20} className="text-accent" />
                 Market Intelligence (LangGraph)
               </h2>
               
               <div className="space-y-6">
                 <div>
                   <label className="text-xs text-secondary uppercase tracking-widest block mb-2">Current Market Regime</label>
                   <div className="flex items-center gap-3">
                     <span className="text-2xl font-bold text-primary capitalize">{data.latest_regime.replace('_', ' ')}</span>
                     <span className="px-2 py-1 bg-accent/20 text-accent text-xs rounded-lg font-bold">
                       {Math.round(data.regime_confidence * 100)}% Match
                     </span>
                   </div>
                 </div>

                 {/* News Sentiment Section */}
                 <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                   <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                     <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                     Market Sentiment (News)
                   </h3>
                   <div className="space-y-4">
                     <div className="flex justify-between items-center text-sm">
                       <span className="text-slate-400">Headline Context</span>
                       <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                         (summary?.latest_news?.avg_sentiment ?? 0) >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                       }`}>
                         {summary?.latest_news?.sentiment_label || 'Neutral'}
                       </span>
                     </div>
                      <div className="space-y-2">
                        {summary?.latest_news?.headlines && summary.latest_news.headlines.length > 0 ? (
                          summary.latest_news.headlines.slice(0, 3).map((h, i) => (
                            <p key={i} className="text-xs text-slate-300 italic border-l-2 border-slate-700 pl-3 leading-relaxed">
                              {h}
                            </p>
                          ))
                        ) : (
                          <p className="text-xs text-zinc-500 italic">Scanning global markets for catalysts...</p>
                        )}
                      </div>
                   </div>
                 </div>

                 {/* Geometric Vision Section */}
                  <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
                      Geometric Pattern Recognition (Vision)
                    </h3>
                    <div className="space-y-4">
                      {summary?.latest_vision && Object.keys(summary.latest_vision).length > 0 ? (
                        Object.entries(summary.latest_vision).map(([symbol, vision]) => (
                          <div key={symbol} className="p-3 bg-zinc-800/30 rounded-lg border border-zinc-700/50">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs text-zinc-400">Pattern Detected ({symbol}):</span>
                              <span className="text-white font-medium text-sm">{vision.pattern || "None"}</span>
                            </div>
                            <p className="text-zinc-400 text-xs italic">
                              "{vision.reasoning || "Analyzing visual chart structures..."}"
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-zinc-500 text-xs italic">Scanning real-time charts for geometric structures...</p>
                      )}
                    </div>
                  </div>

                  <div className="bg-zinc-900/50 rounded-xl p-5 border border-zinc-800">
                    <h4 className="flex items-center gap-2 text-white font-semibold mb-4">
                      <BarChart3 className="w-5 h-5 text-purple-400" />
                      Institutional Footprint (Volume Profile)
                    </h4>
                    {summary?.latest_volume && Object.keys(summary.latest_volume).length > 0 ? (
                      <div className="space-y-4">
                        {Object.entries(summary.latest_volume).map(([symbol, data]) => (
                          <div key={symbol} className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-white font-bold">{symbol}</span>
                              <span className={`text-xs px-2 py-0.5 rounded-full ${
                                data.institutional_activity.includes('Accumulation') ? 'bg-green-500/20 text-green-400' : 
                                data.institutional_activity.includes('Distribution') ? 'bg-red-500/20 text-red-400' : 
                                'bg-zinc-500/20 text-zinc-400'
                              }`}>
                                {data.institutional_activity}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[10px] md:text-xs">
                              <div className="flex justify-between">
                                <span className="text-zinc-400">PoC:</span>
                                <span className="text-white font-mono">₹{data.poc}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">Intensity:</span>
                                <span className="text-white font-mono">{data.activity_intensity}σ</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">VAH:</span>
                                <span className="text-white font-mono">₹{data.vah}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-zinc-400">VAL:</span>
                                <span className="text-white font-mono">₹{data.val}</span>
                              </div>
                            </div>
                            <p className="text-[10px] text-zinc-500 mt-2 italic line-clamp-2">{data.summary}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-zinc-500 text-sm italic">Institutional liquidity analysis in progress...</p>
                    )}
                  </div>

                  <div className="bg-zinc-900/50 rounded-xl p-5 border border-zinc-800">
                    <label className="text-xs text-secondary uppercase tracking-widest block mb-2">Active AI Strategies</label>
                    <div className="flex flex-wrap gap-2">
                      {data.active_strategies.map(s => (
                        <span key={s} className="px-3 py-1.5 bg-white/5 border border-white/5 rounded-full text-xs text-secondary font-medium">
                          {s.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 bg-accent/5 border border-accent/10 rounded-xl">
                    <p className="text-xs text-secondary leading-relaxed italic">
                      "The Market Regime Agent has detected a {data.latest_regime.replace('_', ' ')} phase. Strategy Selection Agent has prioritized these {data.active_strategies.length} logic streams for execution."
                    </p>
                  </div>
               </div>
            </div>
            
            <AgentMemory lessons={lessons} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
