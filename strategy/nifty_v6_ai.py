# strategy/nifty_v6_ai.py
import logging
import pandas as pd
import pandas_ta as ta
import numpy as np

from core.strategy_base import StrategyBase
from strategy.ict_engine import ICTMathEngine
from core.event_bus import bus
from config.settings import settings
from ai.model_engine import ai_engine

class NiftyV6AIStrategy(StrategyBase):
    """
    The production implementation of the V6 Multi-Directional Volatility Engine.
    Combines deterministic ICT math with the XGBoost AI model.
    Fully integrated with the ML Feedback Loop (Part 4).
    """
    def __init__(self):
        # We don't need to pass the model in __init__ anymore, we use the global ai_engine
        super().__init__(name="V6_ICT_AI_Engine", symbol=settings.SYMBOL)
        
    def on_data_ready(self, df: pd.DataFrame):
        # Only run if the brain is loaded and ready
        if not ai_engine.is_loaded:
            return

        try:
            # 1. Base Indicators (TA-Lib / Pandas-TA)
            df.ta.atr(length=14, append=True)
            df.ta.rsi(length=14, append=True)
            df.ffill(inplace=True)
            
            # Setup Date boundaries
            df['Date_Only'] = df.index.date
            
            # 2. V6 Structural Math (TWAP, Day Highs, Prev Day Highs)
            df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
            df['TWAP_Daily'] = df.groupby('Date_Only')['Typical_Price'].transform(lambda x: x.expanding().mean())
            df['VWAP_Dist_Pct'] = ((df['close'] - df['TWAP_Daily']) / df['TWAP_Daily']) * 100
            
            # Prevent Division by Zero if ATR is 0 early in the day
            atr = df['ATRr_14'].replace(0, np.nan)
            df['Velocity_3'] = df['close'].diff(3) / atr
            
            body = abs(df['close'] - df['open'])
            rng = (df['high'] - df['low']).replace(0, np.nan)
            df['Body_Ratio'] = (body / rng).fillna(0.5).clip(0, 1)
            
            df['Prev_Day_High'] = df['Date_Only'].map(df.groupby('Date_Only')['high'].max().shift(1))
            df['Prev_Day_Low'] = df['Date_Only'].map(df.groupby('Date_Only')['low'].min().shift(1))
            df['Dist_to_PDH'] = (df['close'] - df['Prev_Day_High']) / atr
            df['Dist_to_PDL'] = (df['close'] - df['Prev_Day_Low']) / atr
            
            df['Dist_to_Day_High'] = (df['close'] - df.groupby('Date_Only')['high'].transform('cummax')) / atr
            df['Dist_to_Day_Low'] = (df['close'] - df.groupby('Date_Only')['low'].transform('cummin')) / atr
            
            # Volatility Regime (Rolling 1500 bar rank ~ 20 days)
            df['Vol_Regime'] = pd.cut(df['ATRr_14'].rolling(window=1500, min_periods=300).rank(pct=True), 
                                      bins=[0, 0.33, 0.67, 1.0], labels=[0, 1, 2]).astype(float)

            # 3. Apply ICT Deterministic Math (from Part 2)
            df = ICTMathEngine.calculate_fvg(df)
            df = ICTMathEngine.calculate_sweeps(df)
            df = ICTMathEngine.calculate_displacement(df)
            df = ICTMathEngine.calculate_or_distance(df)

            # 4. AI Inference through the dedicated engine
            ai_prediction = ai_engine.predict(df)
            buy_prob = ai_prediction["buy_prob"]
            sell_prob = ai_prediction["sell_prob"]
            
            # Broadcast live AI thinking state for the Web Dashboard
            bus.publish("AI_STATE_UPDATE", {"buy_prob": buy_prob, "sell_prob": sell_prob})

            # 5. Extract current features as a dictionary to pass to the ML Data Collector
            # If the AI engine is loaded, it knows exactly which features it expects
            if ai_engine.expected_features:
                current_feature_dict = df[ai_engine.expected_features].iloc[-1].fillna(0.0).to_dict()
            else:
                current_feature_dict = {}

            # 6. Execute Asymmetric Logic (Trigger thresholds from settings.py)
            current_price = df['close'].iloc[-1]
            current_atr = df['ATRr_14'].iloc[-1]
            
            if buy_prob >= settings.ai.BUY_THRESHOLD:
                logging.info(f"🟢 [V6 AI] High Conviction BUY | Prob: {buy_prob:.2f}")
                self._emit_signal("BUY", current_price, current_atr, current_feature_dict)
                
            elif sell_prob >= settings.ai.SELL_THRESHOLD:
                logging.info(f"🔴 [V6 AI] High Conviction SELL | Prob: {sell_prob:.2f}")
                self._emit_signal("SELL", current_price, current_atr, current_feature_dict)

        except Exception as e:
            logging.error(f"❌ [V6 STRATEGY ERROR]: {e}")

    def _emit_signal(self, side: str, price: float, atr: float, features: dict):
        """
        Calculates dynamic V6 targets and emits to the Event Bus for execution.
        """
        # Dynamic 1:1 True ATR Targets (Matches V6 Training Exactly)
        sl_dist = atr * 2.0
        tp_dist = atr * 2.0
        
        sl_price = price - sl_dist if side == "BUY" else price + sl_dist
        tp_price = price + tp_dist if side == "BUY" else price - tp_dist
        
        signal_data = {
            "symbol": self.symbol,
            "side": side,
            "entry": price,
            "sl": round(sl_price, 2),
            "tp": round(tp_price, 2),
            "qty": settings.risk.MAX_LOTS,
            "ai_features": features  # <--- Handed to OrderManager, then sent to ML Collector!
        }
        
        # Send to the Order Manager (Part 3)
        bus.publish("TRADE_SIGNAL", signal_data)