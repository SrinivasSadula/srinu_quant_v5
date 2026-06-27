# config/settings.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 🚨 This line ensures your .env file is actually read into memory!
load_dotenv()

@dataclass
class BrokerConfig:
    KITE_API_KEY: str = os.getenv("KITE_API_KEY", "your_kite_api_key")
    KITE_API_SECRET: str = os.getenv("KITE_API_SECRET", "your_kite_api_secret")
    KITE_ACCESS_TOKEN: str = os.getenv("KITE_ACCESS_TOKEN", "") # Added to prevent the next error!
    GROWW_TOKEN: str = os.getenv("GROWW_TOKEN", "your_groww_token")
    ACTIVE_BROKER: str = os.getenv("ACTIVE_BROKER", "KITE")
    MODE: str = os.getenv("MODE", "PAPER") # 🚨 THE FIX: Added MODE mapping

@dataclass
class RiskConfig:
    MAX_LOTS: int = int(os.getenv("MAX_LOTS", 5))
    MAX_DAILY_LOSS_PCT: float = float(os.getenv("MAX_DAILY_LOSS_PCT", 2.0))
    RISK_REWARD_RATIO: float = float(os.getenv("RISK_REWARD_RATIO", 2.0))

@dataclass
class AIConfig:
    MODEL_PATH: str = "models/nifty_ai_brain_v6.pkl"
    BUY_THRESHOLD: float = 0.55
    SELL_THRESHOLD: float = 0.65

class Settings:
    broker = BrokerConfig()
    risk = RiskConfig()
    ai = AIConfig()
    SYMBOL = "NIFTY"
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Algo_user:KiteBotPassword2026@cluster0.s7l3e0d.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

settings = Settings()