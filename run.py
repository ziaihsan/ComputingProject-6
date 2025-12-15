#!/usr/bin/env python3
import subprocess
import webbrowser
import time
import os

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
FRONTEND_HTML = os.path.join(BASE_DIR, 'frontend', 'index.html')

print("🚀 Starting Crypto Heatmap...")

# Open frontend in browser
webbrowser.open(f'file://{FRONTEND_HTML}')
print(f"✅ Browser opened: {FRONTEND_HTML}")

# Run backend
print("✅ Starting backend on http://localhost:8000")
os.chdir(BACKEND_DIR)
subprocess.run(['python3', '-m', 'uvicorn', 'main:app', '--reload', '--port', '8000'])
