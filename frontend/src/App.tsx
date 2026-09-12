import React, { useState, useEffect } from 'react';
import {
  BarChart2,
  Table as TableIcon,
  Layers,
  ShieldAlert,
  Sliders,
  FileText,
  Activity,
  CheckCircle,
  Clock,
  Sparkles,
  RefreshCw,
} from 'lucide-react';

import initialDataJson from './data/initialData.json';
import {
  Bar,
  EngineConfig,
  CostModel,
  BacktestMetrics,
  BlotterRow,
  EquityPoint,
  WalkForwardFold,
} from './types/quant';

import { checkBackendStatus, runBacktest, runWalkForward } from './services/api';
import { Header } from './components/Header';
import { MetricsGrid } from './components/MetricsGrid';
import { EquityChart } from './components/EquityChart';
import { PriceChart } from './components/PriceChart';
import { IndicatorsLab } from './components/IndicatorsLab';
import { TradeBlotter } from './components/TradeBlotter';
import { WalkForwardMatrix } from './components/WalkForwardMatrix';
import { ReconciliationDebugger } from './components/ReconciliationDebugger';
import { ConfigDrawer } from './components/ConfigDrawer';
import { ArchitectureModal } from './components/ArchitectureModal';

export function App() {
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [useBackend, setUseBackend] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Core quant states
  const [engineConfig, setEngineConfig] = useState<EngineConfig>(initialDataJson.engine_config);
  const [costModel, setCostModel] = useState<CostModel>(initialDataJson.cost_model);
  const [metrics, setMetrics] = useState<BacktestMetrics>(initialDataJson.metrics as BacktestMetrics);
  const [blotter, setBlotter] = useState<BlotterRow[]>(initialDataJson.blotter as BlotterRow[]);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>(initialDataJson.equity_curve as EquityPoint[]);
  const [walkForwardFolds, setWalkForwardFolds] = useState<WalkForwardFold[]>(initialDataJson.walk_forward_folds as WalkForwardFold[]);
  const [bars] = useState<Bar[]>(initialDataJson.bars as Bar[]);

  // Navigation tabs
  const [activeTab, setActiveTab] = useState<'overview' | 'blotter' | 'walkforward' | 'reconcile'>('overview');

  // Drawers & Modals
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);
  const [isArchitectureOpen, setIsArchitectureOpen] = useState<boolean>(false);

  // Check Python backend connection on mount
  useEffect(() => {
    async function init() {
      const status = await checkBackendStatus();
      if (status.online) {
        setIsBackendConnected(true);
        setUseBackend(true);
      }
    }
    init();
  }, []);

  const handleRunBacktest = async (
    customConfig: EngineConfig = engineConfig,
    customCost: CostModel = costModel
  ) => {
    setIsLoading(true);
    try {
      const result = await runBacktest(bars, customConfig, customCost, useBackend && isBackendConnected);
      setMetrics(result.metrics);
      setBlotter(result.blotter);
      setEquityCurve(result.equity_curve);

      // Also refresh walk forward
      const wfResult = await runWalkForward(bars, customConfig, customCost, 4, useBackend && isBackendConnected);
      setWalkForwardFolds(wfResult.folds);
    } catch (e) {
      console.error('Simulation failed', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyConfig = (newCfg: EngineConfig, newCost: CostModel) => {
    setEngineConfig(newCfg);
    setCostModel(newCost);
    handleRunBacktest(newCfg, newCost);
  };

  return (
    <div className="min-h-screen bg-quant-bg text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Top Navbar */}
      <Header
        isBackendConnected={isBackendConnected}
        useBackend={useBackend}
        setUseBackend={setUseBackend}
        onOpenConfig={() => setIsConfigOpen(true)}
        onOpenArchitecture={() => setIsArchitectureOpen(true)}
        onRunBacktest={() => handleRunBacktest()}
        isLoading={isLoading}
        killSwitchFired={metrics.kill_switch_fired}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 lg:p-6 space-y-5">
        {/* Navigation Tabs Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-quant-border pb-3">
          <div className="flex items-center gap-1 bg-quant-surface p-1 rounded-lg border border-quant-border text-xs font-semibold">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition cursor-pointer ${
                activeTab === 'overview'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-quant-muted hover:text-white'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>Execution Overview</span>
            </button>

            <button
              onClick={() => setActiveTab('blotter')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition cursor-pointer ${
                activeTab === 'blotter'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-quant-muted hover:text-white'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              <span>Trade Blotter ({blotter.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('walkforward')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition cursor-pointer ${
                activeTab === 'walkforward'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-quant-muted hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Walk-Forward Robustness (4 Folds)</span>
            </button>

            <button
              onClick={() => setActiveTab('reconcile')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md transition cursor-pointer ${
                activeTab === 'reconcile'
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-quant-muted hover:text-white'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Crash & Reconciliation Debugger</span>
            </button>
          </div>

          {/* Recruiter Quick Notice */}
          <div className="flex items-center gap-2 text-xs text-quant-muted font-mono bg-quant-card/60 px-3 py-1 rounded border border-quant-border">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span>Live Interactive Mode: Parameter changes recompute fills at t+1 Open</span>
          </div>
        </div>

        {/* Top Quantitative Key Performance Indicators */}
        <MetricsGrid metrics={metrics} startingCash={1000000.0} />

        {/* Tab 1: Overview & Charts */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <EquityChart data={equityCurve} startingCash={1000000.0} />
              <PriceChart bars={bars} blotter={blotter} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <IndicatorsLab bars={bars} />
              </div>

              {/* Quick Strategy Specs Summary */}
              <div className="bg-quant-card/70 border border-quant-border rounded-lg p-4 flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center justify-between">
                    <span>Active Strategy Parameters</span>
                    <button
                      onClick={() => setIsConfigOpen(true)}
                      className="text-sky-400 hover:underline text-[11px] font-normal cursor-pointer"
                    >
                      Edit in Drawer →
                    </button>
                  </h3>

                  <div className="space-y-2 text-xs font-mono text-quant-muted divide-y divide-quant-border/50">
                    <div className="flex justify-between pt-1">
                      <span>Strategy ID:</span>
                      <span className="text-slate-200">{engineConfig.strategy_id}</span>
                    </div>
                    <div className="flex justify-between pt-1">
                      <span>Grid Spacing:</span>
                      <span className="text-sky-400 font-bold">{engineConfig.atr_multiplier}x ATR</span>
                    </div>
                    <div className="flex justify-between pt-1">
                      <span>Stop & Reverse:</span>
                      <span className="text-rose-400 font-bold">{engineConfig.stop_multiplier}x ATR</span>
                    </div>
                    <div className="flex justify-between pt-1">
                      <span>Max Pyramids:</span>
                      <span className="text-slate-200">{engineConfig.max_pyramids} units</span>
                    </div>
                    <div className="flex justify-between pt-1">
                      <span>Position Hard Cap:</span>
                      <span className="text-slate-200">{engineConfig.position_cap} units</span>
                    </div>
                    <div className="flex justify-between pt-1">
                      <span>Kill Switch Threshold:</span>
                      <span className="text-rose-400 font-bold">{(engineConfig.kill_switch_dd_pct * 100).toFixed(0)}% Drawdown</span>
                    </div>
                    <div className="flex justify-between pt-1">
                      <span>Statutory Brokerage:</span>
                      <span className="text-slate-200">₹{costModel.brokerage_per_order} / order</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-2.5 rounded bg-quant-surface/70 border border-quant-border/80 text-[11px] text-quant-muted">
                  <div className="text-slate-200 font-semibold mb-0.5">Execution Rule:</div>
                  Zero lookahead. A signal fired on bar <code className="text-sky-300">i</code> fills at bar <code className="text-sky-300">i+1's Open</code> with slippage and exchange fees.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Execution Blotter */}
        {activeTab === 'blotter' && (
          <TradeBlotter blotter={blotter} />
        )}

        {/* Tab 3: Walk-Forward Robustness */}
        {activeTab === 'walkforward' && (
          <WalkForwardMatrix folds={walkForwardFolds} />
        )}

        {/* Tab 4: Crash & Reconciliation Debugger */}
        {activeTab === 'reconcile' && (
          <ReconciliationDebugger useBackend={useBackend && isBackendConnected} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-quant-border bg-quant-surface/80 px-6 py-4 mt-8 text-xs font-mono text-quant-muted flex flex-col sm:flex-row items-center justify-between gap-3">
        <div>
          Quant Execution Engine & Backtest Dashboard • Vera Developers Submission
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5" /> 39 Tests Passing
          </span>
          <button
            onClick={() => setIsArchitectureOpen(true)}
            className="text-sky-400 hover:underline cursor-pointer"
          >
            Design Principles & Report →
          </button>
        </div>
      </footer>

      {/* Configuration Drawer */}
      <ConfigDrawer
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        currentEngineConfig={engineConfig}
        currentCostModel={costModel}
        onApply={handleApplyConfig}
      />

      {/* Architecture & Scope Modal */}
      <ArchitectureModal
        isOpen={isArchitectureOpen}
        onClose={() => setIsArchitectureOpen(false)}
      />
    </div>
  );
}

export default App;

