import React, { ReactNode } from 'react';

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: ReactNode;
  trendIcon?: React.ReactNode;
  trendText: string;
  trendMode?: 'up' | 'down' | 'neutral';
}

export function StatCard({ icon, label, value, trendIcon, trendText, trendMode = 'neutral' }: StatCardProps) {
  let trendClass = 'trend-neutral';
  if (trendMode === 'up') trendClass = 'trend-up';
  if (trendMode === 'down') trendClass = 'trend-down';

  return (
    <div className="glass-panel stat-card">
      <div className="stat-label">
        {icon} {label}
      </div>
      <div className="stat-value">{value}</div>
      <div className={`stat-trend ${trendClass}`}>
        {trendIcon}
        {trendText}
      </div>
    </div>
  );
}
