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

                 <div>
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
