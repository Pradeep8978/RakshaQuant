import { BrainCircuit, AlertTriangle, Play } from 'lucide-react';

interface HeaderProps {
  isHalted: boolean;
  onToggleHalt: (halt: boolean) => void;
}

export function Header({ isHalted, onToggleHalt }: HeaderProps) {
  return (
    <header className="header glass-panel">
      <h1 className="header-title">
        <BrainCircuit size={32} color="var(--accent)" />
        RakshaQuant
      </h1>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <button 
          onClick={() => onToggleHalt(!isHalted)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '9999px',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: isHalted ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            color: isHalted ? 'var(--success)' : 'var(--danger)',
            transition: 'all 0.2s ease',
          }}
        >
          {isHalted ? (
             <><Play size={16}/> Resume Trading</>
          ) : (
             <><AlertTriangle size={16}/> Halt Trading</>
          )}
        </button>

        <div className="status-badge" style={{
          background: isHalted ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
          borderColor: isHalted ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
          color: isHalted ? 'var(--danger)' : 'var(--success)',
          boxShadow: isHalted ? '0 0 15px var(--danger-glow)' : '0 0 15px var(--success-glow)'
        }}>
          {isHalted ? (
            <>
              <div className="status-dot" style={{ backgroundColor: 'var(--danger)', animation: 'none' }}></div>
              System Halted
            </>
          ) : (
            <>
              <div className="status-dot"></div>
              System Live
            </>
          )}
        </div>
      </div>
    </header>
  );
}
