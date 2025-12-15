#!/usr/bin/env python3
"""
Crypto RSI Heatmap - Single command launcher
Usage: python3 run.py
"""
import subprocess
import sys
import os
import time
import threading
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
FRONTEND_HTML = os.path.join(BASE_DIR, 'frontend', 'index.html')
REQUIREMENTS_FILE = os.path.join(BACKEND_DIR, 'requirements.txt')

def install_dependencies():
    """Install required packages if missing"""
    required = ['fastapi', 'uvicorn', 'aiohttp', 'pandas', 'numpy']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"📦 Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-q',
            '-r', REQUIREMENTS_FILE
        ])
        print("✅ Dependencies installed")
    return True

def open_browser_delayed():
    """Open browser after short delay to ensure backend is ready"""
    time.sleep(2)
    webbrowser.open(f'file://{FRONTEND_HTML}')
    print(f"🌐 Browser opened: {FRONTEND_HTML}")

def main():
    print("=" * 50)
    print("🔥 Crypto RSI Heatmap")
    print("=" * 50)
    
    # Install dependencies if needed
    try:
        install_dependencies()
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Try running: pip install -r backend/requirements.txt")
        sys.exit(1)
    
    # Open browser in background thread
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # Start backend server
    print("🚀 Starting backend server on http://localhost:8000")
    print("📊 Frontend will open automatically in browser")
    print("-" * 50)
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    os.chdir(BACKEND_DIR)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == '__main__':
    main()
