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
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
REQUIREMENTS_FILE = os.path.join(BACKEND_DIR, 'requirements.txt')

def install_dependencies():
    """Install required packages if missing"""
    required = ['fastapi', 'uvicorn', 'aiohttp']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-q',
            '-r', REQUIREMENTS_FILE
        ])
        print("Dependencies installed")
    return True

def build_frontend():
    """Build the React frontend"""
    print("Building frontend...")
    subprocess.run(['npm', 'run', 'build'], cwd=FRONTEND_DIR, check=True)
    print("Frontend built successfully")

def open_browser_delayed():
    """Open browser after short delay to ensure backend is ready"""
    time.sleep(2)
    webbrowser.open('http://localhost:8000')
    print("Browser opened: http://localhost:8000")

def main():
    print("=" * 50)
    print("Crypto RSI Heatmap")
    print("=" * 50)
    
    try:
        install_dependencies()
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        print("Try running: pip install -r backend/requirements.txt")
        sys.exit(1)
    
    try:
        build_frontend()
    except Exception as e:
        print(f"Failed to build frontend: {e}")
        print("Try running: cd frontend && npm install && npm run build")
        sys.exit(1)
    
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    print("Starting server on http://localhost:8000")
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
        print("\nServer stopped")

if __name__ == '__main__':
    main()
