import { Activity, TrendingUp, Wallet, Target, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { useDashboardData } from './hooks/useDashboardData';
import { Header } from './components/Header';
import { StatCard } from './components/StatCard';
import { PerformanceChart } from './components/PerformanceChart';
import { RecentTrades } from './components/RecentTrades';
import { AgentMemory } from './components/AgentMemory';

function App() {
  const { summary, trades, lessons, chartData, loading, toggleHalt } = useDashboardData();

  if (loading && !summary) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Connecting to RakshaQuant Core...</p>
      </div>
    );
  }

  // Fallback if backend is not running yet
  const data = summary || {
    balance: 1000000,
    total_trades: 0,
    win_rate: 0,
    total_pnl: 0,
    open_positions: 0,
    is_halted: false
  };

  const isProfitable = data.total_pnl >= 0;
  
  // Default fallback if no trades have closed yet
  const displayChartData = chartData.length > 0 ? chartData : [
    { time: 'Start', balance: 1000000 }, 
    { time: 'Now', balance: 1000000 }
  ];

  return (
    <div className="dashboard-container">
      <Header isHalted={!!data.is_halted} onToggleHalt={toggleHalt} />

      {/* Stats Overview */}
      <div className="overview-grid">
        <StatCard 
          icon={<Wallet size={16} />} 
          label="Total Balance" 
          value={`₹${data.balance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          trendIcon={isProfitable ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
          trendText={`${Math.abs((data.total_pnl / 1000000) * 100).toFixed(2)}% Session`}
          trendMode={isProfitable ? 'up' : 'down'}
        />

        <StatCard 
          icon={<Activity size={16} />} 
          label="Net P&L" 
          value={`₹${data.total_pnl > 0 ? '+' : ''}${data.total_pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          trendText="Realized"
          trendMode={isProfitable ? 'up' : 'down'}
        />

        <StatCard 
          icon={<Target size={16} />} 
          label="Win Rate" 
          value={`${data.win_rate.toFixed(1)}%`}
          trendIcon={<Minus size={16} />}
          trendText={`Out of ${data.total_trades} trades`}
        />

        <StatCard 
          icon={<TrendingUp size={16} />} 
          label="Open Positions" 
          value={data.open_positions}
          trendText="Currently active"
        />
      </div>

      {/* Main Content */}
      <div className="content-grid">
        <PerformanceChart data={displayChartData} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <RecentTrades trades={trades} />
          <AgentMemory lessons={lessons} />
        </div>
      </div>
    </div>
  );
}

export default App;
