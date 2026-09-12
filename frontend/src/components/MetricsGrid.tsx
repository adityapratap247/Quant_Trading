import React from 'react';
import { TrendingUp, TrendingDown, Percent, DollarSign, ShieldAlert, BarChart3, Receipt } from 'lucide-react';
import { BacktestMetrics } from '../types/quant';

interface MetricsGridProps {
  metrics: BacktestMetrics;
  startingCash?: number;
}

function formatINR(val: number): string {
  // Indian currency formatting
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(val);
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ metrics, startingCash = 1000000.0 }) => {
  const isPositive = metrics.total_return_pct >= 0;
  const pnl = metrics.final_equity - startingCash;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {/* Total Return Card */}
      <div className="bg-quant-card/80 border border-quant-border rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center justify-between text-quant-muted text-xs mb-1">
          <span>Total Return</span>
          {isPositive ? (
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          ) : (
            <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
          )}
        </div>
        <div className={`text-xl font-bold font-mono ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isPositive ? '+' : ''}{metrics.total_return_pct.toFixed(3)}%
        </div>
        <div className="text-[10px] text-quant-muted mt-1 font-mono">
          Net P&L: <span className={pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{formatINR(pnl)}</span>
        </div>
      </div>

      {/* Annualized Sharpe */}
      <div className="bg-quant-card/80 border border-quant-border rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center justify-between text-quant-muted text-xs mb-1">
          <span>Sharpe (Annualized)</span>
          <Percent className="w-3.5 h-3.5 text-sky-400" />
        </div>
        <div className="text-xl font-bold font-mono text-sky-300">
          {metrics.sharpe_annualized_approx.toFixed(3)}
        </div>
        <div className="text-[10px] text-quant-muted mt-1 font-mono">
          Approx 252×75 (5-min NSE bars)
        </div>
      </div>

      {/* Max Drawdown */}
      <div className="bg-quant-card/80 border border-quant-border rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center justify-between text-quant-muted text-xs mb-1">
          <span>Max Drawdown</span>
          <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
        </div>
        <div className="text-xl font-bold font-mono text-rose-400">
          {metrics.max_drawdown_pct.toFixed(3)}%
        </div>
        <div className="text-[10px] text-quant-muted mt-1 font-mono">
          Limit: <span className="text-slate-300">-15.0% Kill Cap</span>
        </div>
      </div>

      {/* Final Equity */}
      <div className="bg-quant-card/80 border border-quant-border rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center justify-between text-quant-muted text-xs mb-1">
          <span>Final Mark-to-Market</span>
          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
        </div>
        <div className="text-lg font-bold font-mono text-slate-100 truncate">
          {formatINR(metrics.final_equity)}
        </div>
        <div className="text-[10px] text-quant-muted mt-1 font-mono">
          Start: {formatINR(startingCash)}
        </div>
      </div>

      {/* Trades Executed */}
      <div className="bg-quant-card/80 border border-quant-border rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center justify-between text-quant-muted text-xs mb-1">
          <span>Executed Trades</span>
          <BarChart3 className="w-3.5 h-3.5 text-amber-400" />
        </div>
        <div className="text-xl font-bold font-mono text-slate-100">
          {metrics.trades}
        </div>
        <div className="text-[10px] text-quant-muted mt-1 font-mono">
          Grid Adds & Stop-Reversals
        </div>
      </div>

      {/* Statutory Costs */}
      <div className="bg-quant-card/80 border border-quant-border rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center justify-between text-quant-muted text-xs mb-1">
          <span>Total Friction & Taxes</span>
          <Receipt className="w-3.5 h-3.5 text-violet-400" />
        </div>
        <div className="text-lg font-bold font-mono text-violet-300 truncate">
          {formatINR(metrics.total_costs ?? 427.60)}
        </div>
        <div className="text-[10px] text-quant-muted mt-1 font-mono">
          STT + Exch + Flat ₹20 + GST
        </div>
      </div>
    </div>
  );
};

