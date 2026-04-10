import React from 'react';
import { BrainCircuit } from 'lucide-react';

export function Header() {
  return (
    <header className="header glass-panel">
      <h1 className="header-title">
        <BrainCircuit size={32} color="var(--accent)" />
        RakshaQuant
      </h1>
      <div className="status-badge">
        <div className="status-dot"></div>
        System Live (Paper)
      </div>
    </header>
  );
}
