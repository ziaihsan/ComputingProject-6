# Crypto Dual Heatmap (EMA + RSI Multi-Layer)

## Quick Start

```bash
# 1. Install dependencies (once)
pip3 install -r backend/requirements.txt

# 2. Run
python3 run.py
```

Or install manually:
```bash
pip3 install fastapi uvicorn pandas numpy aiohttp websockets google-generativeai
```

## Features
- RSI Heatmap multi-timeframe (15m, 1h, 4h, 12h, 1d, 1w)
- Long & Short signals with 5 strength layers
- Real-time data from Binance API
- AI Trading Chatbot (powered by Google Gemini)

## AI Chatbot Setup
1. Click the **"AI Chat"** button (purple) in the header
2. Click **"Configure Gemini API Key"** or the Settings icon
3. Get a free API key at: https://aistudio.google.com/app/apikey
4. Paste your API key and click **Save**
5. Start chatting with AI!

**Note:** Gemini free tier has a limit of 15 requests/minute. If you see a "rate limit" error, wait 1 minute and try again.

## Tech Stack
- **Backend:** Python, FastAPI, Google Gemini AI
- **Frontend:** React, TypeScript, TailwindCSS
- **Data:** Binance API

## Team
Rabih Akbar Nurdin (PM), Yoga Bayu Samudra, Zia Ul Ihsan, Putu Satya Krisnaputra, Sigit Hadi Putranto

## Troubleshooting

### Port 8000 already in use
```bash
lsof -i :8000
kill -9 [PID]
python3 run.py
```

### Module not found
```bash
pip3 install -r backend/requirements.txt
```
