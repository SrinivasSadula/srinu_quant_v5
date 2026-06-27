# backtest/engine.py
import pandas as pd
import logging
import pickle
from strategy.ict_engine import ICTMathEngine
from config.settings import settings
import pandas_ta as ta
import numpy as np

logging.basicConfig(level=logging.INFO)

def run_backtest(csv_file: str, model_file: str):
    logging.info(f"📊 [BACKTEST] Loading Data: {csv_file}")
    df = pd.read_csv(csv_file, parse_dates=True, index_col='date')
    
    logging.info(f"🧠 [BACKTEST] Loading Brain: {model_file}")
    with open(model_file, 'rb') as f:
        data = pickle.load(f)
        model = data['model']
        feature_cols = data['feature_cols']

    # 1. Recreate exact live conditions
    df.ta.atr(length=14, append=True)
    df.ta.rsi(length=14, append=True)
    df.ffill(inplace=True)
    df['Date_Only'] = df.index.date
    
    # 2. Structural Math
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['TWAP_Daily'] = df.groupby('Date_Only')['Typical_Price'].transform(lambda x: x.expanding().mean())
    df['VWAP_Dist_Pct'] = ((df['close'] - df['TWAP_Daily']) / df['TWAP_Daily']) * 100
    df['Velocity_3'] = df['close'].diff(3) / df['ATRr_14'].replace(0, np.nan)
    
    # ... (Add remaining feature generation exactly as in strategy/nifty_v6_ai.py) ...
    # df = ICTMathEngine.calculate_fvg(df)
    # ...
    
    # Fill NAs to simulate production
    df.fillna(0.0, inplace=True)
    
    logging.info("⚙️ [BACKTEST] Running XGBoost Vectorized Inference...")
    X = df[feature_cols]
    probs = model.predict_proba(X)
    
    df['Buy_Prob'] = probs[:, 0]
    df['Sell_Prob'] = probs[:, 1]
    
    # 3. Simulate Asymmetric Execution
    buys = df[df['Buy_Prob'] >= settings.ai.BUY_THRESHOLD]
    sells = df[df['Sell_Prob'] >= settings.ai.SELL_THRESHOLD]
    
    logging.info(f"✅ [BACKTEST RESULTS]")
    logging.info(f"Total Bars Scanned: {len(df)}")
    logging.info(f"Hypothetical BUY Signals: {len(buys)}")
    logging.info(f"Hypothetical SELL Signals: {len(sells)}")
    
if __name__ == "__main__":
    run_backtest("nifty_historical.csv", "models/nifty_ai_brain_v7.pkl")