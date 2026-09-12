"""
Generates a comprehensive, pedagogical Quant Trading System Architecture & Learning Guide PDF.
Designed specifically for developers transitioning from frontend to quant backend development.
"""
from __future__ import annotations

import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

REPORT_DIR = Path(__file__).parent / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
PDF_OUTPUT = REPORT_DIR / "Quant_Developer_Architecture_and_Learning_Guide.pdf"


class NumberedCanvas(canvas.Canvas):
    """Canvas for adding page numbers and running header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Skip cover page
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header
        self.drawString(2 * cm, 28.5 * cm, "Quant Developer Assignment — Architecture & Backend Learning Guide")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(2 * cm, 28.3 * cm, 19 * cm, 28.3 * cm)

        # Running footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(19 * cm, 1.2 * cm, page_str)
        self.drawString(2 * cm, 1.2 * cm, "Vera Developers Placement Submission — Confidential")
        self.line(2 * cm, 1.4 * cm, 19 * cm, 1.4 * cm)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_OUTPUT),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")    # Deep Navy Slate
    accent_color = colors.HexColor("#0284c7")     # Sky Blue
    accent_dark = colors.HexColor("#0369a1")
    text_dark = colors.HexColor("#1e293b")
    text_muted = colors.HexColor("#475569")
    box_bg = colors.HexColor("#f8fafc")
    box_border = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        name="DocSubtitle",
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=accent_dark,
        spaceAfter=20,
    )
    h1_style = ParagraphStyle(
        name="H1_Custom",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        name="H2_Custom",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=accent_dark,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        name="Body_Custom",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6,
    )
    code_style = ParagraphStyle(
        name="Code_Custom",
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    callout_style = ParagraphStyle(
        name="Callout_Text",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0c4a6e"),
    )
    table_cell = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=text_dark,
    )
    table_cell_bold = ParagraphStyle(
        name="TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=text_dark,
    )
    table_header = ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph("QUANT TRADING SYSTEM", title_style))
    story.append(Paragraph("Architecture, Quantitative Finance & Backend Engineering Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=3, color=accent_color, spaceAfter=20))

    story.append(Paragraph(
        "<b>Role:</b> Quantitative Developer (Execution Engine & Backtesting)<br/>"
        "<b>Target Firm:</b> Vera Developers Placement Process<br/>"
        "<b>Focus:</b> Clear, from-the-ground-up explanation of algorithmic execution, "
        "causal technical indicators, Indian market microstructure, deterministic order idempotency, "
        "and lookahead-free backtesting.",
        body_style
    ))
    story.append(Spacer(1, 1.5 * cm))

    # Box for Learner's Perspective
    learner_box = [
        [Paragraph("<b>Note for Full-Stack & Frontend Developers Learning Quant Backend:</b>", table_cell_bold)],
        [Paragraph(
            "If you come from a frontend or traditional full-stack background, quant trading backends differ "
            "in one crucial way: <i>mathematical determinism and zero tolerance for temporal leakage</i>. "
            "In web apps, a 10ms network delay or reading from state slightly early is harmless. In quantitative "
            "execution, looking 1 bar into the future ('lookahead bias') or counting pending orders as inventory creates "
            "phantom profits on paper that blow up with real capital. This guide explains every concept simply, "
            "logically, and with real-world analogies.",
            table_cell
        )]
    ]
    t_learner = Table(learner_box, colWidths=[17 * cm])
    t_learner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bae6fd")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_learner)

    story.append(Spacer(1, 2 * cm))

    # Document Index Summary Table
    toc_data = [
        [Paragraph("<b>Chapter</b>", table_header), Paragraph("<b>Topic Covered</b>", table_header), Paragraph("<b>Core Takeaway</b>", table_header)],
        [Paragraph("1. Executive Overview", table_cell_bold), Paragraph("System Architecture & Data Flow", table_cell), Paragraph("How frontend & backend connect without drift", table_cell)],
        [Paragraph("2. Execution Engine", table_cell_bold), Paragraph("Grid, Pyramiding, Stops, Kill Switch", table_cell), Paragraph("Dynamic ATR spacing and risk capping", table_cell)],
        [Paragraph("3. Causal Indicators", table_cell_bold), Paragraph("EMA, RSI, ATR, and OBV", table_cell), Paragraph("Why causal math prevents lookahead bias", table_cell)],
        [Paragraph("4. Indian Market Plumbing", table_cell_bold), Paragraph("Slippage, STT/CTT, Brokerage, GST", table_cell), Paragraph("Matching returns down to the paisa", table_cell)],
        [Paragraph("5. Order Management", table_cell_bold), Paragraph("Idempotency, SHA-1, Crash Reconciliation", table_cell), Paragraph("Restart-safe state machine & position truth", table_cell)],
        [Paragraph("6. Backtest Harness", table_cell_bold), Paragraph("Bar-Accurate Fills & Walk-Forward", table_cell), Paragraph("Signal at bar i -> Fill at bar i+1 open", table_cell)],
        [Paragraph("7. Interview Prep", table_cell_bold), Paragraph("Talking Points for the Technical Round", table_cell), Paragraph("How to explain your design decisions cleanly", table_cell)],
    ]
    t_toc = Table(toc_data, colWidths=[3.8 * cm, 6.2 * cm, 7.0 * cm])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, box_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, box_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_toc)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 1: EXECUTIVE OVERVIEW & SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("1. Executive Overview & System Architecture", h1_style))
    story.append(Paragraph(
        "At its core, this project implements a <b>systematic, algorithmic quantitative trading system</b>. "
        "A quantitative trading system doesn't rely on human gut feeling; it takes historical or live price "
        "bars (Open, High, Low, Close, Volume), calculates mathematical indicators, makes automated buy/sell decisions, "
        "manages open risk, and accounts for real-world exchange costs down to the paisa.",
        body_style
    ))

    story.append(Paragraph("The Big Picture: How Data Flows Through the System", h2_style))
    story.append(Paragraph(
        "Imagine an assembly line. Every time a new 5-minute candle closes in the market, the following 6-step sequence occurs:",
        body_style
    ))

    flow_data = [
        [Paragraph("<b>Step</b>", table_header), Paragraph("<b>Component</b>", table_header), Paragraph("<b>What Happens in Plain English</b>", table_header)],
        [Paragraph("1. Ingestion", table_cell_bold), Paragraph("src/data.py", table_cell), Paragraph("Receives market OHLCV bars (either synthetic generator or Zerodha Kite Connect feed).", table_cell)],
        [Paragraph("2. Indicators", table_cell_bold), Paragraph("src/indicators.py", table_cell), Paragraph("Computes Trend (EMA), Momentum (RSI), Volatility (ATR), and Volume (OBV) strictly using past data.", table_cell)],
        [Paragraph("3. Strategy", table_cell_bold), Paragraph("src/engine.py", table_cell), Paragraph("GridReverseEngine.on_bar() evaluates whether to enter, add a pyramid unit, or stop-and-reverse.", table_cell)],
        [Paragraph("4. Order Mgmt", table_cell_bold), Paragraph("src/orders.py", table_cell), Paragraph("Emits orders with deterministic SHA-1 IDs to ensure duplicate submissions are impossible.", table_cell)],
        [Paragraph("5. Fills & Costs", table_cell_bold), Paragraph("src/costs.py + backtest.py", table_cell), Paragraph("Fills the order at the NEXT bar's OPEN, subtracting slippage, flat ₹20 brokerage, STT, and GST.", table_cell)],
        [Paragraph("6. Presentation", table_cell_bold), Paragraph("frontend/ (React)", table_cell), Paragraph("Visualizes equity curves, trade blotters, and indicators on an institutional Bloomberg-style UI.", table_cell)],
    ]
    t_flow = Table(flow_data, colWidths=[2.2 * cm, 3.8 * cm, 11.0 * cm])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, box_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, box_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Why We Built Both Python Backend & React Frontend", h2_style))
    story.append(Paragraph(
        "In algorithmic trading desks, research is done in Python (pandas, numpy, vectorbt), but portfolio managers "
        "and risk officers monitor performance through high-density graphical dashboards. By implementing both a "
        "robust Python core and a standalone React dashboard, the project achieves two critical goals:<br/>"
        "1. <b>Recruiter Convenience:</b> A recruiter can open a Vercel link and interact with the strategy in 5 seconds.<br/>"
        "2. <b>Architecture Rigor:</b> The React frontend mirrors the Python logic byte-for-byte, verifying that the "
        "engineering principles hold true across language boundaries.",
        body_style
    ))

    story.append(Spacer(1, 0.5 * cm))

    # =========================================================================
    # CHAPTER 2: THE EXECUTION ENGINE (GRID, PYRAMIDING, SAR, KILL SWITCH)
    # =========================================================================
    story.append(Paragraph("2. The Execution Engine (src/engine.py)", h1_style))
    story.append(Paragraph(
        "The execution engine is the 'brain' of the strategy. It answers one question: <i>Given the current price and market volatility, what action should we take right now?</i>",
        body_style
    ))

    story.append(Paragraph("Concept 1: Trend Filter (Fast EMA vs Slow EMA)", h2_style))
    story.append(Paragraph(
        "Before making any trade, the engine checks market direction. It compares a fast 12-period Exponential Moving "
        "Average against a slow 26-period Exponential Moving Average. If <b>EMA(12) > EMA(26)</b>, the regime is BULLISH; "
        "if <b>EMA(12) < EMA(26)</b>, the regime is BEARISH. When flat (no open position), the engine initiates a trade "
        "matching this trend direction.",
        body_style
    ))

    story.append(Paragraph("Concept 2: ATR-Based Grid Spacing & Pyramiding", h2_style))
    story.append(Paragraph(
        "<b>What is Pyramiding?</b> Pyramiding means adding more units to an already profitable trade. "
        "Rather than betting everything at once, we scale into a winning position as the market moves in our favor.<br/>"
        "<b>Why use ATR (Average True Range) spacing instead of fixed points?</b> If you set a fixed spacing rule of ₹10, "
        "it might work when the stock moves ₹15 a day, but fail completely when volatility expands and it moves ₹100 a day. "
        "By setting <code>grid_spacing = atr_multiplier * ATR</code>, the grid automatically expands during high volatility "
        "and tightens during quiet consolidation.",
        body_style
    ))

    story.append(Paragraph("Concept 3: Position Hard Cap", h2_style))
    story.append(Paragraph(
        "Uncontrolled pyramiding can cause catastrophic losses if a trend suddenly reverses when you hold a huge position. "
        "The engine enforces a strict <b>Position Cap</b> (e.g. maximum 5 units). Once the cap is reached, further pyramid "
        "signals are silently rejected by risk control.",
        body_style
    ))

    story.append(Paragraph("Concept 4: Stop-and-Reverse (SAR)", h2_style))
    story.append(Paragraph(
        "A regular stop-loss flattens your position to cash. A <b>Stop-and-Reverse</b> does something smarter: "
        "it recognizes that if the market moves against you by a large distance (<code>stop_multiplier * ATR</code>), "
        "your original directional thesis was completely wrong and a strong counter-trend has likely begun. "
        "The engine issues two orders at once: first, it sells all existing long units to flatten, and immediately opens "
        "a new short unit to ride the new trend downwards.",
        body_style
    ))

    story.append(Paragraph("Concept 5: Portfolio Kill Switch", h2_style))
    story.append(Paragraph(
        "Algorithmic trading desks mandate an automated circuit breaker. The engine continuously tracks "
        "<b>High-Water Mark Equity</b> (the highest peak portfolio value ever reached). If mark-to-market drawdown "
        "from that peak exceeds 15% (<code>kill_switch_dd_pct = 0.15</code>), the Kill Switch fires: it immediately "
        "cancels all pending orders, flattens all open inventory to cash, and locks out the engine from opening any new positions.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 3: CAUSAL TECHNICAL INDICATORS (NO LOOKAHEAD)
    # =========================================================================
    story.append(Paragraph("3. Technical Analysis Indicators (src/indicators.py)", h1_style))
    story.append(Paragraph(
        "The brief mandated: <i>'one tested implementation per indicator family, no duplicated math.'</i> "
        "Furthermore, every indicator must be strictly <b>causal</b>.",
        body_style
    ))

    story.append(Paragraph("What Does 'Causal' & 'No Lookahead' Mean?", h2_style))
    story.append(Paragraph(
        "In traditional programming, functions can inspect any element in an array. But in time-series finance, "
        "bar <code>i</code> represents the market at 10:00 AM, and bar <code>i+1</code> is 10:05 AM. "
        "If the indicator at 10:00 AM uses data from 10:05 AM, it is guilty of <b>Lookahead Bias</b>. "
        "A backtest with lookahead bias will show unbelievable 1,000% returns because it effectively knows the future, "
        "but will immediately lose all capital in live trading. In our codebase, every indicator value at index <code>i</code> "
        "is computed strictly from data where <code>index &le; i</code>.",
        body_style
    ))

    # Indicator Summary Table
    ind_table_data = [
        [Paragraph("<b>Family</b>", table_header), Paragraph("<b>Indicator & Formula</b>", table_header), Paragraph("<b>Role in Execution Engine</b>", table_header)],
        [
            Paragraph("Trend", table_cell_bold),
            Paragraph("<b>EMA (Exponential Moving Average)</b><br/><code>val[i] = &alpha; * price[i] + (1-&alpha;) * val[i-1]</code><br/>where <code>&alpha; = 2 / (period + 1)</code>", table_cell),
            Paragraph("Fast EMA(12) vs Slow EMA(26) cross determines initial entry direction (Long vs Short).", table_cell)
        ],
        [
            Paragraph("Momentum", table_cell_bold),
            Paragraph("<b>RSI (Relative Strength Index)</b><br/>Wilder's Smoothing: <code>&alpha; = 1 / period</code><br/><code>RS = avg_gain / avg_loss</code><br/><code>RSI = 100 - (100 / (1 + RS))</code>", table_cell),
            Paragraph("Measures velocity of directional price movement. Bounded between 0 and 100.", table_cell)
        ],
        [
            Paragraph("Volatility", table_cell_bold),
            Paragraph("<b>ATR (Average True Range)</b><br/><code>TR = max(H-L, |H-Cp|, |L-Cp|)</code><br/>Wilder's smoothing of True Range over 14 bars.", table_cell),
            Paragraph("The single source of truth for volatility. Sets dynamic grid add spacing and stop-loss distance.", table_cell)
        ],
        [
            Paragraph("Volume", table_cell_bold),
            Paragraph("<b>OBV (On-Balance Volume)</b><br/><code>OBV[i] = OBV[i-1] + sign(&Delta;Close) * Vol[i]</code>", table_cell),
            Paragraph("Tracks institutional accumulation and distribution by adding volume on up-bars and subtracting on down-bars.", table_cell)
        ],
    ]
    t_ind = Table(ind_table_data, colWidths=[2.2 * cm, 7.8 * cm, 7.0 * cm])
    t_ind.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, box_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, box_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_ind)
    story.append(Spacer(1, 0.4 * cm))

    # =========================================================================
    # CHAPTER 4: INDIAN MARKET PLUMBING & STATUTORY COST MECHANICS
    # =========================================================================
    story.append(Paragraph("4. Indian Market Plumbing & Statutory Costs (src/costs.py)", h1_style))
    story.append(Paragraph(
        "A hallmark of an amateur trading system is ignoring transaction costs. On paper, high-frequency "
        "grid additions look profitable, but in the real world, exchange fees, taxes, and slippage will bleed "
        "the account dry. Our cost engine models Indian financial plumbing down to the paisa.",
        body_style
    ))

    cost_rows = [
        [Paragraph("<b>Charge Component</b>", table_header), Paragraph("<b>Standard Rate in India</b>", table_header), Paragraph("<b>How It Is Computed in src/costs.py</b>", table_header)],
        [
            Paragraph("Slippage", table_cell_bold),
            Paragraph("2.0 bps (0.02%)", table_cell),
            Paragraph("Market impact: BUY fills higher than quoted price; SELL fills lower. <code>adj = price * (2 / 10,000)</code>.", table_cell)
        ],
        [
            Paragraph("Flat Brokerage", table_cell_bold),
            Paragraph("₹20.00 per executed order", table_cell),
            Paragraph("Zerodha Kite Connect discount-broker model: fixed flat fee per trade execution.", table_cell)
        ],
        [
            Paragraph("STT / CTT", table_cell_bold),
            Paragraph("1.0 bps (Sell side only)", table_cell),
            Paragraph("Securities/Commodities Transaction Tax: Statutory tax levied <b>strictly on SELL turnover</b> in derivatives.", table_cell)
        ],
        [
            Paragraph("Exchange Charges", table_cell_bold),
            Paragraph("0.35 bps (Turnover)", table_cell),
            Paragraph("NSE / MCX exchange infrastructure turnover charges applied on both BUY and SELL sides.", table_cell)
        ],
        [
            Paragraph("GST (Govt Tax)", table_cell_bold),
            Paragraph("18.0% on Service Fees", table_cell),
            Paragraph("<code>GST = (Brokerage + Exchange Charges) * 0.18</code>. Note: GST applies to service fees, NOT turnover.", table_cell)
        ],
    ]
    t_cost = Table(cost_rows, colWidths=[3.2 * cm, 4.0 * cm, 9.8 * cm])
    t_cost.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, box_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, box_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_cost)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: ORDER & STATE MANAGEMENT (IDEMPOTENCY & CRASH RECONCILIATION)
    # =========================================================================
    story.append(Paragraph("5. Order & State Management (src/orders.py)", h1_style))
    story.append(Paragraph(
        "In production trading, software crashes, network sockets drop, and servers reboot. "
        "What happens if your trading engine places a BUY order, and the server loses power 1 millisecond later? "
        "When the server boots back up, will it submit that order a second time and buy twice as much? "
        "In <code>src/orders.py</code>, we solve this with <b>Deterministic Idempotency</b> and <b>Broker Reconciliation</b>.",
        body_style
    ))

    story.append(Paragraph("Concept 1: Deterministic Client Order IDs (SHA-1)", h2_style))
    story.append(Paragraph(
        "Instead of using random UUIDs (e.g. <code>uuid4()</code>), every order generated by the engine has its "
        "<code>client_order_id</code> computed as a deterministic cryptographic hash:<br/>"
        "<code>client_order_id = sha1(f'{strategy_id}|{bar_index}|{intent}')[:16]</code><br/>"
        "<b>Why is this revolutionary?</b> If bar 46 emits a stop-and-reverse order, its ID will always be "
        "<code>3a98e1f04bc8d821</code>. If the engine crashes, reboots, and replays bar 46, it sees that "
        "<code>3a98e1f04bc8d821</code> already exists in the book! It simply returns the existing order instead "
        "of double-submitting. Replay is mathematically idempotent.",
        body_style
    ))

    story.append(Paragraph("Concept 2: Position Truth from Fills Only", h2_style))
    story.append(Paragraph(
        "A common amateur bug is updating position inventory when an order is <i>placed</i> (intent). "
        "If that order is rejected or cancelled by the broker, the system's internal position drifts from reality. "
        "In our system, <code>OrderManager.net_position()</code> iterates over the order book and sums "
        "<b>strictly orders with status == FILLED</b>. Intentions never inflate risk truth.",
        body_style
    ))

    story.append(Paragraph("Concept 3: Broker Reconciliation Algorithm", h2_style))
    story.append(Paragraph(
        "Upon restarting after a crash, the engine calls <code>OrderManager.reconcile(broker_snapshot)</code>:<br/>"
        "1. <b>Adopts Unknown Orders:</b> If an order was filled on the broker side while local disk was crashing, the engine adopts it as truth.<br/>"
        "2. <b>Resolves Status Mismatches:</b> If local state recorded an order as <code>PENDING</code>, but broker snapshot shows <code>FILLED</code>, the local state is updated to <code>FILLED</code> with the true broker execution price.<br/>"
        "3. <b>Generates Audit Notes:</b> Every discrepancy produces a structured log for compliance monitoring.",
        body_style
    ))

    story.append(Spacer(1, 0.4 * cm))

    # =========================================================================
    # CHAPTER 6: BACKTEST HARNESS & STATISTICAL VALIDATION
    # =========================================================================
    story.append(Paragraph("6. Backtest Harness & Walk-Forward Validation (src/backtest.py)", h1_style))
    story.append(Paragraph(
        "A backtest harness is a simulation engine that tests how a strategy would have performed on historical data. "
        "Our backtester enforces three non-negotiable quantitative standards:",
        body_style
    ))

    story.append(Paragraph("Rule 1: Fills at Bar (i+1) Open (Zero Lookahead)", h2_style))
    story.append(Paragraph(
        "If an indicator cross occurs on bar <code>i</code> at 11:30 AM close, you <b>cannot</b> fill at bar <code>i</code>'s close. "
        "In the real world, bar <code>i</code>'s close is only known once the bar has finished! "
        "Therefore, any order triggered at bar <code>i</code> close executes at bar <code>i+1's OPEN</code> (11:30:01 AM). "
        "This 1-bar execution delay reflects physical reality.",
        body_style
    ))

    story.append(Paragraph("Rule 2: Indicator Warmup Discipline", h2_style))
    story.append(Paragraph(
        "A 26-period EMA requires at least 26 bars of data before its mathematical value is valid. "
        "During bars 0 to 25, indicator values are genuine <code>NaN</code>. The engine refuses to trade until all "
        "indicators are fully warmed up, avoiding garbage signals on startup.",
        body_style
    ))

    story.append(Paragraph("Rule 3: Walk-Forward Validation with Hard Fold Isolation", h2_style))
    story.append(Paragraph(
        "In machine learning and quant research, strategies often suffer from 'overfitting' (memorizing past noise). "
        "We divide our 600 bars into <b>4 chronological, non-overlapping test folds</b>. For each fold, we instantiate a "
        "brand new engine and order manager from scratch. No position inventory or indicator state is allowed to leak "
        "across fold boundaries.",
        body_style
    ))

    # Key Performance Formulas Table
    metric_data = [
        [Paragraph("<b>Metric</b>", table_header), Paragraph("<b>Formula</b>", table_header), Paragraph("<b>Financial Meaning</b>", table_header)],
        [
            Paragraph("Total Return %", table_cell_bold),
            Paragraph("<code>((Final_Equity / Initial_Cash) - 1) * 100</code>", table_cell),
            Paragraph("Net percentage gain or loss after all trading fees and slippage.", table_cell)
        ],
        [
            Paragraph("Max Drawdown %", table_cell_bold),
            Paragraph("<code>min((Equity[i] - Peak_Equity[i]) / Peak_Equity[i]) * 100</code>", table_cell),
            Paragraph("The worst peak-to-trough drop in account value. Measures downside pain and risk of ruin.", table_cell)
        ],
        [
            Paragraph("Sharpe Ratio", table_cell_bold),
            Paragraph("<code>(Mean(Returns) / Std(Returns)) * sqrt(252 * 75)</code>", table_cell),
            Paragraph("Risk-adjusted return. Compares excess return to volatility. Annualized for 5-min bars (252 days &times; 75 bars/day).", table_cell)
        ],
    ]
    t_metrics = Table(metric_data, colWidths=[3.2 * cm, 6.8 * cm, 7.0 * cm])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, box_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, box_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_metrics)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 7: HOW TO EXPLAIN THIS TO A RECRUITER (INTERVIEW CHEAT-SHEET)
    # =========================================================================
    story.append(Paragraph("7. Interview Prep: What to Tell the Recruiter", h1_style))
    story.append(Paragraph(
        "When interviewing for a Quant Developer role, interviewers care about your <b>engineering judgment</b>, "
        "not just syntax. Here are the 5 questions they will ask and how this project demonstrates mastery:",
        body_style
    ))

    qa_list = [
        (
            "Q1: 'How do you ensure backtest numbers reconcile to live trading numbers?'",
            "<b>Answer:</b> 'By having one single decision function with two callers. In my implementation, "
            "GridReverseEngine.on_bar() is the single source of truth for strategy logic. The backtester drives it "
            "in a loop; a live WebSocket bar-close handler drives the exact same method. Fills in the backtester are "
            "strictly deferred to bar i+1 open with identical CostModel slippage, flat ₹20 brokerage, STT, and GST, "
            "preventing any backtest-to-live drift.'"
        ),
        (
            "Q2: 'How does your engine handle unexpected process crashes or restarts?'",
            "<b>Answer:</b> 'Orders use deterministic idempotency keys: client_order_id = sha1(f\"{strategy}|{bar}|{intent}\"). "
            "If the engine crashes and restarts, re-submitting the same decision produces the exact same hash, which is a "
            "safe no-op in OrderManager. Furthermore, OrderManager.reconcile() takes a broker snapshot, adopts any orders filled "
            "during the crash window, corrects status mismatches, and calculates net position truth strictly from FILLED orders.'"
        ),
        (
            "Q3: 'Why did you use ATR for grid spacing and stops instead of fixed rupee targets?'",
            "<b>Answer:</b> 'Market volatility is non-stationary. A fixed ₹10 grid might trade well in low-volatility consolidation "
            "but get chopped up when volatility expands to ₹50. Dynamic ATR spacing expands grid distance and stops during high "
            "volatility regimes and tightens during quiet regimes, preserving risk-reward consistency across time.'"
        ),
        (
            "Q4: 'Why is there both a Python engine and a React frontend?'",
            "<b>Answer:</b> 'Algorithmic development happens in Python for numerical discipline and pytest coverage, but visual "
            "monitoring is critical for risk management. I built an institutional React dashboard with an embedded client-side "
            "simulation engine so the recruiter can test parameters, walk-forward folds, and crash recovery live in their browser "
            "without needing cloud compute.'"
        ),
        (
            "Q5: 'What testing discipline did you apply?'",
            "<b>Answer:</b> '39 automated tests in pytest with zero external mock leaks. Tests cover indicator hand-calculations, "
            "one-sided STT tax rules, position cap enforcement, kill switch firing on extreme drawdown, and a full simulated crash "
            "reconciliation regression test asserting net position parity after restart.'"
        ),
    ]

    for q, a in qa_list:
        story.append(Paragraph(f"<b>{q}</b>", h2_style))
        story.append(Paragraph(a, body_style))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.5 * cm))

    # Concluding Box
    conclude_box = [
        [Paragraph("<b>Summary Checklist for Your Submission:</b>", table_cell_bold)],
        [Paragraph(
            "&bull; <b>39 Pytest tests pass:</b> Run <code>python -m pytest tests/ -v</code><br/>"
            "&bull; <b>Frontend is live:</b> Open <code>http://localhost:3001</code> to view and demo the dashboard<br/>"
            "&bull; <b>Deployable to Vercel:</b> Follow instructions in <code>DEPLOYMENT.md</code> for a public recruiter link<br/>"
            "&bull; <b>PDF Reports ready:</b> Both the Technical Submission Report and this Learning Guide are in <code>report/</code>.",
            table_cell
        )]
    ]
    t_conclude = Table(conclude_box, colWidths=[17 * cm])
    t_conclude.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_conclude)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Learning Guide PDF successfully generated at: {PDF_OUTPUT}")


if __name__ == "__main__":
    build_pdf()

