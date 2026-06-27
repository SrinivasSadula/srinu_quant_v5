# ai/data_collector.py
import logging
from datetime import datetime
from core.event_bus import bus
from database.mongo import db_manager

class MLDataCollector:
    """
    The Institutional Feedback Loop. 
    Captures live feature states at the moment of entry and matches 
    them with the final trade outcome to build a proprietary V7 training dataset.
    """
    def __init__(self):
        # Temporarily stores the AI features while the trade is active in the market
        self.pending_features = {}
        
        # Listen for trade lifecycle events from the EventBus
        bus.subscribe("TRADE_OPENED", self.on_trade_opened)
        bus.subscribe("TRADE_CLOSED", self.on_trade_closed)
        
        logging.info("🧠 [ML STORE] Data Collector initialized. Awaiting live trades...")

    def on_trade_opened(self, trade_data: dict):
        """Called when a trade executes. We save the exact AI features here."""
        ticket = trade_data.get("ticket")
        features = trade_data.get("ai_features") # Passed from strategy/nifty_v6_ai.py
        
        if ticket and features:
            self.pending_features[ticket] = features
            logging.info(f"💾 [ML STORE] Captured entry features for ticket #{ticket}")

    def on_trade_closed(self, trade_data: dict):
        """Called when a trade exits. We link the PnL to the entry features."""
        ticket = trade_data.get("ticket")
        
        # If your broker/watchdog doesn't pass the ticket back on close, 
        # you might need to map it via the symbol. Assuming ticket is passed for precision:
        # (In our trade_monitor.py we passed symbol, so let's extract the ticket from active_trade if needed, 
        # but ideally we pass 'ticket' in the TRADE_CLOSED event payload).
        # Fallback: if we just have symbol, we might have to search pending_features, but let's assume strict ticket tracking.
        
        # NOTE: Make sure your execution/trade_monitor.py includes the 'ticket' in the TRADE_CLOSED event!
        ticket = trade_data.get("ticket", trade_data.get("symbol")) 
        pnl = trade_data.get("pnl", 0.0)
        
        if ticket in self.pending_features:
            features = self.pending_features.pop(ticket)
            
            # Map PnL to Target Label for future XGBoost training
            # 1 = Win (Profitable), 0 = Loss (Chop / Stop Loss)
            target_label = 1 if pnl > 0 else 0
            
            ml_record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": trade_data.get("symbol"),
                "features": features,
                "target": target_label,
                "realized_pnl": pnl,
                "exit_reason": trade_data.get("reason", "UNKNOWN")
            }
            
            # 🚨 THE UPDATE: Use the dedicated ML Mongo function so we don't overwrite Risk State!
            db_manager.push_ml_record(ticket=ticket, payload=ml_record)
            
            logging.info(f"🧠 [ML STORE] Trade complete. Labeled target '{target_label}' saved to Mongo for V7 evolution.")

# Global Singleton Initialization
ml_collector = MLDataCollector()