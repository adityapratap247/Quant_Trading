import React, { useState } from 'react';
import { X, Sliders, RotateCcw, Play, IndianRupee, ShieldCheck } from 'lucide-react';
import { EngineConfig, CostModel } from '../types/quant';

interface ConfigDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentEngineConfig: EngineConfig;
  currentCostModel: CostModel;
  onApply: (newEngineConfig: EngineConfig, newCostModel: CostModel) => void;
}

export const ConfigDrawer: React.FC<ConfigDrawerProps> = ({
  isOpen,
  onClose,
  currentEngineConfig,
  currentCostModel,
  onApply,
}) => {
  const [engineConfig, setEngineConfig] = useState<EngineConfig>({ ...currentEngineConfig });
  const [costModel, setCostModel] = useState<CostModel>({ ...currentCostModel });

  if (!isOpen) return null;

  const handleReset = () => {
    setEngineConfig({
      strategy_id: 'grid_sar_v1',
      base_qty: 1.0,
      atr_multiplier: 1.0,
      stop_multiplier: 2.5,
      max_pyramids: 4,
      position_cap: 5.0,
      kill_switch_dd_pct: 0.15,
    });
    setCostModel({
      slippage_bps: 2.0,
      brokerage_per_order: 20.0,
      stt_ctt_bps: 1.0,
      exchange_txn_bps: 0.35,
      gst_rate: 0.18,
    });
  };

  const handleSave = () => {
    onApply(engineConfig, costModel);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-quant-surface border-l border-quant-border h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-quant-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Parameters & Indian Tax Plumbing</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-quant-border text-quant-muted hover:text-white transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1 space-y-6 text-xs">
          {/* Section 1: Execution Engine Config */}
          <div>
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-quant-border">
              <span className="font-bold text-slate-200 uppercase tracking-wide">Grid & SAR Engine Tuning</span>
              <span className="text-[10px] text-sky-400 font-mono">src/engine.py</span>
            </div>

            <div className="space-y-4">
              {/* ATR Multiplier (Grid Spacing) */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>ATR Grid Spacing (Multiplier)</span>
                  <span className="text-white font-bold">{engineConfig.atr_multiplier}x ATR</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.1"
                  value={engineConfig.atr_multiplier}
                  onChange={e => setEngineConfig({ ...engineConfig, atr_multiplier: parseFloat(e.target.value) })}
                  className="w-full accent-sky-500 cursor-pointer"
                />
                <span className="text-[10px] text-quant-muted">Favourable moves of this distance trigger pyramid adds</span>
              </div>

              {/* Stop Multiplier */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Stop-and-Reverse Distance</span>
                  <span className="text-white font-bold">{engineConfig.stop_multiplier}x ATR</span>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="5.0"
                  step="0.25"
                  value={engineConfig.stop_multiplier}
                  onChange={e => setEngineConfig({ ...engineConfig, stop_multiplier: parseFloat(e.target.value) })}
                  className="w-full accent-rose-500 cursor-pointer"
                />
                <span className="text-[10px] text-quant-muted">Adverse move from entry reference triggers full SAR flip</span>
              </div>

              {/* Max Pyramids */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Max Pyramids (Additional Units)</span>
                  <span className="text-white font-bold">{engineConfig.max_pyramids} units</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="6"
                  step="1"
                  value={engineConfig.max_pyramids}
                  onChange={e => setEngineConfig({ ...engineConfig, max_pyramids: parseInt(e.target.value) })}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              {/* Position Cap */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Position Hard Cap</span>
                  <span className="text-white font-bold">{engineConfig.position_cap} max qty</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={engineConfig.position_cap}
                  onChange={e => setEngineConfig({ ...engineConfig, position_cap: parseFloat(e.target.value) })}
                  className="w-full accent-indigo-500 cursor-pointer"
                />
                <span className="text-[10px] text-quant-muted">Strict bound on net exposure (units)</span>
              </div>

              {/* Kill Switch Drawdown */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Kill Switch Drawdown Limit</span>
                  <span className="text-rose-400 font-bold">{(engineConfig.kill_switch_dd_pct * 100).toFixed(0)}% DD</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="0.30"
                  step="0.01"
                  value={engineConfig.kill_switch_dd_pct}
                  onChange={e => setEngineConfig({ ...engineConfig, kill_switch_dd_pct: parseFloat(e.target.value) })}
                  className="w-full accent-rose-500 cursor-pointer"
                />
                <span className="text-[10px] text-quant-muted">Drawdown from peak equity that immediately flattens and halts</span>
              </div>
            </div>
          </div>

          {/* Section 2: Indian Market Cost Model */}
          <div>
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-quant-border">
              <span className="font-bold text-slate-200 uppercase tracking-wide">Indian Statutory Cost Model</span>
              <span className="text-[10px] text-violet-400 font-mono">src/costs.py</span>
            </div>

            <div className="space-y-4">
              {/* Slippage bps */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Market Slippage Impact</span>
                  <span className="text-white font-bold">{costModel.slippage_bps} bps</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5.0"
                  step="0.25"
                  value={costModel.slippage_bps}
                  onChange={e => setCostModel({ ...costModel, slippage_bps: parseFloat(e.target.value) })}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>

              {/* Flat Brokerage */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Brokerage (Kite Connect flat fee)</span>
                  <span className="text-white font-bold">₹{costModel.brokerage_per_order.toFixed(1)} / order</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="40"
                  step="5"
                  value={costModel.brokerage_per_order}
                  onChange={e => setCostModel({ ...costModel, brokerage_per_order: parseFloat(e.target.value) })}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>

              {/* STT/CTT */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>STT / CTT (Sell-side only)</span>
                  <span className="text-white font-bold">{costModel.stt_ctt_bps} bps</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="3.0"
                  step="0.25"
                  value={costModel.stt_ctt_bps}
                  onChange={e => setCostModel({ ...costModel, stt_ctt_bps: parseFloat(e.target.value) })}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>

              {/* Exchange txn bps */}
              <div>
                <div className="flex justify-between text-quant-muted mb-1 font-mono">
                  <span>Exchange Transaction Charges</span>
                  <span className="text-white font-bold">{costModel.exchange_txn_bps} bps</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="1.5"
                  step="0.05"
                  value={costModel.exchange_txn_bps}
                  onChange={e => setCostModel({ ...costModel, exchange_txn_bps: parseFloat(e.target.value) })}
                  className="w-full accent-sky-500 cursor-pointer"
                />
              </div>

              {/* GST rate */}
              <div className="p-2.5 rounded bg-quant-card border border-quant-border font-mono text-[11px] text-quant-muted">
                <div className="flex justify-between">
                  <span>Statutory GST:</span>
                  <span className="text-slate-200 font-bold">18.0% on (Brokerage + Exchange)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="p-4 border-t border-quant-border bg-quant-card/40 flex items-center justify-between gap-3">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded bg-quant-surface hover:bg-quant-border text-slate-300 text-xs font-medium transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>

          <button
            onClick={handleSave}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow-lg shadow-sky-600/20 transition cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Apply & Recalculate</span>
          </button>
        </div>
      </div>
    </div>
  );
};

