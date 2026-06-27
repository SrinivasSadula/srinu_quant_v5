# brokers/broker_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BrokerBase(ABC):
    """
    Abstract Base Class for all broker integrations.
    Any new broker (Kite, Groww, Dhan) MUST implement these methods.
    """
    
    @abstractmethod
    def login(self) -> bool:
        """Authenticate with the broker API."""
        pass

    @abstractmethod
    def place_order(self, symbol: str, side: str, qty: int, price: float = 0.0, order_type: str = "MARKET") -> Dict[str, Any]:
        """Execute a trade. Side should be 'BUY' or 'SELL'."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        pass

    @abstractmethod
    def get_positions(self) -> list:
        """Return a list of current open positions."""
        pass

    @abstractmethod
    def subscribe_ticks(self, tokens: list):
        """Subscribe to live websocket ticks for given tokens."""
        pass