import React from 'react';
import { BrainCircuit } from 'lucide-react';
import { Lesson } from '../types';

interface AgentMemoryProps {
  lessons: Lesson[];
}

export function AgentMemory({ lessons }: AgentMemoryProps) {
  return (
    <div className="glass-panel">
      <h2 className="section-title">
        <BrainCircuit size={20} color="var(--accent)" />
        Agent Memory
      </h2>
      <div className="agent-log">
        {lessons.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '1rem' }}>
            Memory database is still learning...
          </div>
        ) : (
          lessons.map(lesson => (
            <div key={lesson.lesson_id} className="log-entry">
              <div className="log-entry-category">
                {lesson.category} • {lesson.severity}
              </div>
              <div className="log-entry-content">
                {lesson.description}
              </div>
              <div style={{ marginTop: '0.5rem', color: 'var(--text-primary)', fontSize: '0.85rem', fontWeight: 500 }}>
                → {lesson.lesson}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
