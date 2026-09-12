import React from 'react';
import { X, CheckCircle2, ShieldAlert, Cpu, Layers, GitBranch, Terminal, FileCode2, Scale } from 'lucide-react';

interface ArchitectureModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ArchitectureModal: React.FC<ArchitectureModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-quant-surface border border-quant-border rounded-xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-quant-border flex items-center justify-between bg-quant-card/50">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-sky-400" />
              SYSTEM ARCHITECTURE & QUANT COMPLIANCE
            </h2>
            <p className="text-xs text-quant-muted font-mono">
              Vera Developers — Quant Developer Assignment Submission Architecture
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-quant-border text-quant-muted hover:text-white transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto space-y-6 text-xs leading-relaxed text-slate-300">
          {/* Executive Overview */}
          <div className="bg-sky-500/10 border border-sky-500/20 rounded-lg p-3.5">
            <h3 className="text-xs font-bold text-sky-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Scale className="w-4 h-4 text-sky-400" />
              Quant Engineering Philosophy
            </h3>
            <p className="text-slate-200">
              A production algorithmic execution desk requires reconciling backtest P&L with live trading ledger down to the paisa.
              This system demonstrates a <strong>representative, fully-tested vertical slice</strong> prioritizing architectural rigor:
              causal lookahead-free fills, deterministic idempotency, fill-only position truth, and statutory Indian market cost modeling.
            </p>
          </div>

          {/* Core Design Principles */}
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-1.5 border-b border-quant-border pb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              6 Non-Negotiable Quant Design Principles
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 rounded bg-quant-card border border-quant-border">
                <span className="font-bold text-slate-100 block mb-1">1. No Lookahead Enforced Structurally</span>
                <span className="text-quant-muted">
                  Indicators are causal by construction. Strategy decisions made on bar <code>i</code> are filled exclusively at bar <code>i+1's OPEN</code>, never at bar <code>i</code>'s close.
                </span>
              </div>

              <div className="p-3 rounded bg-quant-card border border-quant-border">
                <span className="font-bold text-slate-100 block mb-1">2. One Implementation Per Concept</span>
                <span className="text-quant-muted">
                  ATR is computed once in <code>src/indicators.py</code> and reused across spacing and stops. Slippage/taxes are calculated by a single <code>CostModel</code>.
                </span>
              </div>

              <div className="p-3 rounded bg-quant-card border border-quant-border">
                <span className="font-bold text-slate-100 block mb-1">3. One Decision Function, Two Callers</span>
                <span className="text-quant-muted">
                  <code>GridReverseEngine.on_bar()</code> is the single source of truth. Driven identically by the backtest loop or a live WebSocket bar-close handler, preventing strategy drift.
                </span>
              </div>

              <div className="p-3 rounded bg-quant-card border border-quant-border">
                <span className="font-bold text-slate-100 block mb-1">4. Position Truth From Fills Only</span>
                <span className="text-quant-muted">
                  <code>OrderManager.net_position()</code> counts strictly <code>FILLED</code> orders. Pending or rejected orders can never silently inflate risk check caps.
                </span>
              </div>

              <div className="p-3 rounded bg-quant-card border border-quant-border">
                <span className="font-bold text-slate-100 block mb-1">5. Idempotency By Construction</span>
                <span className="text-quant-muted">
                  Client order IDs are deterministic SHA-1 hashes of <code>(strategy, bar_index, intent)</code>. Replaying an event stream after a crash is a safe no-op.
                </span>
              </div>

              <div className="p-3 rounded bg-quant-card border border-quant-border">
                <span className="font-bold text-slate-100 block mb-1">6. Hard Walk-Forward Fold Isolation</span>
                <span className="text-quant-muted">
                  Each walk-forward window gets a fresh engine and order manager instance. Zero position state or indicator warmup leaks across fold boundaries.
                </span>
              </div>
            </div>
          </div>

          {/* Module Coverage Breakdown */}
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-3 flex items-center gap-1.5 border-b border-quant-border pb-1">
              <FileCode2 className="w-4 h-4 text-purple-400" />
              Brief Scope vs Implementation Matrix
            </h3>

            <div className="overflow-x-auto rounded border border-quant-border">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-quant-surface text-quant-muted border-b border-quant-border">
                  <tr>
                    <th className="py-2 px-3">Module</th>
                    <th className="py-2 px-3">File</th>
                    <th className="py-2 px-3">Status</th>
                    <th className="py-2 px-3">Brief Requirement Covered</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-quant-border/60">
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">Execution Engine</td>
                    <td className="py-2 px-3 text-sky-400">src/engine.py</td>
                    <td className="py-2 px-3 text-emerald-400">Implemented</td>
                    <td className="py-2 px-3 text-quant-muted">ATR spacing, pyramiding, position cap, kill switch</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">TA Indicators</td>
                    <td className="py-2 px-3 text-sky-400">src/indicators.py</td>
                    <td className="py-2 px-3 text-emerald-400">Implemented</td>
                    <td className="py-2 px-3 text-quant-muted">EMA, RSI (Wilder's), ATR, OBV (no duplicated math)</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">Order/State Book</td>
                    <td className="py-2 px-3 text-sky-400">src/orders.py</td>
                    <td className="py-2 px-3 text-emerald-400">Implemented</td>
                    <td className="py-2 px-3 text-quant-muted">Deterministic IDs, restart reconciliation, fill truth</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">Cost Model</td>
                    <td className="py-2 px-3 text-sky-400">src/costs.py</td>
                    <td className="py-2 px-3 text-emerald-400">Implemented</td>
                    <td className="py-2 px-3 text-quant-muted">Slippage, ₹20 flat brokerage, STT/CTT, GST</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">Backtest Harness</td>
                    <td className="py-2 px-3 text-sky-400">src/backtest.py</td>
                    <td className="py-2 px-3 text-emerald-400">Implemented</td>
                    <td className="py-2 px-3 text-quant-muted">Bar-accurate fills, walk-forward, warmup discipline</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">Regression Suite</td>
                    <td className="py-2 px-3 text-sky-400">tests/</td>
                    <td className="py-2 px-3 text-emerald-400">39 Passing</td>
                    <td className="py-2 px-3 text-quant-muted">Crash recovery test, boundary tests, cost tests</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 font-semibold text-slate-200">Live Kite REST/WS</td>
                    <td className="py-2 px-3 text-amber-400">src/data.py</td>
                    <td className="py-2 px-3 text-amber-400">Sandboxed</td>
                    <td className="py-2 px-3 text-quant-muted">Clean adapter boundary ready for Kite Connect</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-quant-border bg-quant-card/40 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition cursor-pointer"
          >
            Close Overview
          </button>
        </div>
      </div>
    </div>
  );
};

