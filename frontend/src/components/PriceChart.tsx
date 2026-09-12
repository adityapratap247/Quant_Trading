import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Scatter,
} from 'recharts';
import { Bar, BlotterRow } from '../types/quant';

interface PriceChartProps {
  bars: Bar[];
  blotter: BlotterRow[];
}

const PriceCustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-quant-surface border border-quant-border p-3 rounded shadow-xl text-xs font-mono">
        <div className="text-quant-muted mb-1">{data.timestamp}</div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          <div><span className="text-slate-400">Close:</span> <span className="text-white font-bold">₹{data.close.toFixed(2)}</span></div>
          <div><span className="text-slate-400">High:</span> <span className="text-emerald-400">₹{data.high.toFixed(2)}</span></div>
          <div><span className="text-slate-400">Low:</span> <span className="text-rose-400">₹{data.low.toFixed(2)}</span></div>
          <div><span className="text-slate-400">Open:</span> <span className="text-slate-200">₹{data.open.toFixed(2)}</span></div>
          {data.ema_fast && (
            <div><span className="text-amber-400">EMA(12):</span> <span className="text-slate-200">₹{data.ema_fast.toFixed(2)}</span></div>
          )}
          {data.ema_slow && (
            <div><span className="text-purple-400">EMA(26):</span> <span className="text-slate-200">₹{data.ema_slow.toFixed(2)}</span></div>
          )}
        </div>
        {data.tradeInfo && (
          <div className="mt-2 pt-2 border-t border-quant-border">
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                data.tradeInfo.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
              }`}
            >
              {data.tradeInfo.side} {data.tradeInfo.qty} Qty @ ₹{data.tradeInfo.fill_price.toFixed(2)}
            </span>
            <div className="text-[10px] text-quant-muted mt-1">
              Reason: <span className="text-sky-300">{data.tradeInfo.reason}</span>
            </div>
            <div className="text-[10px] text-quant-muted">
              Friction Cost: <span className="text-violet-300">₹{data.tradeInfo.cost.toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    );
  }
  return null;
};

export const PriceChart: React.FC<PriceChartProps> = ({ bars, blotter }) => {
  // Merge blotter fills into bar points for visualization
  const chartData = React.useMemo(() => {
    // Map timestamp -> trade
    const tradeMap = new Map<string, BlotterRow>();
    for (const b of blotter) {
      tradeMap.set(b.timestamp, b);
    }

    return bars.map((bar, idx) => {
      const trade = tradeMap.get(bar.timestamp);
      return {
        ...bar,
        index: idx,
        buyFill: trade && trade.side === 'BUY' ? trade.fill_price : null,
        sellFill: trade && trade.side === 'SELL' ? trade.fill_price : null,
        tradeInfo: trade,
      };
    });
  }, [bars, blotter]);

  // Downsample if more than 350 bars
  const renderedData = React.useMemo(() => {
    if (chartData.length <= 350) return chartData;
    const step = Math.ceil(chartData.length / 350);
    return chartData.filter((d, idx) => idx % step === 0 || d.tradeInfo !== undefined);
  }, [chartData]);

  const minPrice = Math.min(...bars.map(b => b.low)) * 0.995;
  const maxPrice = Math.max(...bars.map(b => b.high)) * 1.005;

  return (
    <div className="bg-quant-card/70 border border-quant-border rounded-lg p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            PRICE & EXECUTION OVERLAY
            <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              Fills @ Bar t+1 Open (No Lookahead)
            </span>
          </h2>
          <p className="text-xs text-quant-muted">
            Green triangles = BUY entries/pyramids • Red inverted triangles = SELL/stops/flattens
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-slate-300 inline-block"></span>
            <span className="text-slate-300">Close</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-amber-400 inline-block"></span>
            <span className="text-amber-400">EMA(12)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-purple-400 inline-block"></span>
            <span className="text-purple-400">EMA(26)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-emerald-400 rotate-45 inline-block"></span>
            <span className="text-emerald-400">BUY</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 bg-rose-400 rotate-45 inline-block"></span>
            <span className="text-rose-400">SELL</span>
          </div>
        </div>
      </div>

      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={renderedData} margin={{ top: 10, right: 10, left: 15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
            <XAxis
              dataKey="timestamp"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              tickFormatter={(val: string) => val ? val.split(' ')[1]?.substring(0, 5) || val : ''}
              minTickGap={40}
            />
            <YAxis
              domain={[minPrice, maxPrice]}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              tickFormatter={(val: number) => `₹${val.toFixed(0)}`}
              orientation="right"
            />
            <Tooltip content={<PriceCustomTooltip />} />

            <Line type="monotone" dataKey="close" stroke="#e2e8f0" strokeWidth={1.2} dot={false} />
            <Line type="monotone" dataKey="ema_fast" stroke="#fbbf24" strokeWidth={1} dot={false} />
            <Line type="monotone" dataKey="ema_slow" stroke="#c084fc" strokeWidth={1} dot={false} />

            {/* Buy execution markers */}
            <Scatter
              dataKey="buyFill"
              fill="#10b981"
              shape="triangle"
              legendType="none"
            />

            {/* Sell execution markers */}
            <Scatter
              dataKey="sellFill"
              fill="#f43f5e"
              shape="star"
              legendType="none"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

