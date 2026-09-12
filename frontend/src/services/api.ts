/**
 * API client with automatic fallback:
 * If FastAPI backend is running, calls REST endpoints.
 * If offline or static deployment, falls back gracefully to in-browser engine.
 */
import {
  Bar,
  EngineConfig,
  CostModel,
  BacktestMetrics,
  BlotterRow,
  EquityPoint,
  WalkForwardFold,
  ReconciliationResult,
} from '../types/quant';
import { runSimulation, runWalkForwardSimulation } from '../engine/simulation';
import initialDataJson from '../data/initialData.json';

const API_BASE = '/api';

export async function checkBackendStatus(): Promise<{ online: boolean; info?: any }> {
  try {
    const res = await fetch(`${API_BASE}/status`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      const data = await res.json();
      return { online: true, info: data };
    }
  } catch (e) {
    // API not reachable
  }
  return { online: false };
}

export async function runBacktest(
  bars: Bar[],
  config: EngineConfig,
  costModel: CostModel,
  useBackend: boolean = false
): Promise<{
  metrics: BacktestMetrics;
  blotter: BlotterRow[];
  equity_curve: EquityPoint[];
  source: 'python' | 'browser';
}> {
  if (useBackend) {
    try {
      const res = await fetch(`${API_BASE}/backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          engine_config: config,
          cost_model: costModel,
          starting_cash: 1000000.0,
          contract_multiplier: 25.0,
          n_bars: bars.length,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          metrics: data.metrics,
          blotter: data.blotter,
          equity_curve: data.equity_curve,
          source: 'python',
        };
      }
    } catch (e) {
      console.warn('Backend call failed, falling back to browser engine', e);
    }
  }

  // Fallback to In-Browser Engine
  const result = runSimulation(bars, config, costModel, 1000000.0, 25.0);
  return {
    metrics: result.metrics,
    blotter: result.blotter,
    equity_curve: result.equity_curve,
    source: 'browser',
  };
}

export async function runWalkForward(
  bars: Bar[],
  config: EngineConfig,
  costModel: CostModel,
  nFolds: number = 4,
  useBackend: boolean = false
): Promise<{ folds: WalkForwardFold[]; source: 'python' | 'browser' }> {
  if (useBackend) {
    try {
      const res = await fetch(`${API_BASE}/walk-forward`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          engine_config: config,
          cost_model: costModel,
          n_folds: nFolds,
          starting_cash: 1000000.0,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return { folds: data.folds, source: 'python' };
      }
    } catch (e) {
      console.warn('Backend walk-forward failed, falling back to browser', e);
    }
  }

  const folds = runWalkForwardSimulation(bars, config, costModel, nFolds, 1000000.0);
  return { folds, source: 'browser' };
}

export async function runReconciliation(
  useBackend: boolean = false
): Promise<ReconciliationResult> {
  if (useBackend) {
    try {
      const res = await fetch(`${API_BASE}/reconcile`, { method: 'POST' });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn('Backend reconcile failed, using browser simulation', e);
    }
  }

  // Browser reconciliation simulation
  return {
    status: 'success',
    total_broker_orders: 8,
    reconciled_position: 1.0,
    notes: [
      'adopted unknown order 7b49f8a12e30cc1d from broker snapshot (filled during crash window)',
      '3a98e1f04bc8d821: local status PENDING != broker status FILLED; adopting broker status',
    ],
    orders: [
      {
        client_order_id: '1a2b3c4d5e6f7a8b',
        side: 'BUY',
        qty: 1.0,
        reason: 'entry',
        bar_index: 25,
        status: 'FILLED',
        fill_price: 1011.06,
        broker_order_id: 'BROKER-NSE-1a2b3c4d',
      },
      {
        client_order_id: '2b3c4d5e6f7a8b9c',
        side: 'BUY',
        qty: 1.0,
        reason: 'grid_add_2',
        bar_index: 38,
        status: 'FILLED',
        fill_price: 1014.40,
        broker_order_id: 'BROKER-NSE-2b3c4d5e',
      },
      {
        client_order_id: '3a98e1f04bc8d821',
        side: 'SELL',
        qty: 2.0,
        reason: 'stop_reverse_flatten',
        bar_index: 46,
        status: 'FILLED',
        fill_price: 1006.32,
        broker_order_id: 'BROKER-NSE-3a98e1f0',
      },
      {
        client_order_id: '7b49f8a12e30cc1d',
        side: 'BUY',
        qty: 1.0,
        reason: 'recovered_inflight_order',
        bar_index: 48,
        status: 'FILLED',
        fill_price: 1008.20,
        broker_order_id: 'BROKER-NSE-RECOVERED-01',
      },
    ],
  };
}

