import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPORT_DIR = Path(__file__).parent
ROOT = REPORT_DIR.parent
RESULTS = ROOT / "results"
OUT = REPORT_DIR / "Quant_Developer_Assignment_Report.pdf"

summary = json.loads((RESULTS / "summary.json").read_text())
fm = summary["full_sample_metrics"]
folds = summary["walk_forward_folds"]
ecfg = summary["engine_config"]
ccfg = summary["cost_model"]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="H1c", parent=styles["Heading1"], spaceAfter=10, textColor=colors.HexColor("#1a2b40")))
styles.add(ParagraphStyle(name="H2c", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1a2b40")))
styles.add(ParagraphStyle(name="Bodyc", parent=styles["BodyText"], leading=14, spaceAfter=6))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11, textColor=colors.HexColor("#444444")))
styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontSize=22, spaceAfter=6))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=12, textColor=colors.HexColor("#555555"), spaceAfter=4))

story = []

# ---------------------------------------------------------------- cover
story.append(Spacer(1, 4 * cm))
story.append(Paragraph("Quant Developer -- Assignment Submission", styles["Cover"]))
story.append(Paragraph("Vera Developers -- Placement Process", styles["CoverSub"]))
story.append(Spacer(1, 0.6 * cm))
story.append(Paragraph("Grid + Stop-and-Reverse Execution Engine with Bar-Accurate Backtest Harness", styles["CoverSub"]))
story.append(Spacer(1, 2 * cm))
story.append(Paragraph("Submitted by: Aditya", styles["Bodyc"]))
story.append(Paragraph("Chitkara University -- Career Advancement Services referral", styles["Bodyc"]))
story.append(Paragraph("Developed with Claude Code, per assignment instructions", styles["Bodyc"]))
story.append(PageBreak())

# ---------------------------------------------------------------- scope
story.append(Paragraph("1. Scope and Approach", styles["H1c"]))
story.append(Paragraph(
    "The assignment brief describes a full production trading system: a live grid and "
    "stop-and-reverse execution engine, a technical analysis module, a Macro Regime Engine, "
    "Zerodha Kite Connect broker/data integration, a backtest harness, order/state management, "
    "observability, and automated SDLC agents. Building all of this to production quality is "
    "several months of work; within the assignment's timeline the goal was to build a smaller "
    "set of pieces to real engineering depth rather than a larger set shallowly.",
    styles["Bodyc"],
))
story.append(Paragraph("What was built, fully working and tested:", styles["Bodyc"]))
story.append(ListFlowable([
    ListItem(Paragraph("Technical analysis module -- one tested implementation per indicator family "
                        "(trend, momentum, volatility, volume), no duplicated math", styles["Bodyc"])),
    ListItem(Paragraph("Live grid + stop-and-reverse execution engine -- ATR-based spacing, pyramiding, "
                        "position caps, portfolio-level kill switch", styles["Bodyc"])),
    ListItem(Paragraph("Order/state management -- idempotent order placement (deterministic client order "
                        "ids) and broker-snapshot reconciliation after a simulated crash/restart", styles["Bodyc"])),
    ListItem(Paragraph("Cost model -- slippage, brokerage, STT/CTT, exchange charges, GST", styles["Bodyc"])),
    ListItem(Paragraph("Backtest harness -- bar-accurate fills (decision at bar i, fill at bar i+1's open), "
                        "walk-forward evaluation with per-fold engine state reset", styles["Bodyc"])),
    ListItem(Paragraph("39 automated tests, including a crash/restart order-reconciliation regression test", styles["Bodyc"])),
], bulletType="bullet"))

story.append(Paragraph("Deliberately deferred, and why:", styles["Bodyc"]))
story.append(ListFlowable([
    ListItem(Paragraph("Live Zerodha Kite Connect REST/WebSocket integration -- this sandbox has no network "
                        "route to a broker or market-data API. The data-source module (src/data.py) is "
                        "isolated behind a plain OHLCV DataFrame interface specifically so it is a drop-in "
                        "replacement point for a Kite Connect adapter, without touching indicators, engine, "
                        "orders, or the backtester.", styles["Bodyc"])),
    ListItem(Paragraph("Macro Regime Engine -- scoring macro proxies into regime states and applying "
                        "parameter overrides is a substantial, largely independent subsystem; given the "
                        "timeline it was better to leave it out cleanly than implement it as a stub that "
                        "doesn't actually score anything.", styles["Bodyc"])),
    ListItem(Paragraph("MCX/NSE contract master and expiry/rollover handling -- requires real instrument "
                        "data this sandbox cannot fetch.", styles["Bodyc"])),
    ListItem(Paragraph("An asyncio-based live ingestion loop -- the engine's on_bar() call is written so "
                        "either a synchronous backtest loop or an async live handler can drive it unchanged; "
                        "only the synchronous (backtest) caller is implemented here.", styles["Bodyc"])),
], bulletType="bullet"))

# ---------------------------------------------------------------- architecture
story.append(Paragraph("2. Architecture", styles["H1c"]))
story.append(Paragraph(
    "The system is deliberately layered so that each concern has exactly one implementation, "
    "reused everywhere it's needed:",
    styles["Bodyc"],
))
story.append(Image(str(REPORT_DIR / "architecture_diagram.png"), width=16 * cm, height=9.14 * cm))
story.append(Paragraph(
    "The same GridReverseEngine.on_bar() call is what both the backtester and a live handler would "
    "drive -- there is only one implementation of the strategy decision logic, which is the "
    "mechanism by which backtest numbers are designed to reconcile to live numbers: there is no "
    "separate vectorized-backtest version of the strategy that could silently diverge from the "
    "live version.",
    styles["Bodyc"],
))

# ---------------------------------------------------------------- design choices
story.append(Paragraph("3. Key Design Choices", styles["H1c"]))
design_points = [
    ("No lookahead, enforced structurally", "Indicators are causal by construction (value at bar i uses "
     "only data through bar i). The backtest harness fills a decision made at bar i using bar i+1's open "
     "price, never bar i's own close/high/low -- so a signal can never trade at a price that was only "
     "knowable at the same instant the signal fired."),
    ("Idempotent orders", "Every order's client_order_id is a deterministic hash of (strategy id, bar "
     "index, intent). Replaying the same decision twice -- e.g. after a crash and restart -- is a no-op "
     "rather than a duplicate order."),
    ("Position truth from fills only", "OrderManager.net_position() sums only FILLED orders. A pending or "
     "rejected order can never inflate the position that risk checks (position cap, kill switch) observe."),
    ("Reconciliation as a first-class operation", "OrderManager.reconcile() takes an external broker "
     "snapshot and adopts it as truth for any status mismatch or any order the local process didn't "
     "know about -- the same shape a real Kite Connect reconciliation pass after a restart would take."),
    ("One cost function everywhere", "Slippage and transaction costs are computed by a single CostModel "
     "used by every fill in the backtester (and would be the same one used to size live orders), so "
     "backtest P&L and a live cost estimate can never silently use different assumptions."),
    ("Walk-forward with hard fold isolation", "Each walk-forward fold gets its own fresh engine and order "
     "manager; no position state or indicator warmup leaks from one fold into the next."),
]
for title, body in design_points:
    story.append(Paragraph(f"<b>{title}.</b> {body}", styles["Bodyc"]))

story.append(PageBreak())

# ---------------------------------------------------------------- tests
story.append(Paragraph("4. Test Coverage", styles["H1c"]))
story.append(Paragraph(
    "39 automated tests (pytest), organized by module. All pass. Coverage focuses on the properties "
    "that actually matter for a trading system, not just line coverage:",
    styles["Bodyc"],
))
cell = styles["Small"]
header_style = ParagraphStyle(name="TblHeader", parent=styles["Small"], textColor=colors.white)
test_table_data = [
    [Paragraph("<b>Module</b>", header_style), Paragraph("<b>Tests</b>", header_style), Paragraph("<b>What's checked</b>", header_style)],
    [Paragraph("indicators.py", cell), Paragraph("10", cell), Paragraph(
        "Hand-checked values, boundary behaviour (RSI 0/100 on monotonic series), "
        "causal length, input validation", cell)],
    [Paragraph("costs.py", cell), Paragraph("5", cell), Paragraph(
        "Slippage direction, one-sided STT, linear scaling with turnover", cell)],
    [Paragraph("orders.py", cell), Paragraph("8", cell), Paragraph(
        "Idempotent client order ids, idempotent placement, fill-only position truth, "
        "reconciliation of both status mismatches and unknown orders", cell)],
    [Paragraph("engine.py", cell), Paragraph("8", cell), Paragraph(
        "Entry direction, pyramiding trigger, position-cap enforcement, stop-and-reverse "
        "trigger and order sequence, kill-switch firing and post-kill halt, idempotent replay", cell)],
    [Paragraph("backtest.py", cell), Paragraph("8", cell), Paragraph(
        "Warmup rows produce no signal, fills use next-bar open (not current close), "
        "zero-cost fills are exact, position cap holds across a full run, walk-forward windows are "
        "chronological/non-overlapping, a crash/restart reconciliation regression test, kill-switch "
        "wiring inside the full harness", cell)],
]
t = Table(test_table_data, colWidths=[2.6 * cm, 1.4 * cm, 12 * cm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2b40")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.3),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph(
    "The regression test worth highlighting: it runs a full backtest, snapshots the order book "
    "mid-run as \"broker truth,\" then replays the same engine decisions from a completely fresh "
    "OrderManager and reconciles against that snapshot -- asserting the resulting net position "
    "matches the original run exactly. This is the test that would catch a future change silently "
    "breaking crash-safety (e.g. double-submitting orders on restart).",
    styles["Bodyc"],
))

story.append(PageBreak())

# ---------------------------------------------------------------- results
story.append(Paragraph("5. Backtest Results", styles["H1c"]))
story.append(Paragraph(
    "Run on 600 bars (5-minute) of reproducible synthetic OHLCV data with regime-switching "
    "trend/chop legs (see src/data.py -- this sandbox has no network route to real NSE/MCX data, "
    "so results here demonstrate correctness of the mechanics, not claimed alpha). Starting capital "
    "INR 10,00,000, contract multiplier 25.",
    styles["Bodyc"],
))

cfg_table = [
    ["Engine parameter", "Value", "Cost parameter", "Value"],
    ["ATR multiplier (grid spacing)", str(ecfg["atr_multiplier"]), "Slippage (bps)", str(ccfg["slippage_bps"])],
    ["Stop multiplier", str(ecfg["stop_multiplier"]), "Brokerage/order (INR)", str(ccfg["brokerage_per_order"])],
    ["Max pyramids", str(ecfg["max_pyramids"]), "STT/CTT (bps, sell)", str(ccfg["stt_ctt_bps"])],
    ["Position cap (units)", str(ecfg["position_cap"]), "Exchange txn (bps)", str(ccfg["exchange_txn_bps"])],
    ["Kill-switch drawdown", f"{ecfg['kill_switch_dd_pct']*100:.0f}%", "GST", f"{ccfg['gst_rate']*100:.0f}%"],
]
t2 = Table(cfg_table, colWidths=[5.3 * cm, 2.7 * cm, 5.3 * cm, 2.7 * cm])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2b40")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t2)
story.append(Spacer(1, 0.3 * cm))

metrics_table = [
    ["Metric", "Full sample"],
    ["Trades", str(fm["trades"])],
    ["Total return", f"{fm['total_return_pct']}%"],
    ["Max drawdown", f"{fm['max_drawdown_pct']}%"],
    ["Sharpe (annualized, approx.)", str(fm["sharpe_annualized_approx"])],
    ["Final equity (INR)", f"{fm['final_equity']:,}"],
    ["Kill switch fired", str(fm["kill_switch_fired"])],
]
t3 = Table(metrics_table, colWidths=[7 * cm, 5 * cm])
t3.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2b40")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t3)
story.append(Spacer(1, 0.3 * cm))
story.append(Image(str(RESULTS / "equity_curve.png"), width=16 * cm, height=10.67 * cm))

story.append(PageBreak())
story.append(Paragraph("Walk-Forward Evaluation (4 folds)", styles["H2c"]))
story.append(Paragraph(
    "Each fold uses a fresh engine and order manager (no state or indicator warmup carried across "
    "fold boundaries), evaluated in chronological order.",
    styles["Bodyc"],
))
wf_table = [["Fold", "Bars", "Trades", "Return %", "Max DD %", "Sharpe (approx.)"]]
for f in folds:
    wf_table.append([
        str(f["fold"]), str(f["bars"]), str(f["trades"]),
        str(f["total_return_pct"]), str(f["max_drawdown_pct"]), str(f["sharpe_annualized_approx"]),
    ])
t4 = Table(wf_table, colWidths=[1.5 * cm, 2 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm])
t4.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2b40")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t4)
story.append(Spacer(1, 0.3 * cm))
story.append(Paragraph(
    "Read this as a mechanics check, not a claim of edge: on synthetic regime-switching data with a "
    "simple EMA-cross trend filter, results are close to flat after costs in every fold, which is "
    "expected -- the point being demonstrated here is that the harness produces stable, "
    "reconcilable, cost-aware numbers across independent folds, not that this particular trend "
    "filter has alpha on real NSE/MCX data.",
    styles["Bodyc"],
))

# ---------------------------------------------------------------- next steps
story.append(Paragraph("6. What's Next", styles["H1c"]))
story.append(Paragraph(
    "Given more time, the next pieces in priority order would be:",
    styles["Bodyc"],
))
story.append(ListFlowable([
    ListItem(Paragraph("Kite Connect adapter implementing the same OHLCV-DataFrame interface as "
                        "src/data.py, plus a WebSocket bar-close handler calling the same "
                        "GridReverseEngine.on_bar() used here", styles["Bodyc"])),
    ListItem(Paragraph("Macro Regime Engine: ingest macro proxies, score into discrete regime states, "
                        "and apply regime-conditional overrides to atr_multiplier / stop_multiplier / "
                        "position_cap", styles["Bodyc"])),
    ListItem(Paragraph("NSE/MCX contract master with expiry/rollover handling, feeding lot-size-aware "
                        "position sizing", styles["Bodyc"])),
    ListItem(Paragraph("Structured logging and an alerting blotter (kill-switch fires, reconciliation "
                        "mismatches) wired to the observability requirements in the brief", styles["Bodyc"])),
], bulletType="bullet"))

story.append(Paragraph("7. Repository", styles["H1c"]))
story.append(Paragraph(
    "Full source, 39 tests, and commit history (7 commits, staged by module: indicators -> costs -> "
    "orders -> engine -> data -> backtest harness -> run script/README) are included alongside this "
    "report. See README.md for exact run instructions (`pytest tests/ -v`, `python run_backtest.py`).",
    styles["Bodyc"],
))

doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="Quant Developer Assignment Report", author="Aditya",
)
doc.build(story)
print("PDF built:", OUT)
