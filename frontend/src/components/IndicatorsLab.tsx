import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { Bar } from '../types/quant';

interface IndicatorsLabProps {
  bars: Bar[];
}

export const IndicatorsLab: React.FC<IndicatorsLabProps> = ({ bars }) => {
  const [activeTab, setActiveTab] = useState<'rsi' | 'atr' | 'obv' | 'trend'>('rsi');

  const chartData = React.useMemo(() => {
    if (bars.length <= 300) return bars;
    const step = Math.ceil(bars.length / 300);
    return bars.filter((_, idx) => idx % step === 0 || idx === bars.length - 1);
  }, [bars]);

  return (
    <div className="bg-quant-card/70 border border-quant-border rounded-lg p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            TECHNICAL ANALYSIS LAB (TA MODULE)
            <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">
              Pure Causal Mathematical Indicators
            </span>
          </h2>
          <p className="text-xs text-quant-muted">
            One tested implementation per indicator family • Zero duplicated math • Causal (no lookahead)
          </p>
        </div>

        {/* Tab Selector */}
        <div className="flex rounded-md bg-quant-surface p-1 border border-quant-border text-xs font-medium">
          <button
            onClick={() => setActiveTab('rsi')}
            className={`px-3 py-1 rounded transition cursor-pointer ${
              activeTab === 'rsi' ? 'bg-sky-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Momentum: RSI(14)
          </button>
          <button
            onClick={() => setActiveTab('atr')}
            className={`px-3 py-1 rounded transition cursor-pointer ${
              activeTab === 'atr' ? 'bg-sky-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Volatility: ATR(14)
          </button>
          <button
            onClick={() => setActiveTab('trend')}
            className={`px-3 py-1 rounded transition cursor-pointer ${
              activeTab === 'trend' ? 'bg-sky-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Trend: EMA 12/26 Spread
          </button>
          <button
            onClick={() => setActiveTab('obv')}
            className={`px-3 py-1 rounded transition cursor-pointer ${
              activeTab === 'obv' ? 'bg-sky-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Volume: OBV
          </button>
        </div>
      </div>

      <div className="h-[200px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
            <XAxis
              dataKey="timestamp"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              tickFormatter={(val: string) => val ? val.split(' ')[1]?.substring(0, 5) || val : ''}
              minTickGap={40}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-quant-surface border border-quant-border p-2 rounded shadow-xl text-xs font-mono">
                      <div className="text-quant-muted">{d.timestamp}</div>
                      {activeTab === 'rsi' && (
                        <div className="text-sky-400">RSI(14): <span className="font-bold text-white">{d.rsi ? d.rsi.toFixed(2) : 'Warmup'}</span></div>
                      )}
                      {activeTab === 'atr' && (
                        <div className="text-amber-400">ATR(14): <span className="font-bold text-white">₹{d.atr ? d.atr.toFixed(2) : 'Warmup'}</span></div>
                      )}
                      {activeTab === 'trend' && (
                        <div className="text-purple-400">Trend Bullish: <span className="font-bold text-white">{d.trend_bullish ? 'YES (EMA12 > EMA26)' : 'NO (Bearish)'}</span></div>
                      )}
                      {activeTab === 'obv' && (
                        <div className="text-emerald-400">OBV: <span className="font-bold text-white">{d.obv ? d.obv.toLocaleString() : 'Warmup'}</span></div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />

            {activeTab === 'rsi' && (
              <>
                <YAxis domain={[0, 100]} stroke="#64748b" fontSize={10} tickLine={false} orientation="right" />
                <ReferenceLine y={70} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: '70 (Overbought)', fill: '#f43f5e', fontSize: 10 }} />
                <ReferenceLine y={30} stroke="#10b981" strokeDasharray="3 3" label={{ value: '30 (Oversold)', fill: '#10b981', fontSize: 10 }} />
                <Line type="monotone" dataKey="rsi" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
              </>
            )}

            {activeTab === 'atr' && (
              <>
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} orientation="right" tickFormatter={(v) => `₹${v.toFixed(1)}`} />
                <Line type="monotone" dataKey="atr" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
              </>
            )}

            {activeTab === 'trend' && (
              <>
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} orientation="right" />
                <Line type="monotone" dataKey="ema_fast" stroke="#fbbf24" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="ema_slow" stroke="#c084fc" strokeWidth={1.5} dot={false} />
              </>
            )}

            {activeTab === 'obv' && (
              <>
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} orientation="right" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Line type="monotone" dataKey="obv" stroke="#10b981" strokeWidth={1.5} dot={false} />
              </>
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

