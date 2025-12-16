import sqlite3
import json
import time
import os
from typing import Optional, Dict, Any

class CacheManager:
    def __init__(self, db_path: str = "heatmap_cache.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
        self.init_db()

    def init_db(self):
        """Initialize the cache table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    key TEXT PRIMARY KEY,
                    data TEXT,
                    timestamp REAL,
                    expires_at REAL
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Cache init failed: {e}")

    def _get_cache_key(self, limit: int, timeframe: str) -> str:
        return f"heatmap_{limit}_{timeframe}"

    def get_cache(self, limit: int, timeframe: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache if valid"""
        try:
            key = self._get_cache_key(limit, timeframe)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = time.time()
            # Clean old cache while we are here
            cursor.execute("DELETE FROM api_cache WHERE expires_at < ?", (now,))
            
            cursor.execute("SELECT data FROM api_cache WHERE key = ? AND expires_at > ?", (key, now))
            row = cursor.fetchone()
            conn.commit() # Commit the cleanup
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            print(f"Cache get failed: {e}")
            return None

    def set_cache(self, limit: int, timeframe: str, data: Dict[str, Any], ttl_seconds: int = 300):
        """Store data in cache"""
        try:
            key = self._get_cache_key(limit, timeframe)
            now = time.time()
            expires_at = now + ttl_seconds
            json_data = json.dumps(data)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO api_cache (key, data, timestamp, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (key, json_data, now, expires_at))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Cache set failed: {e}")
