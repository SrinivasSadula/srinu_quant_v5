# core/strategy_base.py
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
from core.event_bus import bus

class StrategyBase(ABC):
    """
    Abstract base class for all trading strategies in V5.
    Listens to 'CANDLE_CLOSED' events and maintains its own history.
    """
    def __init__(self, name: str, symbol: str, history_size: int = 1500):
        self.name = name
        self.symbol = symbol
        self.history_size = history_size
        
        # We store history in a fast list of dicts, converting to DataFrame only when needed
        self.history: list[Dict[str, Any]] = []
        
        bus.subscribe("CANDLE_CLOSED", self._on_candle)
        logging.info(f"🧠 [STRATEGY] '{self.name}' initialized and listening for {self.symbol} candles.")

    def _on_candle(self, candle: dict):
        if candle.get("symbol") != self.symbol:
            return
            
        self.history.append(candle)
        
        # Keep memory clean
        if len(self.history) > self.history_size:
            self.history.pop(0)

        # Only run logic if we have enough data to calculate indicators (e.g., 200 EMA)
        if len(self.history) > 200:
            df = pd.DataFrame(self.history)
            df.set_index('timestamp', inplace=True)
            self.on_data_ready(df)

    @abstractmethod
    def on_data_ready(self, df: pd.DataFrame):
        """
        Called every time a new candle closes and the history DataFrame is ready.
        Implement indicator calculations and AI inference here.
        """
        pass