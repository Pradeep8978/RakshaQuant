import React from 'react';
import { TrendingUp } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { ChartDataPoint } from '../types';

interface PerformanceChartProps {
  data: ChartDataPoint[];
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
      <h2 className="section-title">
        <TrendingUp size={20} color="var(--accent)" />
        Session Performance
      </h2>
      <div style={{ flex: 1, minHeight: '300px', width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis 
              dataKey="time" 
              stroke="var(--text-secondary)" 
              tick={{ fill: 'var(--text-secondary)' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              domain={['dataMin - 1000', 'dataMax + 1000']} 
              stroke="var(--text-secondary)"
              tick={{ fill: 'var(--text-secondary)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(val) => `₹${val/1000}k`}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(15, 18, 25, 0.9)', 
                border: '1px solid var(--panel-border)',
                borderRadius: '8px'
              }}
              itemStyle={{ color: 'var(--text-primary)' }}
            />
            <Area 
              type="monotone" 
              dataKey="balance" 
              stroke="var(--accent)" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorBalance)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
