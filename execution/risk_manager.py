# execution/risk_manager.py
import logging
from datetime import datetime
import threading
from database.mongo import db_manager
from config.settings import settings

class RiskManager:
    """
    Manages Drawdown, Streaks, and Live PnL. 
    Syncs flawlessly with MongoDB Atlas.
    """
    def __init__(self):
        self.lock = threading.RLock()
        
        # Original Quant State Variables
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.consecutive_losses = 0
        self.closed_trades = []
        
        self.max_loss_limit = -15000.0 # Define your max drawdown here

    def perform_startup_sync(self):
        """Fetches MongoDB data on boot. ONLY restores if data is from today."""
        logging.info("⏳ [STARTUP SYNC] Fetching MongoDB cloud data...")
        payload = db_manager.fetch_master_state()
        today_str = datetime.now().strftime('%Y-%m-%d')
        cloud_date = payload.get("date", "NO_DATE")
        
        with self.lock:
            if cloud_date == today_str:
                self.daily_pnl = float(payload.get("daily_pnl", 0.0))
                self.total_trades = int(payload.get("total_trades", 0))
                self.consecutive_losses = int(payload.get("consecutive_losses", 0))
                self.closed_trades = payload.get("closed_trades", [])
                logging.info(f"💾 [MONGO RESTORE] Recovered {self.total_trades} trades & ₹{self.daily_pnl:.2f} PnL.")
            else:
                logging.info("🌅 [STARTUP SYNC] Clean slate for today in MongoDB.")
                self.sync_to_cloud() # Wipe old data for the new day

    def sync_to_cloud(self):
        """Packs the current risk state and ships it to MongoDB."""
        with self.lock:
            payload = {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "daily_pnl": self.daily_pnl,
                "total_trades": self.total_trades,
                "consecutive_losses": self.consecutive_losses,
                "closed_trades": self.closed_trades
            }
        db_manager.push_master_state(payload)

    def is_trade_allowed(self) -> bool:
        with self.lock:
            if self.daily_pnl <= self.max_loss_limit:
                logging.warning("🛑 [RISK] MAX DAILY DRAWDOWN HIT. Trading halted.")
                return False
            if self.consecutive_losses >= 3:
                logging.warning("🛑 [RISK] 3 Consecutive Losses. Cooldown engaged.")
                return False
            return True

risk_manager = RiskManager()