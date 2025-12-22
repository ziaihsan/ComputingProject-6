#!/usr/bin/env python3
"""
Crypto RSI Heatmap - Demo Mode Launcher
Usage: python3 run-demo.py

This runs a standalone demo version without requiring backend/API connection.
"""
import os
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_HTML = os.path.join(BASE_DIR, 'frontend', 'demo-old.html')

def main():
    print("=" * 50)
    print("Crypto RSI Heatmap - DEMO MODE")
    print("=" * 50)
    print("Opening demo version in browser...")
    print("Note: This uses simulated data, not live API.")
    print("=" * 50)
    
    webbrowser.open(f'file://{DEMO_HTML}')
    print(f"Opened: {DEMO_HTML}")

if __name__ == '__main__':
    main()
