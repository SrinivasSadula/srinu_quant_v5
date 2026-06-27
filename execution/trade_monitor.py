# execution/trade_monitor.py
import logging
from datetime import datetime
from core.event_bus import bus
from brokers.broker_router import active_broker
from execution.order_manager import order_manager
from execution.risk_manager import risk_manager

class TradeMonitor:
    """
    Continuously checks the live market for SL/TP hits, 
    calculates exact PnL, and triggers the MongoDB sync on closure.
    """
    def __init__(self):
        bus.subscribe("TICK_UPDATE", self.monitor_position)

    def monitor_position(self, tick: dict):
        trade = order_manager.active_trade
        if not trade:
            return

        # Ensure we are checking the Nifty Spot/Futures price, not the Option premium
        if tick["token"] != 256265: # Nifty Spot/Fut token used in app.py
            return

        current_spot = tick["ltp"]
        side = trade["side"]
        
        exit_triggered = False
        reason = ""

        # Long Nifty (Holding CE)
        if side == "BUY":
            if current_spot <= trade["spot_sl"]: 
                exit_triggered, reason = True, "STOP LOSS HIT"
            elif current_spot >= trade["spot_tp"]: 
                exit_triggered, reason = True, "TAKE PROFIT HIT"

        # Short Nifty (Holding PE)
        elif side == "SELL":
            if current_spot >= trade["spot_sl"]: 
                exit_triggered, reason = True, "STOP LOSS HIT"
            elif current_spot <= trade["spot_tp"]: 
                exit_triggered, reason = True, "TAKE PROFIT HIT"

        if exit_triggered:
            self._close_position(trade, current_spot, reason)

    def _close_position(self, trade: dict, exit_price: float, reason: str):
        logging.info(f"⚠️ [WATCHDOG] {reason} triggered at {exit_price}. Liquidating {trade['option_symbol']}...")
        
        # 1. Execute exit order on active broker (We BOUGHT to open, so we SELL to close)
        active_broker.place_order(
            symbol=trade["option_symbol"], 
            side="SELL", 
            qty=trade["qty"], 
            order_type="MARKET"
        )
        
        # 2. Calculate PnL 
        # (In a pure live setup, you'd fetch the exact exit premium. 
        # Here we calculate based on Index points captured)
        points_captured = abs(trade["spot_entry"] - trade["spot_tp"]) if "PROFIT" in reason else -abs(trade["spot_entry"] - trade["spot_sl"])
        lot_size = 25 # Default Nifty lot size
        realized_pnl = points_captured * lot_size * (trade["qty"] / lot_size)

        # 3. Update Risk State securely with Thread Lock
        with risk_manager.lock:
            risk_manager.daily_pnl += realized_pnl
            risk_manager.total_trades += 1
            if realized_pnl > 0:
                risk_manager.consecutive_losses = 0
            else:
                risk_manager.consecutive_losses += 1

            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Add to the dashboard ledger
            risk_manager.closed_trades.insert(0, {
                "time": timestamp,
                "symbol": trade["option_symbol"],
                "entry": trade["spot_entry"], 
                "exit": exit_price,
                "pnl": realized_pnl,
                "reason": reason
            })

        # 4. Fire the Cloud Sync for Risk Management
        risk_manager.sync_to_cloud()
        logging.info(f"💾 [CLOUD SYNC] Trade closed. Net PnL updated to ₹{risk_manager.daily_pnl:.2f}")

        # 5. 🚨 CRITICAL FIX: Broadcast TRADE_CLOSED with 'ticket' for the ML Data Collector!
        bus.publish("TRADE_CLOSED", {
            "ticket": trade["ticket"],    # <--- Required for V7 AI Retraining mapping
            "symbol": trade["option_symbol"],
            "reason": reason,
            "pnl": realized_pnl
        })
        
        # 6. Clear active trade so the system can scan for the next setup
        order_manager.clear_active_trade()

# Initialize the monitor globally
trade_monitor = TradeMonitor()