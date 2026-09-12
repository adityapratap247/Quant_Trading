import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { EquityPoint } from '../types/quant';

interface EquityChartProps {
  data: EquityPoint[];
  startingCash?: number;
}

function formatINR(val: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(val);
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const equity = data.equity;
    const peak = data.peak || equity;
    const dd = data.drawdown !== undefined ? data.drawdown : 0;

    return (
      <div className="bg-quant-surface border border-quant-border p-3 rounded shadow-xl text-xs font-mono">
        <div className="text-quant-muted mb-1">{data.timestamp}</div>
        <div className="flex items-center justify-between gap-4 py-0.5">
          <span className="text-sky-400 font-medium">Equity:</span>
          <span className="font-bold text-white">{formatINR(equity)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 py-0.5">
          <span className="text-slate-400">Peak Watermark:</span>
          <span className="text-slate-300">{formatINR(peak)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 py-0.5">
          <span className="text-rose-400">Drawdown:</span>
          <span className="text-rose-400 font-bold">{dd.toFixed(2)}%</span>
        </div>
      </div>
    );
  }
  return null;
};

export const EquityChart: React.FC<EquityChartProps> = ({ data, startingCash = 1000000.0 }) => {
  // Downsample if more than 300 points for ultra-smooth rendering
  const chartData = React.useMemo(() => {
    if (data.length <= 300) return data;
    const step = Math.ceil(data.length / 300);
    return data.filter((_, idx) => idx % step === 0 || idx === data.length - 1);
  }, [data]);

  const minEquity = Math.min(...data.map(d => d.equity), startingCash * 0.98);
  const maxEquity = Math.max(...data.map(d => d.equity), startingCash * 1.01);

  return (
    <div className="bg-quant-card/70 border border-quant-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            PORTFOLIO EQUITY CURVE (MARK-TO-MARKET)
            <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono">
              Bar-by-Bar Valuation (INR)
            </span>
          </h2>
          <p className="text-xs text-quant-muted">
            Strict causal mark using bar close prices before next-bar decision execution
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block"></span>
            <span className="text-slate-300">Equity</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 border-t border-dashed border-slate-500 inline-block"></span>
            <span className="text-slate-400">Peak Watermark</span>
          </div>
        </div>
      </div>

      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 15, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
              </linearGradient>
            </defs>
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
              domain={[minEquity, maxEquity]}
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              tickFormatter={(val: number) => `₹${(val / 1000).toFixed(1)}k`}
              orientation="right"
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#38bdf8"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#equityGradient)"
            />
            <Line
              type="stepAfter"
              dataKey="peak"
              stroke="#64748b"
              strokeDasharray="4 4"
              strokeWidth={1}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

