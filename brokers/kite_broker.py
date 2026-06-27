# brokers/kite_broker.py
import logging
import time
from typing import Dict, Any
from core.event_bus import bus
from config.settings import settings

try:
    from kiteconnect import KiteConnect
except ImportError:
    logging.warning("kiteconnect package not found. KiteBroker will fail in LIVE mode.")

class KiteBroker:
    """
    Implementation of the BrokerBase for Zerodha Kite.
    Includes built-in Paper Trading safety rails.
    """
    def __init__(self):
        self.kite = None
        self.mode = settings.broker.MODE  # "LIVE" or "PAPER"
        self.is_connected = False

    def login(self) -> bool:
        logging.info(f"🔑 [KITE] Initializing login sequence in {self.mode} mode...")
        if self.mode == "PAPER":
            self.is_connected = True
            logging.info("✅ [KITE PAPER] Successfully initialized virtual broker.")
            return True
            
        try:
            self.kite = KiteConnect(api_key=settings.broker.KITE_API_KEY)
            # In a real production app, you'd handle the request_token & access_token flow here
            self.kite.set_access_token(settings.broker.KITE_ACCESS_TOKEN)
            self.is_connected = True
            logging.info("✅ [KITE LIVE] Successfully authenticated with Zerodha API.")
            return True
        except Exception as e:
            logging.error(f"❌ [KITE LIVE] Login failed: {e}")
            return False

    def place_order(self, symbol: str, side: str, qty: int, price: float = 0.0, order_type: str = "MARKET") -> Dict[str, Any]:
        logging.info(f"🔄 [KITE {self.mode}] Executing {side} | {qty} qty | {symbol} @ {price}")
        
        if self.mode == "PAPER":
            # Simulate a successful order
            virtual_order_id = f"PAPER_{int(time.time())}"
            logging.info(f"✅ [KITE PAPER] Virtual Order Placed: {virtual_order_id}")
            return {"status": "success", "order_id": virtual_order_id, "price": price}

        try:
            # LIVE EXECUTION
            kite_order_type = self.kite.ORDER_TYPE_MARKET if order_type == "MARKET" else self.kite.ORDER_TYPE_LIMIT
            kite_transaction_type = self.kite.TRANSACTION_TYPE_BUY if side == "BUY" else self.kite.TRANSACTION_TYPE_SELL
            
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NFO,  # Nifty Options
                tradingsymbol=symbol,
                transaction_type=kite_transaction_type,
                quantity=qty,
                product=self.kite.PRODUCT_MIS,    # Intraday
                order_type=kite_order_type,
                price=price
            )
            logging.info(f"✅ [KITE LIVE] Order Placed: {order_id}")
            return {"status": "success", "order_id": order_id}
        except Exception as e:
            logging.error(f"❌ [KITE LIVE] Order Failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_positions(self) -> list:
        if self.mode == "PAPER":
            return [] # In a full system, you would query your local DB for paper positions
            
        try:
            return self.kite.positions().get("net", [])
        except Exception as e:
            logging.error(f"❌ [KITE LIVE] Failed to fetch positions: {e}")
            return []