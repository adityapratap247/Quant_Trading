export interface Bar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ema_fast?: number | null;
  ema_slow?: number | null;
  atr?: number | null;
  trend_bullish?: boolean | null;
  rsi?: number | null;
  obv?: number | null;
}

export interface EngineConfig {
  strategy_id: string;
  base_qty: number;
  atr_multiplier: number;
  stop_multiplier: number;
  max_pyramids: number;
  position_cap: number;
  kill_switch_dd_pct: number;
}

export interface CostModel {
  slippage_bps: number;
  brokerage_per_order: number;
  stt_ctt_bps: number;
  exchange_txn_bps: number;
  gst_rate: number;
}

export interface BlotterRow {
  bar_index: number;
  timestamp: string;
  side: 'BUY' | 'SELL';
  qty: number;
  fill_price: number;
  cost: number;
  reason: string;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown?: number;
  peak?: number;
}

export interface BacktestMetrics {
  trades: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  sharpe_annualized_approx: number;
  final_equity: number;
  kill_switch_fired: boolean;
  win_rate_pct?: number;
  profit_factor?: number;
  total_costs?: number;
}

export interface WalkForwardFold {
  fold: number;
  start: string;
  end: string;
  bars: number;
  trades: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  sharpe_annualized_approx: number;
  final_equity: number;
  kill_switch_fired: boolean;
}

export interface InitialData {
  engine_config: EngineConfig;
  cost_model: CostModel;
  metrics: BacktestMetrics;
  walk_forward_folds: WalkForwardFold[];
  bars: Bar[];
  blotter: BlotterRow[];
  equity_curve: EquityPoint[];
}

export interface OrderItem {
  client_order_id: string;
  side: 'BUY' | 'SELL';
  qty: number;
  reason: string;
  bar_index: number;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  fill_price?: number | null;
  broker_order_id?: string | null;
}

export interface ReconciliationResult {
  status: string;
  total_broker_orders: number;
  notes: string[];
  reconciled_position: number;
  orders: OrderItem[];
}

