# market/option_chain.py
import logging
from datetime import datetime

class OptionSelector:
    """
    Translates Index/Spot signals into tradable Option Contracts.
    """
    def __init__(self, symbol_prefix: str = "NIFTY", strike_step: int = 50):
        self.symbol_prefix = symbol_prefix
        self.strike_step = strike_step
        # In a production environment, this would be fetched dynamically from the broker API
        self.current_expiry_str = "24JUN" # Example: 2024 June Expiry

    def get_atm_strike(self, spot_price: float) -> int:
        """Rounds the spot price to the nearest Nifty strike (e.g., 24020 -> 24000)"""
        return int(round(spot_price / self.strike_step) * self.strike_step)

    def generate_contract_symbol(self, spot_price: float, side: str) -> str:
        """
        Generates the exact broker trading symbol.
        BUY Signal -> Call Option (CE)
        SELL Signal -> Put Option (PE)
        """
        atm_strike = self.get_atm_strike(spot_price)
        
        # If AI says BUY the market, we buy a Call Option
        if side == "BUY":
            option_type = "CE"
        # If AI says SELL the market, we buy a Put Option
        elif side == "SELL":
            option_type = "PE"
        else:
            raise ValueError(f"Invalid side {side}")

        # Example Output: NIFTY24JUN24000CE
        contract_symbol = f"{self.symbol_prefix}{self.current_expiry_str}{atm_strike}{option_type}"
        logging.info(f"🎯 [OPTION SELECTOR] Spot: {spot_price} | Selected Strike: {contract_symbol}")
        return contract_symbol

# Singleton instance
option_selector = OptionSelector()