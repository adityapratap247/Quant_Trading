/**
 * Bar-accurate, lookahead-free Grid + Stop-and-Reverse execution engine
 * and backtest harness in TypeScript.
 * Matches src/engine.py and src/backtest.py.
 */
import {
  Bar,
  EngineConfig,
  CostModel,
  BlotterRow,
  EquityPoint,
  BacktestMetrics,
  WalkForwardFold,
} from '../types/quant';
import { CostCalculator } from './costs';
import { OrderManager } from './orders';
import { ema, atr } from './indicators';

export enum Direction {
  FLAT = 0,
  LONG = 1,
  SHORT = -1,
}

export interface EngineState {
  direction: Direction;
  units: number;
  entryReferencePrice: number | null;
  equityPeak: number;
  killed: boolean;
}

export class GridReverseEngine {
  public state: EngineState;

  constructor(public config: EngineConfig) {
    this.state = {
      direction: Direction.FLAT,
      units: 0,
      entryReferencePrice: null,
      equityPeak: 0.0,
      killed: false,
    };
  }

  updateEquityAndCheckKillSwitch(equity: number): boolean {
    const st = this.state;
    st.equityPeak = Math.max(st.equityPeak, equity);
    if (st.killed || st.equityPeak <= 0) return false;
    const drawdown = (st.equityPeak - equity) / st.equityPeak;
    if (drawdown >= this.config.kill_switch_dd_pct) {
      st.killed = true;
      return true;
    }
    return false;
  }

  forceFlatten(barIndex: number, orderManager: OrderManager) {
    const st = this.state;
    if (st.units === 0) return;
    const side = st.direction === Direction.LONG ? 'SELL' : 'BUY';
    const qty = this.config.base_qty * st.units;
    orderManager.place(side, qty, 'kill_switch_flatten', barIndex, this.config.strategy_id);
    st.units = 0;
    st.direction = Direction.FLAT;
    st.entryReferencePrice = null;
  }

  onBar(
    barIndex: number,
    close: number,
    atrValue: number | null,
    trendBullish: boolean | null,
    orderManager: OrderManager
  ) {
    const st = this.state;
    const cfg = this.config;

    if (st.killed) return;
    if (atrValue === null || trendBullish === null || atrValue <= 0) return;

    if (st.direction === Direction.FLAT) {
      const side = trendBullish ? 'BUY' : 'SELL';
      orderManager.place(side, cfg.base_qty, 'entry', barIndex, cfg.strategy_id);
      st.direction = trendBullish ? Direction.LONG : Direction.SHORT;
      st.units = 1;
      st.entryReferencePrice = close;
      return;
    }

    const ref = st.entryReferencePrice!;
    const gridSpacing = cfg.atr_multiplier * atrValue;
    const stopDistance = cfg.stop_multiplier * atrValue;

    if (st.direction === Direction.LONG) {
      const adverseMove = ref - close;
      const favourableMove = close - ref;

      if (adverseMove >= stopDistance) {
        this.stopAndReverse(barIndex, orderManager, Direction.SHORT, close);
        return;
      }

      if (favourableMove >= gridSpacing && st.units - 1 < cfg.max_pyramids) {
        const totalQtyIfAdded = cfg.base_qty * (st.units + 1);
        if (totalQtyIfAdded <= cfg.position_cap) {
          orderManager.place('BUY', cfg.base_qty, `grid_add_${st.units + 1}`, barIndex, cfg.strategy_id);
          st.units += 1;
          st.entryReferencePrice = close;
        }
      }
    } else {
      // SHORT
      const adverseMove = close - ref;
      const favourableMove = ref - close;

      if (adverseMove >= stopDistance) {
        this.stopAndReverse(barIndex, orderManager, Direction.LONG, close);
        return;
      }

      if (favourableMove >= gridSpacing && st.units - 1 < cfg.max_pyramids) {
        const totalQtyIfAdded = cfg.base_qty * (st.units + 1);
        if (totalQtyIfAdded <= cfg.position_cap) {
          orderManager.place('SELL', cfg.base_qty, `grid_add_${st.units + 1}`, barIndex, cfg.strategy_id);
          st.units += 1;
          st.entryReferencePrice = close;
        }
      }
    }
  }

  private stopAndReverse(barIndex: number, orderManager: OrderManager, toDirection: Direction, close: number) {
    const st = this.state;
    const cfg = this.config;
    const flattenSide = st.direction === Direction.LONG ? 'SELL' : 'BUY';
    const flattenQty = cfg.base_qty * st.units;
    orderManager.place(flattenSide, flattenQty, 'stop_reverse_flatten', barIndex, cfg.strategy_id);

    const entrySide = toDirection === Direction.LONG ? 'BUY' : 'SELL';
    orderManager.place(entrySide, cfg.base_qty, 'stop_reverse_entry', barIndex, cfg.strategy_id);

    st.direction = toDirection;
    st.units = 1;
    st.entryReferencePrice = close;
  }
}

export function runSimulation(
  rawBars: Bar[],
  config: EngineConfig,
  costModel: CostModel,
  startingCash: number = 1000000.0,
  contractMultiplier: number = 25.0
): {
  metrics: BacktestMetrics;
  blotter: BlotterRow[];
  equity_curve: EquityPoint[];
  kill_switch_fired: boolean;
  kill_switch_bar: number | null;
} {
  const costCalc = new CostCalculator(costModel);
  const engine = new GridReverseEngine(config);
  const om = new OrderManager();

  let cash = startingCash;
  let position = 0.0;
  const blotter: BlotterRow[] = [];
  const equityPoints: EquityPoint[] = [];

  let killSwitchFired = false;
  let killSwitchBar: number | null = null;
  let peakEquity = startingCash;

  const n = rawBars.length;
  for (let i = 0; i < n - 1; i++) {
    const bar = rawBars[i];
    const closeI = bar.close;
    const atrI = bar.atr ?? null;
    const trendI = bar.trend_bullish ?? null;

    // Mark to market equity at bar i close
    const equityNow = cash + position * closeI * contractMultiplier;
    peakEquity = Math.max(peakEquity, equityNow);
    const ddNow = peakEquity > 0 ? (equityNow - peakEquity) / peakEquity : 0;

    equityPoints.push({
      timestamp: bar.timestamp,
      equity: Number(equityNow.toFixed(2)),
      drawdown: Number((ddNow * 100).toFixed(3)),
      peak: Number(peakEquity.toFixed(2)),
    });

    if (!killSwitchFired) {
      const fired = engine.updateEquityAndCheckKillSwitch(equityNow);
      if (fired) {
        killSwitchFired = true;
        killSwitchBar = i;
        engine.forceFlatten(i, om);
      }
    }

    if (!killSwitchFired) {
      engine.onBar(i, closeI, atrI, trendI, om);
    }

    // Fill orders on bar i+1 open
    const nextOpen = rawBars[i + 1].open;
    for (const order of om.openOrders()) {
      const rawPrice = costCalc.slippedPrice(nextOpen, order.side);
      const cost = costCalc.totalCost(rawPrice, order.qty, order.side);
      om.markFilled(order.client_order_id, rawPrice, `SIM-${order.client_order_id}`);

      const signedQty = order.side === 'BUY' ? order.qty : -order.qty;
      cash -= signedQty * rawPrice * contractMultiplier;
      cash -= cost;
      position += signedQty;

      blotter.push({
        bar_index: i,
        timestamp: rawBars[i + 1].timestamp,
        side: order.side,
        qty: order.qty,
        fill_price: Number(rawPrice.toFixed(4)),
        cost: Number(cost.toFixed(4)),
        reason: order.reason,
      });
    }
  }

  // Final bar mark
  const finalEquity = cash + position * rawBars[n - 1].close * contractMultiplier;
  peakEquity = Math.max(peakEquity, finalEquity);
  equityPoints.push({
    timestamp: rawBars[n - 1].timestamp,
    equity: Number(finalEquity.toFixed(2)),
    drawdown: peakEquity > 0 ? Number((((finalEquity - peakEquity) / peakEquity) * 100).toFixed(3)) : 0,
    peak: Number(peakEquity.toFixed(2)),
  });

  // Calculate stats
  const totalReturnPct = ((finalEquity / startingCash) - 1.0) * 100.0;
  let minDD = 0.0;
  for (const pt of equityPoints) {
    if (pt.drawdown !== undefined && pt.drawdown < minDD) minDD = pt.drawdown;
  }

  // Calculate returns for Sharpe
  const rets: number[] = [];
  for (let i = 1; i < equityPoints.length; i++) {
    const prev = equityPoints[i - 1].equity;
    if (prev > 0) {
      rets.push((equityPoints[i].equity - prev) / prev);
    }
  }

  let sharpe = 0.0;
  if (rets.length > 1) {
    const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
    const variance = rets.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (rets.length - 1);
    const std = Math.sqrt(variance);
    if (std > 0) {
      const barsPerYear = 252 * 75;
      sharpe = (mean / std) * Math.sqrt(barsPerYear);
    }
  }

  let totalCosts = 0;
  for (const b of blotter) totalCosts += b.cost;

  const metrics: BacktestMetrics = {
    trades: blotter.length,
    total_return_pct: Number(totalReturnPct.toFixed(3)),
    max_drawdown_pct: Number(minDD.toFixed(3)),
    sharpe_annualized_approx: Number(sharpe.toFixed(3)),
    final_equity: Number(finalEquity.toFixed(2)),
    kill_switch_fired: killSwitchFired,
    total_costs: Number(totalCosts.toFixed(2)),
  };

  return {
    metrics,
    blotter,
    equity_curve: equityPoints,
    kill_switch_fired: killSwitchFired,
    kill_switch_bar: killSwitchBar,
  };
}

export function runWalkForwardSimulation(
  bars: Bar[],
  config: EngineConfig,
  costModel: CostModel,
  nFolds: number = 4,
  startingCash: number = 1000000.0
): WalkForwardFold[] {
  const warmup = 40;
  const n = bars.length;
  const usable = n - warmup;
  if (usable < nFolds * 10) return [];

  const foldSize = Math.floor(usable / nFolds);
  const folds: WalkForwardFold[] = [];
  let cursor = 0;

  for (let f = 0; f < nFolds; f++) {
    const start = cursor;
    const end = f < nFolds - 1 ? start + warmup + foldSize : n;
    const windowBars = bars.slice(start, Math.min(end, n));

    const res = runSimulation(windowBars, config, costModel, startingCash, 25.0);
    folds.push({
      fold: f,
      start: bars[start].timestamp,
      end: bars[Math.min(end, n) - 1].timestamp,
      bars: windowBars.length,
      trades: res.metrics.trades,
      total_return_pct: res.metrics.total_return_pct,
      max_drawdown_pct: res.metrics.max_drawdown_pct,
      sharpe_annualized_approx: res.metrics.sharpe_annualized_approx,
      final_equity: res.metrics.final_equity,
      kill_switch_fired: res.metrics.kill_switch_fired,
    });

    cursor = start + warmup + foldSize;
  }

  return folds;
}

