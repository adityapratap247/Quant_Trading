"""
Entry point: generate data, run a full backtest and a walk-forward
evaluation, and write everything the PDF report needs into results/.

Usage: python run_backtest.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.backtest import run_backtest, run_walk_forward
from src.costs import CostModel
from src.data import generate_ohlcv
from src.engine import EngineConfig

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def main():
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

    # -- full-sample run --------------------------------------------------
    result = run_backtest(df, engine_config, cost_model, starting_cash=1_000_000.0, contract_multiplier=25.0)
    metrics = result.metrics()

    blotter_df = pd.DataFrame([vars(r) for r in result.blotter])
    blotter_df.to_csv(RESULTS_DIR / "blotter.csv", index=False)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(result.equity_curve.index.to_pydatetime(), result.equity_curve.values, color="#1f77b4")
    ax1.set_title("Equity curve -- grid + stop-and-reverse engine (synthetic data)")
    ax1.set_ylabel("Equity (INR)")
    ax1.grid(alpha=0.3)

    ax2.plot(df.index.to_pydatetime(), df["close"].values, color="#555555", linewidth=0.8)
    if not blotter_df.empty:
        buys = blotter_df[blotter_df["side"] == "BUY"]
        sells = blotter_df[blotter_df["side"] == "SELL"]
        buy_ts = pd.to_datetime(buys["timestamp"]).dt.to_pydatetime()
        sell_ts = pd.to_datetime(sells["timestamp"]).dt.to_pydatetime()
        ax2.scatter(buy_ts, buys["fill_price"].values, marker="^", color="green", s=25, label="BUY fill", zorder=5)
        ax2.scatter(sell_ts, sells["fill_price"].values, marker="v", color="red", s=25, label="SELL fill", zorder=5)
    ax2.set_title("Price with fills")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "equity_curve.png", dpi=140)
    plt.close(fig)

    # -- walk-forward -------------------------------------------------
    fold_metrics = run_walk_forward(df, engine_config, cost_model, n_folds=4, starting_cash=1_000_000.0)

    summary = {
        "engine_config": vars(engine_config),
        "cost_model": vars(cost_model),
        "full_sample_metrics": metrics,
        "walk_forward_folds": fold_metrics,
        "n_bars": len(df),
    }
    with open(RESULTS_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
