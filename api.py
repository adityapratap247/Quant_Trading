"""
FastAPI backend for the Quant Execution Engine & Backtest Dashboard.
Exposes REST endpoints for backtesting, walk-forward evaluation,
order-book crash reconciliation, and static frontend serving.

Usage:
    pip install fastapi uvicorn
    python api.py
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
except ImportError:
    print("FastAPI or Uvicorn is not installed. To run the API server, run:\n    pip install fastapi uvicorn")

from src.data import generate_ohlcv
from src.engine import EngineConfig, GridReverseEngine
from src.costs import CostModel
from src.backtest import run_backtest, run_walk_forward, compute_signal_frame
from src.indicators import rsi, obv
from src.orders import OrderManager, Side, OrderStatus

app = FastAPI(
    title="Quant Execution Engine API",
    description="Bar-accurate backtesting, grid+SAR execution, and order reconciliation service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache synthetic data
_DATA_DF = generate_ohlcv(n_bars=600, seed=42)
_SIGNAL_DF = compute_signal_frame(_DATA_DF)
_SIGNAL_DF["rsi"] = rsi(_SIGNAL_DF["close"], period=14)
_SIGNAL_DF["obv"] = obv(_SIGNAL_DF["close"], _SIGNAL_DF["volume"])


class EngineConfigSchema(BaseModel):
    strategy_id: str = "grid_sar_v1"
    base_qty: float = 1.0
    atr_multiplier: float = 1.0
    stop_multiplier: float = 2.5
    max_pyramids: int = 4
    position_cap: float = 5.0
    kill_switch_dd_pct: float = 0.15


class CostModelSchema(BaseModel):
    slippage_bps: float = 2.0
    brokerage_per_order: float = 20.0
    stt_ctt_bps: float = 1.0
    exchange_txn_bps: float = 0.35
    gst_rate: float = 0.18


class BacktestRequest(BaseModel):
    engine_config: EngineConfigSchema = EngineConfigSchema()
    cost_model: CostModelSchema = CostModelSchema()
    starting_cash: float = 1_000_000.0
    contract_multiplier: float = 25.0
    n_bars: Optional[int] = 600
    seed: Optional[int] = 42


class WalkForwardRequest(BaseModel):
    engine_config: EngineConfigSchema = EngineConfigSchema()
    cost_model: CostModelSchema = CostModelSchema()
    n_folds: int = 4
    starting_cash: float = 1_000_000.0


@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "engine": "GridReverseEngine (ATR spacing + pyramiding + SAR)",
        "cost_model": "Indian Market (Slippage + Brokerage + STT/CTT + Exchange + GST)",
        "bars_loaded": len(_DATA_DF),
        "lookahead_free": True,
        "idempotent_orders": True,
    }


@app.get("/api/data")
def get_market_data():
    bars = []
    for ts, row in _SIGNAL_DF.iterrows():
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
    return {"bars": bars}


@app.post("/api/backtest")
def run_backtest_endpoint(req: BacktestRequest):
    df = generate_ohlcv(n_bars=req.n_bars, seed=req.seed) if (req.n_bars != 600 or req.seed != 42) else _DATA_DF

    cfg = EngineConfig(
        strategy_id=req.engine_config.strategy_id,
        base_qty=req.engine_config.base_qty,
        atr_multiplier=req.engine_config.atr_multiplier,
        stop_multiplier=req.engine_config.stop_multiplier,
        max_pyramids=req.engine_config.max_pyramids,
        position_cap=req.engine_config.position_cap,
        kill_switch_dd_pct=req.engine_config.kill_switch_dd_pct,
    )

    cost = CostModel(
        slippage_bps=req.cost_model.slippage_bps,
        brokerage_per_order=req.cost_model.brokerage_per_order,
        stt_ctt_bps=req.cost_model.stt_ctt_bps,
        exchange_txn_bps=req.cost_model.exchange_txn_bps,
        gst_rate=req.cost_model.gst_rate,
    )

    result = run_backtest(df, cfg, cost, starting_cash=req.starting_cash, contract_multiplier=req.contract_multiplier)
    metrics = result.metrics()

    blotter = [
        {
            "bar_index": r.bar_index,
            "timestamp": str(r.timestamp),
            "side": r.side,
            "qty": r.qty,
            "fill_price": round(float(r.fill_price), 4),
            "cost": round(float(r.cost), 4),
            "reason": r.reason,
        }
        for r in result.blotter
    ]

    equity_curve = [
        {"timestamp": str(ts), "equity": round(float(val), 2)}
        for ts, val in result.equity_curve.items()
    ]

    return {
        "metrics": metrics,
        "blotter": blotter,
        "equity_curve": equity_curve,
        "kill_switch_fired": result.kill_switch_fired,
        "kill_switch_bar": result.kill_switch_bar,
    }


@app.post("/api/walk-forward")
def run_walk_forward_endpoint(req: WalkForwardRequest):
    cfg = EngineConfig(
        strategy_id=req.engine_config.strategy_id,
        base_qty=req.engine_config.base_qty,
        atr_multiplier=req.engine_config.atr_multiplier,
        stop_multiplier=req.engine_config.stop_multiplier,
        max_pyramids=req.engine_config.max_pyramids,
        position_cap=req.engine_config.position_cap,
        kill_switch_dd_pct=req.engine_config.kill_switch_dd_pct,
    )
    cost = CostModel(
        slippage_bps=req.cost_model.slippage_bps,
        brokerage_per_order=req.cost_model.brokerage_per_order,
        stt_ctt_bps=req.cost_model.stt_ctt_bps,
        exchange_txn_bps=req.cost_model.exchange_txn_bps,
        gst_rate=req.cost_model.gst_rate,
    )
    folds = run_walk_forward(_DATA_DF, cfg, cost, n_folds=req.n_folds, starting_cash=req.starting_cash)
    return {"folds": folds}


@app.post("/api/reconcile")
def run_reconciliation_simulation():
    """Simulate a mid-session crash and demonstrate broker truth reconciliation."""
    cfg = EngineConfig()
    cost = CostModel()
    
    # Run first 50 bars
    sub_df = _DATA_DF.iloc[:50]
    result = run_backtest(sub_df, cfg, cost)
    
    # Create simulated broker snapshot
    broker_snapshot = {}
    for row in result.blotter:
        # Build client order id
        from src.orders import make_client_order_id
        coid = make_client_order_id(cfg.strategy_id, row.bar_index, row.reason)
        broker_snapshot[coid] = {
            "status": "FILLED",
            "fill_price": row.fill_price,
            "broker_order_id": f"BROKER-NSE-{coid[:8]}",
            "side": row.side,
            "qty": row.qty,
            "reason": row.reason,
            "bar_index": row.bar_index,
        }
        
    # Inject 1 unknown order filled on broker side (e.g. sent just before crash)
    ghost_coid = "ghost_order_99a8b"
    broker_snapshot[ghost_coid] = {
        "status": "FILLED",
        "fill_price": 1005.50,
        "broker_order_id": "BROKER-NSE-RECOVERED-01",
        "side": "BUY",
        "qty": 1.0,
        "reason": "emergency_hedging",
        "bar_index": 48,
    }
    
    # New clean order manager after simulated restart
    restarted_om = OrderManager()
    
    # Perform reconciliation
    notes = restarted_om.reconcile(broker_snapshot)
    reconciled_position = restarted_om.net_position()
    
    return {
        "status": "success",
        "total_broker_orders": len(broker_snapshot),
        "notes": notes,
        "reconciled_position": reconciled_position,
        "orders": [
            {
                "client_order_id": o.client_order_id,
                "side": o.side.value,
                "qty": o.qty,
                "status": o.status.value,
                "fill_price": o.fill_price,
                "broker_order_id": o.broker_order_id,
                "reason": o.reason,
            }
            for o in restarted_om.orders.values()
        ],
    }


# Static frontend serving if built
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Quant Engine API at http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

