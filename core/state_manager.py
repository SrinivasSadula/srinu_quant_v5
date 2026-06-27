# core/state_manager.py
from datetime import datetime
import pytz

IST_TZ = pytz.timezone('Asia/Kolkata')

# This is your legacy state structure, now accessible by all modules
system_state = {
    "execution_mode": "PAPER",
    "broker_status": "DISCONNECTED",
    "market_indices": {
        "NIFTY 50": {"price": 0.0, "change": 0.0, "pChange": 0.0, "high": 0.0, "low": 0.0},
        "SENSEX": {"price": 74649.84, "change": 382.50, "pChange": 0.0, "high": 74700.0, "low": 74200.0},
    },
    "daily_pnl": 0.0,
    "total_trades": 0,
    "consecutive_losses": 0,
    "circuit_breaker_tripped": False,
    "active_trade": None,
    "closed_trades": [],
    "journal": [],
    "current_signal_status": "AWAITING MARKET OPEN",
    "active_broker": "ZERODHA",
    "groww_connected": False
}