# market/tick_processor.py
import logging
from core.event_bus import bus
from market.market_cache import cache

class TickProcessor:
    """
    Listens to raw ticks from the WebSocket and routes them to 
    the Cache and Candle engines.
    """
    def __init__(self):
        # Subscribe to the WebSocket stream
        bus.subscribe("TICK_UPDATE", self.process_tick)

    def process_tick(self, tick_data: dict):
        try:
            symbol = tick_data.get("token") # In production, map token to tradingsymbol (e.g., NIFTY24JUNFUT)
            ltp = tick_data.get("ltp")
            volume = tick_data.get("volume", 0)

            if not symbol or not ltp:
                return

            # 1. Update ultra-fast cache
            cache.update_price(symbol, ltp, volume)

            # 2. Forward to the Candle Aggregator
            bus.publish("PROCESS_CANDLE", tick_data)
            
        except Exception as e:
            logging.error(f"❌ [TICK PROCESSOR] Error handling tick: {e}")