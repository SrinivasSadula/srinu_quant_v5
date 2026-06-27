# market/market_cache.py
import threading
from typing import Dict, Any

class MarketCache:
    """
    Ultra-low latency in-memory state store for live market data.
    Acts as a local Redis replacement for sub-millisecond access.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def update_price(self, symbol: str, ltp: float, volume: int):
        with self._lock:
            if symbol not in self._cache:
                self._cache[symbol] = {"high": ltp, "low": ltp, "volume": 0}
            
            state = self._cache[symbol]
            state["ltp"] = ltp
            state["volume"] = volume
            if ltp > state["high"]: state["high"] = ltp
            if ltp < state["low"]: state["low"] = ltp

    def get_state(self, symbol: str) -> Dict[str, Any]:
        with self._lock:
            return self._cache.get(symbol, {})

# Global singleton
cache = MarketCache()