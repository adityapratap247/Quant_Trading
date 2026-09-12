import React, { useState } from 'react';
import { Download, Filter, Search, ArrowUpRight, ArrowDownRight, Tag } from 'lucide-react';
import { BlotterRow } from '../types/quant';

interface TradeBlotterProps {
  blotter: BlotterRow[];
}

export const TradeBlotter: React.FC<TradeBlotterProps> = ({ blotter }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sideFilter, setSideFilter] = useState<'ALL' | 'BUY' | 'SELL'>('ALL');

  const filteredBlotter = React.useMemo(() => {
    return blotter.filter(row => {
      const matchesSearch =
        row.reason.toLowerCase().includes(searchTerm.toLowerCase()) ||
        row.timestamp.includes(searchTerm) ||
        row.side.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSide = sideFilter === 'ALL' || row.side === sideFilter;
      return matchesSearch && matchesSide;
    });
  }, [blotter, searchTerm, sideFilter]);

  const handleExportCSV = () => {
    const headers = ['bar_index', 'timestamp', 'side', 'qty', 'fill_price', 'cost', 'reason'];
    const rows = blotter.map(r => [
      r.bar_index,
      `"${r.timestamp}"`,
      r.side,
      r.qty,
      r.fill_price,
      r.cost,
      `"${r.reason}"`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `trade_blotter_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-quant-card/70 border border-quant-border rounded-lg p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            EXECUTION TRADE BLOTTER
            <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              {filteredBlotter.length} Fills Recorded
            </span>
          </h2>
          <p className="text-xs text-quant-muted">
            Auditable log of executed orders, slippage-adjusted fill prices, and statutory costs down to the paisa
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search bar */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-quant-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter reason, side..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="bg-quant-surface border border-quant-border rounded-md pl-8 pr-3 py-1 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-sky-500 w-44"
            />
          </div>

          {/* Side Filter */}
          <div className="flex rounded-md bg-quant-surface p-0.5 border border-quant-border text-xs">
            {(['ALL', 'BUY', 'SELL'] as const).map(s => (
              <button
                key={s}
                onClick={() => setSideFilter(s)}
                className={`px-2 py-0.5 rounded cursor-pointer ${
                  sideFilter === s ? 'bg-sky-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Export button */}
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-quant-surface hover:bg-quant-border border border-quant-border text-xs text-slate-300 transition cursor-pointer"
            title="Download CSV for Excel / desk spreadsheet reconciliation"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[320px] rounded border border-quant-border">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-quant-surface text-quant-muted sticky top-0 border-b border-quant-border select-none">
            <tr>
              <th className="py-2 px-3 font-semibold">Bar #</th>
              <th className="py-2 px-3 font-semibold">Timestamp (t+1 Open)</th>
              <th className="py-2 px-3 font-semibold">Side</th>
              <th className="py-2 px-3 font-semibold">Qty</th>
              <th className="py-2 px-3 font-semibold text-right">Fill Price (INR)</th>
              <th className="py-2 px-3 font-semibold text-right">Friction Cost (INR)</th>
              <th className="py-2 px-3 font-semibold">Reason / Intent</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-quant-border/60">
            {filteredBlotter.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-quant-muted">
                  No orders match the current filter criteria.
                </td>
              </tr>
            ) : (
              filteredBlotter.map((row, idx) => {
                const isBuy = row.side === 'BUY';
                return (
                  <tr key={idx} className="hover:bg-quant-surface/50 transition">
                    <td className="py-2 px-3 text-quant-muted">#{row.bar_index}</td>
                    <td className="py-2 px-3 text-slate-300">{row.timestamp}</td>
                    <td className="py-2 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${
                          isBuy
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}
                      >
                        {isBuy ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {row.side}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-medium text-slate-200">{row.qty.toFixed(1)}</td>
                    <td className="py-2 px-3 text-right text-slate-100 font-medium">
                      ₹{row.fill_price.toFixed(4)}
                    </td>
                    <td className="py-2 px-3 text-right text-violet-300">
                      ₹{row.cost.toFixed(4)}
                    </td>
                    <td className="py-2 px-3">
                      <span className="inline-flex items-center gap-1 text-[11px] text-sky-300 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                        <Tag className="w-2.5 h-2.5" />
                        {row.reason}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

