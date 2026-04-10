import { ReactNode } from 'react';

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string | number;
  trendIcon?: ReactNode;
  trendText?: string;
  trendMode?: 'up' | 'down' | 'neutral';
}

export function StatCard({ 
  icon, 
  label, 
  value, 
  trendIcon, 
  trendText, 
  trendMode = 'neutral' 
}: StatCardProps) {
  
  let trendColor = 'text-warning';
  if (trendMode === 'up') trendColor = 'text-success';
  if (trendMode === 'down') trendColor = 'text-danger';

  return (
    <div className="glass-panel flex flex-col gap-2">
      <div className="text-secondary text-sm font-medium uppercase tracking-wider flex items-center gap-2">
        {icon}
        {label}
      </div>
      <div className="text-4xl font-bold text-primary">
        {value}
      </div>
      {trendText && (
        <div className={`text-sm font-medium flex items-center gap-1 ${trendColor}`}>
          {trendIcon}
          {trendText}
        </div>
      )}
    </div>
  );
}
