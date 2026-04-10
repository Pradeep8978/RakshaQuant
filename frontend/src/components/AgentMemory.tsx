import { Brain } from 'lucide-react';
import { Lesson } from '../types';

interface AgentMemoryProps {
  lessons: Lesson[];
}

export function AgentMemory({ lessons }: AgentMemoryProps) {
  return (
    <div className="glass-panel">
      <h2 className="text-xl mb-5 text-primary flex items-center gap-2">
        <Brain size={20} />
        Live Agent Memory
      </h2>
      
      {lessons.length === 0 ? (
        <div className="text-secondary p-4 text-center border border-white/5 rounded-lg">
          No new lessons learned in this session.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {lessons.map((l, i) => (
            <div key={i} className="p-3.5 border-l-4 border-accent bg-gradient-to-r from-accent/5 to-transparent rounded-r-lg text-sm leading-relaxed">
              <div className="text-xs text-accent uppercase tracking-wider mb-1 font-semibold flex justify-between">
                <span>{l.category.replace('_', ' ')}</span>
                <span className={`
                  ${l.severity === 'critical' ? 'text-red-500' : ''}
                  ${l.severity === 'high' ? 'text-orange-500' : ''}
                  ${l.severity === 'medium' ? 'text-yellow-500' : ''}
                  ${l.severity === 'low' ? 'text-emerald-500' : ''}
                `}>
                  {l.severity} Priority
                </span>
              </div>
              <div className="text-secondary font-medium mb-1">
                {l.lesson}
              </div>
              <div className="text-secondary/70 text-xs italic">
                "{l.description}"
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
