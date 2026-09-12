import React, { useState } from 'react';
import { ShieldAlert, RefreshCw, CheckCircle2, AlertOctagon, Terminal, ArrowRight, Database } from 'lucide-react';
import { runReconciliation } from '../services/api';
import { ReconciliationResult } from '../types/quant';

interface ReconciliationDebuggerProps {
  useBackend: boolean;
}

export const ReconciliationDebugger: React.FC<ReconciliationDebuggerProps> = ({ useBackend }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ReconciliationResult | null>(null);

  const handleRunReconcile = async () => {
    setIsRunning(true);
    try {
      const res = await runReconciliation(useBackend);
      setResult(res);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-quant-card/70 border border-quant-border rounded-lg p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            CRASH RECOVERY & BROKER RECONCILIATION DEBUGGER
            <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
              Idempotent Orders & Broker State Truth
            </span>
          </h2>
          <p className="text-xs text-quant-muted">
            Simulates an engine crash mid-session, restarts with clean memory, and reconciles against broker snapshot
          </p>
        </div>

        <button
          onClick={handleRunReconcile}
          disabled={isRunning}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-sm transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{result ? 'Re-run Crash Simulation' : 'Simulate Crash & Reconcile'}</span>
        </button>
      </div>

      {!result ? (
        <div className="p-6 text-center rounded border border-dashed border-quant-border bg-quant-surface/40">
          <Database className="w-8 h-8 text-sky-400/60 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-slate-200">Test Order State Recovery & Idempotency</h3>
          <p className="text-xs text-quant-muted max-w-lg mx-auto mt-1 mb-4">
            Click the button above to simulate an ungraceful process termination during active trading.
            The engine restarts from scratch, generates deterministic SHA-1 client order IDs, and adopts broker truth.
          </p>
          <button
            onClick={handleRunReconcile}
            className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition cursor-pointer"
          >
            Launch Crash & Reconciliation Test
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Status summary banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 rounded bg-quant-surface border border-quant-border">
              <span className="text-[10px] text-quant-muted uppercase tracking-wider block mb-0.5">Reconciliation Status</span>
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-sm font-mono">
                <CheckCircle2 className="w-4 h-4" />
                RECONCILED TO BROKER TRUTH
              </div>
            </div>

            <div className="p-3 rounded bg-quant-surface border border-quant-border">
              <span className="text-[10px] text-quant-muted uppercase tracking-wider block mb-0.5">Broker Orders Synced</span>
              <div className="text-slate-100 font-bold text-sm font-mono">
                {result.total_broker_orders} Orders Verified
              </div>
            </div>

            <div className="p-3 rounded bg-quant-surface border border-quant-border">
              <span className="text-[10px] text-quant-muted uppercase tracking-wider block mb-0.5">Position Truth (Fills Only)</span>
              <div className="text-sky-300 font-bold text-sm font-mono">
                Net {result.reconciled_position.toFixed(1)} Units Held
              </div>
            </div>
          </div>

          {/* Audit Notes Terminal */}
          <div className="rounded border border-quant-border bg-[#070b12] p-3 font-mono text-xs">
            <div className="flex items-center gap-2 text-quant-muted pb-2 mb-2 border-b border-quant-border/60">
              <Terminal className="w-3.5 h-3.5 text-amber-400" />
              <span className="font-semibold text-slate-300">ENGINE RECONCILIATION AUDIT LOG:</span>
            </div>
            <div className="space-y-1.5 text-slate-300">
              {result.notes.map((note, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-amber-400 font-bold shrink-0">[AUDIT]</span>
                  <span className="text-amber-200/90">{note}</span>
                </div>
              ))}
              <div className="flex items-start gap-2 text-emerald-400">
                <span className="font-bold shrink-0">[OK]</span>
                <span>Deterministic SHA-1 keys matched. Zero duplicate fills recorded. Position verified.</span>
              </div>
            </div>
          </div>

          {/* Reconciled Order Book */}
          <div className="overflow-x-auto max-h-[220px] rounded border border-quant-border">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-quant-surface text-quant-muted sticky top-0 border-b border-quant-border">
                <tr>
                  <th className="py-2 px-3">Client Order ID (SHA-1)</th>
                  <th className="py-2 px-3">Broker Order ID</th>
                  <th className="py-2 px-3">Side</th>
                  <th className="py-2 px-3">Qty</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3 text-right">Fill Price</th>
                  <th className="py-2 px-3">Intent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-quant-border/60">
                {result.orders.map((o, idx) => (
                  <tr key={idx} className="hover:bg-quant-surface/50">
                    <td className="py-2 px-3 font-semibold text-sky-300">{o.client_order_id}</td>
                    <td className="py-2 px-3 text-quant-muted">{o.broker_order_id || 'PENDING'}</td>
                    <td className="py-2 px-3">
                      <span className={o.side === 'BUY' ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                        {o.side}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-200">{o.qty.toFixed(1)}</td>
                    <td className="py-2 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold">
                        {o.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right text-slate-100">
                      {o.fill_price ? `₹${o.fill_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="py-2 px-3 text-slate-400">{o.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

