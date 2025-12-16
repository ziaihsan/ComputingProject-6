
import asyncio
import aiohttp
import uvicorn
import multiprocessing
import time
import sys
import os

# Import app to ensure it loads correctly
try:
    from main import app
except Exception as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

async def test_endpoint():
    print("Waiting for server to start...")
    await asyncio.sleep(2)
    
    async with aiohttp.ClientSession() as session:
        try:
            print("Testing /api/heatmap...")
            async with session.get("http://127.0.0.1:8001/api/heatmap?limit=5&timeframe=4h") as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print("Success!")
                    print(f"Total coins: {data.get('total_coins')}")
                    if data.get('signals'):
                        print("First signal sample:", data['signals'][0])
                else:
                    text = await resp.text()
                    print(f"Failed: {text}")
        except Exception as e:
            print(f"Request failed: {e}")

def main():
    # Start server in a separate process
    proc = multiprocessing.Process(target=run_server)
    proc.start()
    
    try:
        # Run async test
        asyncio.run(test_endpoint())
    finally:
        # Cleanup
        proc.terminate()
        proc.join()

if __name__ == "__main__":
    # Fix for Windows multiprocessing
    multiprocessing.freeze_support()
    main()
