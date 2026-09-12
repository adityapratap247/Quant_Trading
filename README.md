# Quant Developer Assignment -- Vera Developers

Deployed link: [https://vera-quant-engine.vercel.app](https://vera-quant-engine.vercel.app/)

Scope note: the brief (see `Instructions_Quant_Developer.docx`) covers a full
production trading system -- live execution, broker/data integration, a
macro regime engine, and more. Given the assignment timeline, this
submission implements a representative, fully-tested vertical slice rather
than attempting the entire brief shallowly. See the PDF report
(`report/Quant_Developer_Assignment_Report.pdf`) for the scoping rationale
and what's deliberately deferred.

## What's implemented

| Module | File | Brief item(s) covered |
|---|---|---|
| TA indicators | `src/indicators.py` | Technical analysis module: one tested implementation per indicator family (trend=EMA, momentum=RSI, volatility=ATR, volume=OBV), no duplicated math |
| Execution engine | `src/engine.py` | Live grid + stop-and-reverse execution: ATR-based spacing, pyramiding, position caps, portfolio-level kill switch |
| Order/state management | `src/orders.py` | Idempotent order placement (deterministic client order ids), broker-snapshot reconciliation after a simulated restart |
| Cost model | `src/costs.py` | Slippage + brokerage + STT/CTT + exchange charges + GST, shared by backtest and (eventually) live sizing |
| Backtest harness | `src/backtest.py` | Bar-accurate fills (signal at bar i, fill at bar i+1 open), no-lookahead indicator warmup handling, walk-forward evaluation |
| Synthetic data | `src/data.py` | Stand-in for the Zerodha Kite Connect / tick vendor feed (this sandbox has no network route to a broker or market data API) |
| Tests | `tests/` | 39 tests: unit tests per module + backtest-level regression tests, including a crash/restart reconciliation regression test |

## What's deliberately NOT implemented (see report for reasoning)

- Live Zerodha Kite Connect REST/WebSocket integration (network-isolated
  sandbox; the adapter boundary is designed so it's a drop-in replacement
  for `src/data.py`)
- Macro Regime Engine (macro proxies, regime scoring, parameter overrides)
- MCX/NSE contract master, expiry/rollover handling
- Concurrency (asyncio ingestion loop) -- the engine's `on_bar` interface is
  designed to be called from either a synchronous backtest loop or an async
  live handler without modification, but the async handler itself isn't
  built here

## Running the Project

### 1. Python Engine & Tests
```bash
pip install -r requirements.txt
python -m pytest tests/ -v          # 39 tests passing
python run_backtest.py              # writes results/{summary.json,blotter.csv,equity_curve.png}
```

### 2. Interactive React Frontend Dashboard
```bash
cd frontend
npm install
npm run dev                         # Launches terminal dashboard at http://localhost:3000
```

### 3. Optional FastAPI Backend (Full Stack)
```bash
pip install fastapi uvicorn
python api.py                       # Runs REST API on http://localhost:8000
```

### 4. Deploying for Recruiters (Vercel / Netlify / Cloud)
See **[DEPLOYMENT.md](DEPLOYMENT.md)** for a 2-minute guide to deploying this interactive dashboard to Vercel/Netlify for free so recruiters can directly test and interact with your strategy online.

## Design principles this code follows

1. **One implementation per concept.** ATR is computed once (`indicators.atr`)
   and reused everywhere spacing/stops are needed -- never re-derived.
2. **No lookahead, enforced structurally, not by convention.** Indicators
   are causal by construction; the backtest harness fills a bar-i decision
   at bar i+1's open, never at bar i's own price.
3. **One decision function, two callers.** `GridReverseEngine.on_bar` is
   the single source of strategy logic. The backtest harness drives it in
   a loop; a live handler would drive the same method from a WebSocket
   bar-close event. There is no separate "live version" of the strategy
   to drift out of sync with the backtested one.
4. **Position truth comes from fills, not intentions.** `OrderManager.net_position`
   only counts `FILLED` orders, so a pending/rejected order can never
   silently inflate the position the risk checks see.
5. **Idempotent by construction.** Client order ids are a deterministic
   hash of (strategy, bar, intent), so replaying the same event twice
   (e.g. after a crash) is a no-op, not a duplicate order.
