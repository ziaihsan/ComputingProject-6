# Crypto RSI Heatmap (EMA + RSI Multi-Layer)

Real-time cryptocurrency market analysis with AI-powered insights.

**Live Demo:** https://computingproject-6.onrender.com

## Quick Start (Run Locally)

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
- **Testing:** pytest (backend), Vitest + React Testing Library (frontend)
- **CI/CD:** GitHub Actions

## Testing

Tests run in an isolated environment and do NOT affect the production deployment.

### Backend Tests (pytest)
```bash
cd backend

# Install test dependencies (separate from production)
pip install -r requirements-dev.txt

# Run all tests with coverage
pytest

# Run unit tests only
pytest tests/unit/ -v

# View HTML coverage report
open htmlcov/index.html
```

**Coverage Report Location:** `backend/htmlcov/index.html`

### Frontend Tests (Vitest)
```bash
cd frontend

# Install dependencies
npm install

# Run tests (watch mode)
npm test

# Run tests once (CI mode)
npm run test:run

# Run with coverage report
npm run test:coverage

# Open Vitest UI (browser-based)
npm run test:ui
```

**Coverage Report Location:** `frontend/coverage/index.html`

### Continuous Integration (GitHub Actions)

Tests run automatically on every push to `main`/`develop` and on pull requests.

View test results: Go to **Actions** tab in GitHub repository.

### Understanding Test Results

**Coverage Report** indicates the percentage of code covered by tests:
- `80-100%` = Excellent (green)
- `60-79%` = Good (yellow)
- `<60%` = Needs Improvement (red)

**Test Output:**
- `PASSED` = Test successful ✅
- `FAILED` = Test failed (bug detected) ❌
- `SKIPPED` = Test intentionally skipped

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
