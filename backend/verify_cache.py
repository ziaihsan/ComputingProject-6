
import asyncio
import aiohttp
import time
import multiprocessing
import uvicorn
import os
import sys

# Ensure backend dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
except ImportError:
    # Try importing assuming run from backend dir
    sys.path.append('.') 
    from main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")

async def test_caching():
    print("Waiting for server to start...")
    await asyncio.sleep(2)
    
    url = "http://127.0.0.1:8002/api/heatmap?limit=5&timeframe=4h"
    
    async with aiohttp.ClientSession() as session:
        # Request 1: Should be MISS (First fetch)
        print("\n--- Request 1 (Expect MISS) ---")
        start = time.time()
        async with session.get(url) as resp:
            data = await resp.json()
            headers = resp.headers
            print(f"Status: {resp.status}")
            print(f"X-Cache: {headers.get('X-Cache')}")
            print(f"Time: {time.time() - start:.2f}s")
            
        # Request 2: Should be HIT (Cached)
        print("\n--- Request 2 (Expect HIT) ---")
        start = time.time()
        async with session.get(url) as resp:
            data = await resp.json()
            headers = resp.headers
            print(f"Status: {resp.status}")
            print(f"X-Cache: {headers.get('X-Cache')}")
            print(f"Time: {time.time() - start:.2f}s")
            
        if headers.get('X-Cache') == 'HIT':
            print("\nSUCCESS: Caching is working!")
        else:
            print("\nFAILURE: Caching did not work.")

def main():
    # Start server in a separate process
    proc = multiprocessing.Process(target=run_server)
    proc.start()
    
    try:
        # Run async test
        asyncio.run(test_caching())
    finally:
        # Cleanup
        proc.terminate()
        proc.join()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
