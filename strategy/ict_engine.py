# strategy/ict_engine.py
import pandas as pd
import numpy as np

class ICTMathEngine:
    """
    Deterministic mathematical definitions for ICT/SMC structures.
    These calculations exactly match the V6 training environment.
    """
    
    @staticmethod
    def calculate_fvg(df: pd.DataFrame) -> pd.DataFrame:
        """
        Proper 3-Candle ICT Fair Value Gap calculation.
        Requires the gap to exist AND the middle candle body to not close into it.
        """
        # Bullish FVG
        bull_gap_open = df['low'] > df['high'].shift(2)
        bull_mid_clean = df['high'].shift(1) < df['low']
        bull_gap_size = df['low'] - df['high'].shift(2)
        df['FVG_Bull'] = np.where(bull_gap_open & bull_mid_clean, bull_gap_size, 0.0)

        # Bearish FVG
        bear_gap_open = df['high'] < df['low'].shift(2)
        bear_mid_clean = df['low'].shift(1) > df['high']
        bear_gap_size = df['high'] - df['low'].shift(2) # Negative value
        df['FVG_Bear'] = np.where(bear_gap_open & bear_mid_clean, bear_gap_size, 0.0)

        df['FVG_Net'] = df['FVG_Bull'] + df['FVG_Bear']
        return df

    @staticmethod
    def calculate_sweeps(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """
        Proper ICT Liquidity Sweep (The 'Trap').
        Wick must penetrate the rolling high/low, but the close MUST be back inside.
        """
        roll_high = df['high'].shift(1).rolling(window=window, min_periods=window//2).max()
        roll_low = df['low'].shift(1).rolling(window=window, min_periods=window//2).min()

        # Swept high but closed below the high
        swept_high = (df['high'] > roll_high) & (df['close'] < roll_high)
        # Swept low but closed above the low
        swept_low = (df['low'] < roll_low) & (df['close'] > roll_low)

        df['Sweep_High_V4'] = np.where(swept_high, df['high'] - roll_high, 0.0)
        df['Sweep_Low_V4'] = np.where(swept_low, roll_low - df['low'], 0.0)
        return df

    @staticmethod
    def calculate_displacement(df: pd.DataFrame, atr_col: str = 'ATRr_14') -> pd.DataFrame:
        """
        Institutional displacement detection.
        Candle body must be > 60% of the current ATR.
        Returns +1 (Bull), -1 (Bear), 0 (Noise).
        """
        body = abs(df['close'] - df['open'])
        df['Displacement'] = np.where(
            body > (df[atr_col] * 0.6),
            np.sign(df['close'] - df['open']),
            0.0
        )
        return df
        
    @staticmethod
    def calculate_or_distance(df: pd.DataFrame, atr_col: str = 'ATRr_14') -> pd.DataFrame:
        """
        Calculates distance from the Opening Range (09:15-09:29) highs and lows.
        Normalized by ATR.
        """
        df['Date_Only'] = df.index.date
        or_mask = (df.index.hour == 9) & (df.index.minute >= 15) & (df.index.minute < 30)
        or_data = df[or_mask]
        
        # Map the daily OR high/low to every row
        df['OR_High'] = df['Date_Only'].map(or_data.groupby(or_data.index.date)['high'].max())
        df['OR_Low'] = df['Date_Only'].map(or_data.groupby(or_data.index.date)['low'].min())
        
        df['Dist_to_OR_High'] = (df['close'] - df['OR_High']) / df[atr_col]
        df['Dist_to_OR_Low'] = (df['close'] - df['OR_Low']) / df[atr_col]
        return df