# Crypto Dual Heatmap (EMA + RSI Multi-Layer)

## Quick Start

```bash
# 1. Install backend dependencies
pip3 install -r backend/requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install

# 3. Build frontend
npm run build

# 4. Run (from project root)
python3 run.py
```

Or install backend manually:
```bash
pip3 install fastapi uvicorn pandas numpy aiohttp websockets google-generativeai
```

Frontend will be served automatically at http://localhost:8000

## Features
- RSI Heatmap multi-timeframe (15m, 1h, 4h, 12h, 1d, 1w)
- Long & Short signals with 5 strength layers
- Real-time data from Binance API
- AI Trading Chatbot (powered by Google Gemini)
- AI Fundamental Analysis - Click any coin to get AI-powered fundamental analysis

## AI Chatbot Setup
1. Click the **"AI Chat"** button (purple) in the header
2. Click **"Configure Gemini API Key"** or the Settings icon
3. Get a free API key at: https://aistudio.google.com/app/apikey
4. Paste your API key and click **Save**
5. Start chatting with AI!

**Note:** Gemini free tier has a limit of 15 requests/minute. If you see a "rate limit" error, wait 1 minute and try again.

## Fundamental Analysis
Click any coin (dot in heatmap or name in table) to view AI-powered fundamental analysis:
- **Intrinsic Value** - Supply model, use case, team/founder
- **Macroeconomic Factors** - Interest rates, regulation, market sentiment
- **Coin-Specific Events** - Token unlocks, ETF approvals, protocol upgrades

Uses Gemini 3 Flash for fast, accurate analysis.

## Tech Stack
- **Backend:** Python, FastAPI, Google Gemini AI
- **Frontend:** React, TypeScript, TailwindCSS, react-markdown (for AI response formatting)
- **Data:** Binance API
- **Markdown Rendering:** react-markdown (safe, XSS-protected)

## Team
Rabih Akbar Nurdin (PM), Yoga Bayu Samudra, Zia Ul Ihsan, Putu Satya Krisnaputra, Sigit Hadi Putranto

## Troubleshooting

### Port 8000 already in use
```bash
lsof -i :8000
kill -9 [PID]
python3 run.py
```

### Backend module not found
```bash
pip3 install -r backend/requirements.txt
```

### Frontend dependencies not installed
```bash
cd frontend
npm install
npm run build
```

### Frontend not loading
Make sure to run `npm run build` in the frontend directory before starting the backend server.

### Fundamental Analysis not working
- Ensure Gemini API key is configured in AI Settings
- Check that you have access to gemini-3-flash-preview model
- Wait 1 minute if you hit rate limit (15 requests/min free tier)
