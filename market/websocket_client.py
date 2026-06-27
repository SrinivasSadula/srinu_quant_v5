# market/websocket_client.py
import logging
import threading
from core.event_bus import bus
from config.settings import settings

try:
    from kiteconnect import KiteTicker
except ImportError:
    logging.warning("kiteconnect package not found. WebSocket will not run.")

class MarketDataStreamer:
    """
    Connects to the broker's WebSocket to receive live tick data.
    Pushes normalized tick data to the EventBus.
    """
    def __init__(self, instrument_tokens: list):
        self.tokens = instrument_tokens
        self.kws = None
        self.is_running = False

    def on_ticks(self, ws, ticks):
        """Callback for incoming ticks."""
        for tick in ticks:
            # Normalize the tick data so downstream components don't rely on Kite's specific format
            normalized_tick = {
                "token": tick.get("instrument_token"),
                "ltp": tick.get("last_price"),
                "volume": tick.get("volume_traded", 0),
                "oi": tick.get("oi", 0),
                "timestamp": tick.get("exchange_timestamp")
            }
            # 🚀 Fire it into the Event Bus!
            bus.publish("TICK_UPDATE", normalized_tick)

    def on_connect(self, ws, response):
        """Callback on successful connection."""
        logging.info("🟢 [WEBSOCKET] Connected to live market data feed.")
        ws.subscribe(self.tokens)
        ws.set_mode(ws.MODE_FULL, self.tokens)

    def on_close(self, ws, code, reason):
        logging.warning(f"🔴 [WEBSOCKET] Connection closed: {reason}")
        self.is_running = False

    def start(self):
        if settings.broker.MODE == "PAPER" and not settings.broker.KITE_ACCESS_TOKEN:
            logging.info("⚠️ [WEBSOCKET] Running in pure PAPER mode without live Kite token. Tick simulation required.")
            return

        logging.info("📡 [WEBSOCKET] Initializing KiteTicker...")
        self.kws = KiteTicker(settings.broker.KITE_API_KEY, settings.broker.KITE_ACCESS_TOKEN)
        
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close

        # Run the websocket in a background thread so it doesn't block the main app
        thread = threading.Thread(target=self.kws.connect, kwargs={"threaded": True}, daemon=True)
        thread.start()
        self.is_running = True