"""
Time-Series Data Cache Manager
Handles efficient storage and retrieval of historical data
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import redis
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of time-series data:
    1. In-memory cache for frequently accessed data
    2. Redis cache for distributed systems
    3. Automatic expiration and cleanup
    """

    def __init__(self, backend: str = 'memory', redis_url: Optional[str] = None):
        """
        Initialize Cache Manager
        
        Args:
            backend: 'memory' or 'redis'
            redis_url: Redis connection URL
        """
        self.backend = backend
        self.memory_cache: Dict[str, Any] = {}
        self.ttl_map: Dict[str, datetime] = {}  # Track expiration times
        
        if backend == 'redis' and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Falling back to memory cache.")
                self.backend = 'memory'
                self.redis_client = None
        else:
            self.redis_client = None

    def set(self, key: str, value: Any, ttl_minutes: int = 15):
        """
        Set cache value
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if dict/list)
            ttl_minutes: Time to live in minutes
        """
        expiration = datetime.now() + timedelta(minutes=ttl_minutes)
        
        if self.backend == 'memory':
            self.memory_cache[key] = value
            self.ttl_map[key] = expiration
        elif self.backend == 'redis' and self.redis_client:
            try:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                self.redis_client.setex(key, ttl_minutes * 60, value)
            except Exception as e:
                logger.error(f"Redis set failed: {e}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if expired/not found
        """
        if self.backend == 'memory':
            if key in self.ttl_map and datetime.now() > self.ttl_map[key]:
                # Expired
                del self.memory_cache[key]
                del self.ttl_map[key]
                return None
            return self.memory_cache.get(key)
        
        elif self.backend == 'redis' and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    # Try to parse JSON
                    try:
                        return json.loads(value.decode('utf-8'))
                    except:
                        return value.decode('utf-8')
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
        
        return None

    def cache_ohlcv(self, symbol: str, timeframe: str, data: pd.DataFrame, ttl_minutes: int = 15):
        """
        Cache OHLCV data
        
        Args:
            symbol: Symbol (e.g., 'ES', 'SPY')
            timeframe: Timeframe (e.g., '5min', '1h')
            data: OHLCV DataFrame
            ttl_minutes: Cache TTL
        """
        key = f"ohlcv:{symbol}:{timeframe}"
        # Convert DataFrame to dict for caching
        value = data.to_dict(orient='records')
        self.set(key, value, ttl_minutes)

    def get_ohlcv(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Get cached OHLCV data
        
        Args:
            symbol: Symbol
            timeframe: Timeframe
        
        Returns:
            OHLCV DataFrame or None
        """
        key = f"ohlcv:{symbol}:{timeframe}"
        value = self.get(key)
        if value:
            return pd.DataFrame(value)
        return None

    def cache_indicators(self, symbol: str, indicators: Dict[str, float], ttl_minutes: int = 5):
        """
        Cache technical indicators
        
        Args:
            symbol: Symbol
            indicators: Dictionary of indicator values
            ttl_minutes: Cache TTL
        """
        key = f"indicators:{symbol}"
        self.set(key, indicators, ttl_minutes)

    def get_indicators(self, symbol: str) -> Optional[Dict]:
        """
        Get cached indicators
        
        Args:
            symbol: Symbol
        
        Returns:
            Indicators dictionary or None
        """
        key = f"indicators:{symbol}"
        return self.get(key)

    def cache_ml_forecast(self, symbol: str, forecast: Dict, ttl_minutes: int = 5):
        """
        Cache ML model forecast
        
        Args:
            symbol: Symbol
            forecast: Forecast dictionary
            ttl_minutes: Cache TTL
        """
        key = f"forecast:{symbol}"
        self.set(key, forecast, ttl_minutes)

    def get_ml_forecast(self, symbol: str) -> Optional[Dict]:
        """
        Get cached ML forecast
        
        Args:
            symbol: Symbol
        
        Returns:
            Forecast dictionary or None
        """
        key = f"forecast:{symbol}"
        return self.get(key)

    def clear_expired(self):
        """
        Remove all expired entries from memory cache
        """
        if self.backend == 'memory':
            expired_keys = [
                k for k, expiration in self.ttl_map.items()
                if datetime.now() > expiration
            ]
            for key in expired_keys:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.ttl_map:
                    del self.ttl_map[key]
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if self.backend == 'memory':
            return {
                'backend': 'memory',
                'total_entries': len(self.memory_cache),
                'expired_entries': len([k for k, exp in self.ttl_map.items() if datetime.now() > exp])
            }
        else:
            return {
                'backend': 'redis',
                'status': 'connected' if self.redis_client else 'disconnected'
            }
