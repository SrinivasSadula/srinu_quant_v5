# market/candle_builder.py
import logging
from datetime import datetime
from core.event_bus import bus
import pandas as pd

class CandleBuilder:
    """
    Aggregates sub-second ticks into standardized OHLCV candles.
    """
    def __init__(self, timeframe_minutes: int = 5):
        self.timeframe = timeframe_minutes
        self.current_candle = {}
        bus.subscribe("PROCESS_CANDLE", self.aggregate_tick)

    def aggregate_tick(self, tick: dict):
        symbol = tick.get("token")
        ltp = tick.get("ltp")
        vol = tick.get("volume", 0)
        now = datetime.now()
        
        # Calculate the current 5-minute boundary
        minute_bucket = (now.minute // self.timeframe) * self.timeframe
        candle_timestamp = now.replace(minute=minute_bucket, second=0, microsecond=0)

        if symbol not in self.current_candle:
            self._init_new_candle(symbol, ltp, vol, candle_timestamp)
            return

        active = self.current_candle[symbol]
        
        # Check if we crossed into a new 5-minute window
        if candle_timestamp > active["timestamp"]:
            # Close the old candle and broadcast it to the AI!
            bus.publish("CANDLE_CLOSED", active)
            logging.info(f"📊 [CANDLE BUILDER] {self.timeframe}m Candle Closed for {symbol}: C={active['close']}")
            
            # Start the new one
            self._init_new_candle(symbol, ltp, vol, candle_timestamp)
        else:
            # Update running candle
            active["close"] = ltp
            active["volume"] += vol
            if ltp > active["high"]: active["high"] = ltp
            if ltp < active["low"]: active["low"] = ltp

    def _init_new_candle(self, symbol, ltp, vol, timestamp):
        self.current_candle[symbol] = {
            "symbol": symbol,
            "timestamp": timestamp,
            "open": ltp,
            "high": ltp,
            "low": ltp,
            "close": ltp,
            "volume": vol
        }