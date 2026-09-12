# Quant Trading System: Architecture & Backend Learning Guide

> **Target Audience:** Developers with frontend or full-stack experience who are learning quantitative trading systems and algorithmic backend architecture for the first time.  
> **PDF Version Available:** [`report/Quant_Developer_Architecture_and_Learning_Guide.pdf`](Quant_Developer_Architecture_and_Learning_Guide.pdf)

---

## 1. Executive Overview & The Quant Backend Mindset

In traditional web development, a 10ms network delay or reading state slightly early is harmless. In quantitative execution:
- **Looking 1 bar ahead** ("lookahead bias") creates phantom profits in backtests that crash and burn in live markets.
- **Counting pending orders as inventory** inflates risk limits and causes catastrophic double-executions.
- **Ignoring transaction taxes and slippage** turns a theoretical winning algorithm into a real-world loss.

### How Data Flows (Assembly Line):
```
Market Bar (OHLCV) 
    ↳ Causal Indicators (EMA, RSI, ATR, OBV) [src/indicators.py]
        ↳ Execution Engine (Grid + SAR Strategy) [src/engine.py]
            ↳ Order Manager (Deterministic SHA-1 Idempotency) [src/orders.py]
                ↳ Cost & Slippage Engine (Indian Taxes to the Paisa) [src/costs.py]
                    ↳ Backtest Fill at Bar (i+1) Open [src/backtest.py]
                        ↳ Institutional UI Dashboard [frontend/]
```

---

## 2. Core Execution Engine Concepts (`src/engine.py`)

### A. Trend Filter (Fast EMA vs Slow EMA)
- The engine computes an **EMA(12)** and an **EMA(26)**.
- If `EMA(12) > EMA(26)`, the regime is **BULLISH**; if `EMA(12) < EMA(26)`, the regime is **BEARISH**.
- When flat (0 units), initial entry follows this direction.

### B. ATR Grid Spacing & Pyramiding
- **Pyramiding** means scaling into an already winning trade as momentum continues.
- Rather than adding units at fixed rupee intervals (e.g. every ₹10), spacing is dynamic:  
  $$\text{Grid Spacing} = \text{atr\_multiplier} \times \text{ATR}$$
- In volatile markets, the grid widens automatically to prevent premature entries; in calm markets, it tightens.

### C. Position Hard Cap
- If the market continues in our favor, pyramiding adds units up to `max_pyramids` (e.g. 4 additional units).
- However, total exposure cannot exceed `position_cap` (e.g. 5 units maximum). Any extra signals are rejected to prevent over-leverage.

### D. Stop-and-Reverse (SAR)
- If the market reverses against our entry reference price by:  
  $$\text{Stop Distance} = \text{stop\_multiplier} \times \text{ATR}$$
- The engine recognizes that the original trend has broken and a strong counter-trend has emerged.
- It flattens all existing units and immediately opens a position in the opposite direction.

### E. Portfolio Kill Switch (Circuit Breaker)
- The engine marks portfolio equity to market every bar and tracks `equity_peak`.
- If drawdown from peak exceeds 15% (`kill_switch_dd_pct = 0.15`), the Kill Switch fires:
  - Immediately flattens all open inventory to cash.
  - Locks out the engine from opening any new positions.

---

## 3. Causal Technical Indicators (`src/indicators.py`)

### The Golden Rule: No Lookahead Bias
An indicator value at bar index $i$ must use data **strictly from bars $\le i$**.

| Family | Indicator | Formula & Logic | Quant Purpose |
|---|---|---|---|
| **Trend** | **EMA** | $val_i = \alpha \cdot Close_i + (1-\alpha) \cdot val_{i-1}$, $\alpha = \frac{2}{N+1}$ | Lag-reduced moving average to identify directional regime |
| **Momentum** | **RSI** | Wilder's smoothing ($\alpha = \frac{1}{N}$), $RSI = 100 - \frac{100}{1 + RS}$ | Velocity of price change; 70 overbought / 30 oversold |
| **Volatility** | **ATR** | Wilder's smoothing of True Range: $\max(H-L, \|H-C_p\|, \|L-C_p\|)$ | Volatility measurement used for grid spacing & stops |
| **Volume** | **OBV** | $OBV_i = OBV_{i-1} + \text{sign}(\Delta Close) \times Vol_i$ | Cumulative volume confirming institutional flow |

---

## 4. Indian Market Plumbing & Statutory Costs (`src/costs.py`)

Every fill incurs real-world friction calculated down to the paisa:
1. **Slippage**: 2.0 basis points (0.02%) adverse price movement (BUY fills higher, SELL fills lower).
2. **Brokerage**: Flat ₹20.00 per executed order (Zerodha Kite Connect model).
3. **STT / CTT**: 1.0 basis point (0.01%) levied **strictly on SELL turnover**.
4. **Exchange Turnover Charges**: 0.35 basis points on turnover (NSE / MCX).
5. **GST**: 18.0% levied strictly on service fees:  
   $$\text{GST} = (\text{Brokerage} + \text{Exchange Charges}) \times 0.18$$

---

## 5. Order Management, Idempotency & Crash Recovery (`src/orders.py`)

### The Idempotency Key (SHA-1)
To make restarts safe after an ungraceful crash:
$$\text{client\_order\_id} = \text{sha1}(f"\{\text{strategy\_id}\}|\{\text{bar\_index}\}|\{\text{intent}\}")[:16]$$
Replaying the same event stream produces the identical key, making replay a harmless no-op.

### Position Truth from Fills Only
`OrderManager.net_position()` iterates over the book and sums **strictly FILLED orders**. Open intents or rejected orders never inflate inventory.

### Broker Reconciliation Algorithm
When restarting:
1. Adopts any unknown orders from the broker truth snapshot.
2. Resolves status mismatches (e.g. local `PENDING` $\to$ broker `FILLED`).
3. Emits structured audit notes for compliance monitoring.

---

## 6. Backtest Harness & Walk-Forward Validation (`src/backtest.py`)

1. **Bar-Accurate Fills**: Strategy decision on bar $i$ fills at bar $i+1$'s **OPEN** price.
2. **Indicator Warmup**: Early bars produce `NaN` and are ignored until indicators warm up.
3. **Walk-Forward Validation**: 4 non-overlapping chronological test folds with a fresh engine per fold (zero position leakage across boundaries).

---

## 7. Interview Talking Points (Cheat-Sheet)

1. **How do backtest and live numbers reconcile?**
   > "One single decision function with two callers: `GridReverseEngine.on_bar()`. Driven identically by the backtester and a live WebSocket bar-close handler, filling at $i+1$ open with identical cost calculations."
2. **How do you handle crashes?**
   > "Deterministic SHA-1 idempotency keys prevent duplicate orders upon replay, and `OrderManager.reconcile()` adopts broker snapshot truth."
3. **Why ATR spacing?**
   > "Market volatility is non-stationary. Dynamic ATR spacing expands in high-volatility regimes and contracts in consolidation, maintaining risk-reward consistency."

