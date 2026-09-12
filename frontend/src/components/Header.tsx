import React from 'react';
import { Activity, Cpu, ShieldCheck, Sliders, FileText, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

interface HeaderProps {
  isBackendConnected: boolean;
  useBackend: boolean;
  setUseBackend: (val: boolean) => void;
  onOpenConfig: () => void;
  onOpenArchitecture: () => void;
  onRunBacktest: () => void;
  isLoading: boolean;
  killSwitchFired: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  isBackendConnected,
  useBackend,
  setUseBackend,
  onOpenConfig,
  onOpenArchitecture,
  onRunBacktest,
  isLoading,
  killSwitchFired,
}) => {
  return (
    <header className="border-b border-quant-border bg-quant-surface/90 backdrop-blur sticky top-0 z-30 px-4 lg:px-6 py-3">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        {/* Title & Brand */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 font-bold">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                VERA QUANT LAB
                <span className="text-xs px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 font-mono border border-sky-500/30 font-semibold">
                  v1.0-PROD
                </span>
              </h1>
            </div>
            <p className="text-xs text-quant-muted font-mono">
              Grid + Stop-and-Reverse Execution Engine • Bar-Accurate Fills • Indian Market Plumbing
            </p>
          </div>
        </div>

        {/* Engine Status Badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Execution Environment Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-quant-card border border-quant-border">
            <Cpu className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-quant-muted">Engine:</span>
            {isBackendConnected ? (
              <button
                onClick={() => setUseBackend(!useBackend)}
                className={`font-semibold cursor-pointer hover:underline ${
                  useBackend ? 'text-emerald-400' : 'text-amber-400'
                }`}
                title="Click to toggle between Python FastAPI and In-Browser Engine"
              >
                {useBackend ? 'Python API (Connected)' : 'In-Browser JS Engine'}
              </button>
            ) : (
              <span className="text-sky-400 font-medium font-mono" title="Zero-friction client-side execution for recruiters">
                In-Browser Engine (Vercel Ready)
              </span>
            )}
          </div>

          {/* Lookahead Guard */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-quant-card border border-quant-border">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-quant-muted">No-Lookahead:</span>
            <span className="text-emerald-400 font-medium">t+1 Open Fill</span>
          </div>

          {/* Kill Switch State */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border ${
              killSwitchFired
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400 animate-pulse'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}
          >
            {killSwitchFired ? (
              <>
                <AlertTriangle className="w-3.5 h-3.5" />
                <span className="font-semibold">Kill Switch: FIRED (15% DD)</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Kill Switch: ACTIVE (15% Max DD)</span>
              </>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={onRunBacktest}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Re-run Simulation</span>
          </button>

          <button
            onClick={onOpenConfig}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-quant-card hover:bg-quant-border border border-quant-border text-slate-200 text-xs font-medium transition cursor-pointer"
          >
            <Sliders className="w-3.5 h-3.5 text-sky-400" />
            <span>Parameters</span>
          </button>

          <button
            onClick={onOpenArchitecture}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-quant-card hover:bg-quant-border border border-quant-border text-slate-200 text-xs font-medium transition cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-amber-400" />
            <span>Architecture & Scope</span>
          </button>
        </div>
      </div>
    </header>
  );
};

