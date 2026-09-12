"""
Export complete backtest data to JSON for the frontend dashboard.
Computes ground truth OHLCV, indicators, execution blotter, equity curve,
and walk-forward analysis using the Python quant engine.
"""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
import numpy as np

from src.data import generate_ohlcv
from src.engine import EngineConfig
from src.costs import CostModel
from src.backtest import run_backtest, run_walk_forward, compute_signal_frame
from src.indicators import rsi, obv

OUTPUT_DIR = Path(__file__).parent / "frontend" / "src" / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "initialData.json"


def export():
    print("Generating synthetic OHLCV data...")
    df = generate_ohlcv(n_bars=600, seed=42)

    engine_config = EngineConfig(
        strategy_id="grid_sar_v1",
        base_qty=1.0,
        atr_multiplier=1.0,
        stop_multiplier=2.5,
        max_pyramids=4,
        position_cap=5.0,
        kill_switch_dd_pct=0.15,
    )
    cost_model = CostModel(
        slippage_bps=2.0,
        brokerage_per_order=20.0,
        stt_ctt_bps=1.0,
        exchange_txn_bps=0.35,
        gst_rate=0.18,
    )

    print("Computing signal frame & indicators...")
    sig = compute_signal_frame(df)
    sig["rsi"] = rsi(sig["close"], period=14)
    sig["obv"] = obv(sig["close"], sig["volume"])

    print("Running full-sample backtest...")
    result = run_backtest(df, engine_config, cost_model, starting_cash=1_000_000.0, contract_multiplier=25.0)
    metrics = result.metrics()

    print("Running walk-forward evaluation...")
    fold_metrics = run_walk_forward(df, engine_config, cost_model, n_folds=4, starting_cash=1_000_000.0)

    # Format bars
    bars = []
    for ts, row in sig.iterrows():
        bars.append({
            "timestamp": str(ts),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": int(row["volume"]),
            "ema_fast": round(float(row["ema_fast"]), 2) if pd.notna(row["ema_fast"]) else None,
            "ema_slow": round(float(row["ema_slow"]), 2) if pd.notna(row["ema_slow"]) else None,
            "atr": round(float(row["atr"]), 2) if pd.notna(row["atr"]) else None,
            "trend_bullish": bool(row["trend_bullish"]) if pd.notna(row["trend_bullish"]) else None,
            "rsi": round(float(row["rsi"]), 2) if pd.notna(row["rsi"]) else None,
            "obv": float(row["obv"]) if pd.notna(row["obv"]) else None,
        })

    # Format blotter
    blotter = []
    for r in result.blotter:
        blotter.append({
            "bar_index": r.bar_index,
            "timestamp": str(r.timestamp),
            "side": r.side,
            "qty": r.qty,
            "fill_price": round(float(r.fill_price), 4),
            "cost": round(float(r.cost), 4),
            "reason": r.reason,
        })

    # Format equity curve
    equity_curve = []
    for ts, val in result.equity_curve.items():
        equity_curve.append({
            "timestamp": str(ts),
            "equity": round(float(val), 2),
        })

    export_payload = {
        "engine_config": vars(engine_config),
        "cost_model": vars(cost_model),
        "metrics": metrics,
        "walk_forward_folds": fold_metrics,
        "bars": bars,
        "blotter": blotter,
        "equity_curve": equity_curve,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(export_payload, f, indent=2)

    print(f"Data successfully exported to {OUTPUT_FILE} ({len(bars)} bars, {len(blotter)} trades)")


if __name__ == "__main__":
    export()

