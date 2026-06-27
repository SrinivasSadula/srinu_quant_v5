# market/mock_streamer.py
import time
import random
import threading
import logging
from datetime import datetime, timedelta
from core.event_bus import bus
from config.settings import settings

class MockMarketStreamer:
    """
    Simulates a live market environment for weekend testing.
    Instantly injects 200 historical candles to prime the AI, 
    then streams sub-second ticks.
    """
    def __init__(self, start_price=24000.0):
        self.current_price = start_price
        self.is_running = False

    def _prime_the_ai(self):
        logging.info("💉 [SIMULATOR] Injecting 200 historical candles to wake up the AI...")
        now = datetime.now()
        
        # Blast 200 candles into the event bus
        for i in range(210):
            # Create a slight random trend so the AI has something to analyze
            trend = random.uniform(-5.0, 5.0) 
            self.current_price += trend
            
            candle = {
                "symbol": settings.SYMBOL,
                "timestamp": now - timedelta(minutes=5 * (210 - i)),
                "open": self.current_price - trend,
                "high": self.current_price + 15.0,
                "low": self.current_price - 15.0,
                "close": self.current_price,
                "volume": random.randint(1000, 5000)
            }
            # Directly fire the candle closed event (bypassing the Tick -> Candle builder for speed)
            bus.publish("CANDLE_CLOSED", candle)
            
        logging.info("✅ [SIMULATOR] AI Priming complete. Starting live tick stream...")

    def _simulate_ticks(self):
        self._prime_the_ai()
        
        while self.is_running:
            # Generate a realistic random walk (-3 to +3 Nifty points per tick)
            move = random.uniform(-3.0, 3.0)
            self.current_price += move
            
            tick = {
                "token": 256265, # Must match your NIFTY_FUT_TOKEN in app.py
                "ltp": round(self.current_price, 2),
                "volume": random.randint(10, 100),
                "timestamp": datetime.now().isoformat()
            }
            
            # Fire the tick into the main system
            bus.publish("TICK_UPDATE", tick)
            
            # 2 ticks per second
            time.sleep(0.5) 

    def start(self):
        self.is_running = True
        thread = threading.Thread(target=self._simulate_ticks, daemon=True)
        thread.start()