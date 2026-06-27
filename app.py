# app.py
import logging
import time

# Part 1: Core & Market Data
from config.settings import settings
from brokers.broker_router import active_broker
from market.websocket_client import MarketDataStreamer
from market.tick_processor import TickProcessor
from market.candle_builder import CandleBuilder
from database.mongo import db_manager

# Part 2, 3, & 4: Strategies, Execution, AI Engine
from ai.model_engine import ai_engine
from ai.data_collector import ml_collector
from strategy.nifty_v6_ai import NiftyV6AIStrategy
from execution.order_manager import order_manager
from execution.trade_monitor import trade_monitor
from execution.risk_manager import risk_manager

# Part 5: The Web Dashboard
from dashboard.web_server import dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def boot_sequence():
    print("╔══════════════════════════════════════════════════╗")
    print("║      SRINU QUANT AI V5 (Institutional Edition)   ║")
    print("╚══════════════════════════════════════════════════╝")
    
    # 1. Broker Authentication
    if not active_broker.login():
        logging.error("Shutting down due to broker auth failure.")
        return

    # 2. Sync MongoDB State (Recovers exact Daily PnL & Streak from your legacy setup)
    risk_manager.perform_startup_sync() 

    # 3. Boot execution and strategy engines
    tick_proc = TickProcessor()
    candle_bldr = CandleBuilder(timeframe_minutes=5)
    v6_strategy = NiftyV6AIStrategy()
    
    # 4. Start the Web Dashboard on port 8080
    dashboard.start()

    # 5. Connect to live market (Nifty Fut Token)
    NIFTY_FUT_TOKEN = 256265 # Make sure this matches your actual Kite Nifty token!
    # 🔴 COMMENT OUT THE REAL STREAMER FOR WEEKEND TESTING
    # from market.websocket_client import MarketDataStreamer
    # streamer = MarketDataStreamer(instrument_tokens=[NIFTY_FUT_TOKEN])
    
    # 🟢 INJECT THE WEEKEND SIMULATOR
    from market.mock_streamer import MockMarketStreamer
    streamer = MockMarketStreamer(start_price=24000.0)
    
    streamer.start()

    logging.info("🚀 [SYSTEM LIVE] V5 Trading Architecture fully engaged.")

    # Keep the main process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("🛑 Shutting down V5 Engine gracefully...")

if __name__ == "__main__":
    boot_sequence()