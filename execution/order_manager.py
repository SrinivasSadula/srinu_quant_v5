# execution/order_manager.py
import logging
from core.event_bus import bus
from brokers.broker_router import active_broker
from market.option_chain import option_selector
from execution.risk_manager import risk_manager

class OrderManager:
    """
    Listens for AI Trade Signals, translates them into Option orders, 
    and routes them to the active broker.
    """
    def __init__(self):
        self.active_trade = None
        bus.subscribe("TRADE_SIGNAL", self.handle_signal)

    def handle_signal(self, signal: dict):
        # 1. Check if we are already in a trade (No pyramiding in this version)
        if self.active_trade is not None:
            logging.info("⏳ [ORDER MANAGER] Ignoring signal. Position already active.")
            return

        # 2. Institutional Risk Check
        if not risk_manager.is_trade_allowed():
            return

        spot_price = signal["entry"]
        side = signal["side"]
        qty = signal["qty"]

        # 3. Translate Index Signal to Option Contract
        try:
            option_symbol = option_selector.generate_contract_symbol(spot_price, side)
        except Exception as e:
            logging.error(f"❌ [ORDER MANAGER] Failed to select option strike: {e}")
            return

        # 4. Execute the Trade (We ALWAYS BUY options, we do not short sell them)
        # If AI says SELL Nifty, we BUY a Put Option.
        result = active_broker.place_order(
            symbol=option_symbol, 
            side="BUY",  # Buying the CE or PE
            qty=qty, 
            order_type="MARKET"
        )

        # 5. Register the Active Trade
        if result.get("status") == "success":
            self.active_trade = {
                "ticket": result.get("order_id"),
                "option_symbol": option_symbol,
                "spot_entry": spot_price,
                "spot_sl": signal["sl"],
                "spot_tp": signal["tp"],
                "qty": qty,
                "side": side # The underlying Nifty direction
            }
            logging.info(f"✅ [ORDER MANAGER] Trade Executed & Registered. Tracking Index targets.")
            bus.publish("TRADE_OPENED", self.active_trade)

    def clear_active_trade(self):
        self.active_trade = None

order_manager = OrderManager()