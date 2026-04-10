import { BrainCircuit, AlertTriangle, Play } from 'lucide-react';

interface HeaderProps {
  isHalted: boolean;
  onToggleHalt: (halt: boolean) => void;
}

export function Header({ isHalted, onToggleHalt }: HeaderProps) {
  return (
    <header className="flex justify-between items-center pb-4 border-b border-panel-border">
      <h1 className="text-3xl font-semibold bg-gradient-to-br from-white to-slate-400 bg-clip-text text-transparent flex items-center gap-3">
        <BrainCircuit size={32} className="text-accent" />
        RakshaQuant
      </h1>
      <div className="flex gap-4 items-center">
        <button 
          onClick={() => onToggleHalt(!isHalted)}
          className={`flex items-center gap-2 px-4 py-2 rounded-full font-semibold transition-all duration-200 border-none cursor-pointer ${
            isHalted 
              ? 'bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30' 
              : 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
          }`}
        >
          {isHalted ? (
             <><Play size={16}/> Resume Trading</>
          ) : (
             <><AlertTriangle size={16}/> Halt Trading</>
          )}
        </button>

        <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border shadow-[0_0_15px] ${
          isHalted 
            ? 'bg-red-500/10 border-red-500/20 text-red-500 shadow-red-500/30' 
            : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500 shadow-emerald-500/30'
        }`}>
          {isHalted ? (
            <>
              <div className="w-2 h-2 rounded-full bg-red-500"></div>
              System Halted
            </>
          ) : (
            <>
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              System Live
            </>
          )}
        </div>
      </div>
    </header>
  );
}
