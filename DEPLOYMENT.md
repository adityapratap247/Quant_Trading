# Deployment Guide: Quant Trading Engine & Dashboard

This repository contains:
1. **The Python Quantitative Engine**: Lookahead-free Grid + SAR execution engine, causal TA indicators, Indian market cost model (STT/CTT, brokerage, GST), idempotent order manager, and walk-forward backtesting harness (`src/`, `tests/`).
2. **The Institutional React Frontend**: Interactive Bloomberg/TradingView-style dark terminal dashboard (`frontend/`) featuring live equity curves, execution overlays, parameter tuning, trade blotter, 4-fold walk-forward matrix, and crash recovery debugger.

---

## Option 1: Deploy to Vercel (Recommended for Recruiters — 2 Minutes, Free)

Deploying the frontend to Vercel provides a public HTTPS link (e.g. `https://your-quant-engine.vercel.app`) that a recruiter or hiring manager can open immediately on desktop or mobile.

### Step-by-Step Instructions:
1. Push this repository to your GitHub account:
   ```bash
   git add .
   git commit -m "Add React quant dashboard and deployment configuration"
   git push origin master
   ```
2. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
3. Click **"Add New"** > **"Project"** and select your repository.
4. In the configuration screen:
   - **Root Directory**: Click "Edit" and choose `frontend`
   - **Framework Preset**: Vite (detected automatically)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Click **"Deploy"**.

> [!NOTE]
> The frontend comes with a built-in TypeScript execution engine matching `src/engine.py` with 100% mathematical parity. When deployed on Vercel, recruiters can dynamically adjust parameters (ATR multipliers, stop levels, Indian taxes), run simulations, test the crash-recovery reconciler, and export blotters without requiring a running Python server!

---

## Option 2: Deploy to Netlify (Free Static Hosting)

1. Go to [netlify.com](https://netlify.com) and click **"Add new site"** > **"Import an existing project"**.
2. Connect your GitHub repository.
3. Set the build settings:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
4. Click **"Deploy site"**.

---

## Option 3: Full-Stack Deployment (Render / Railway / Docker)

If you want to host both the Python FastAPI backend and the React frontend on a single live web service:

### Render.com Setup:
1. Create a **New Web Service** on Render connected to this repository.
2. Configure:
   - **Environment**: Python
   - **Build Command**:
     ```bash
     pip install -r requirements.txt fastapi uvicorn && cd frontend && npm install && npm run build && cd ..
     ```
   - **Start Command**:
     ```bash
     python api.py
     ```
3. Render will run `api.py`, which serves both:
   - The REST API at `/api/backtest`, `/api/walk-forward`, `/api/reconcile`
   - The static React dashboard at `/`

---

## Option 4: Run Locally

### Running the React Frontend (Development Mode):
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Running with the Optional Python FastAPI Backend:
In terminal 1 (Python API):
```bash
pip install fastapi uvicorn
python api.py
```
In terminal 2 (React Frontend):
```bash
cd frontend
npm run dev
```
The React frontend will automatically detect the running Python backend and show **"Engine: Python API (Connected)"** in the top header.

