# database/mongo.py
import logging
import threading
from pymongo import MongoClient
from config.settings import settings

class MongoManager:
    """
    Asynchronous Threaded MongoDB Engine.
    Handles the 'master_state' for Risk Management and 'ml_data' for AI Training.
    """
    def __init__(self):
        try:
            self.client = MongoClient(
                settings.MONGO_URI, 
                serverSelectionTimeoutMS=3000, 
                tlsAllowInvalidCertificates=True, 
                maxPoolSize=50
            )
            self.db = self.client["quant_engine"]
            self.storage_col = self.db["mt5_system_storage"]
            logging.info("✅ [MONGO INIT] Successfully connected to MongoDB Atlas!")
        except Exception as e:
            logging.error(f"❌ [MONGO INIT ERROR] Could not connect -> {e}")
            self.client = None

    # --- 1. RISK MANAGER STATE (Legacy Logic) ---
    def fetch_master_state(self) -> dict:
        if not self.client: return {}
        try:
            doc = self.storage_col.find_one({"_id": "master_state"})
            if doc and "payload" in doc:
                return doc["payload"]
        except Exception as e:
            logging.error(f"❌ [MONGO FETCH ERROR]: {e}")
        return {}

    def _async_write_worker(self, payload: dict):
        if not self.client: return
        try:
            self.storage_col.update_one(
                {"_id": "master_state"},
                {"$set": {"payload": payload}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"❌ [MONGO WRITE FAULT]: {e}")

    def push_master_state(self, payload: dict):
        if "closed_trades" in payload and len(payload["closed_trades"]) > 20:
            payload["closed_trades"] = payload["closed_trades"][:20]
        threading.Thread(target=self._async_write_worker, args=(payload,), daemon=True).start()

    # --- 2. AI MACHINE LEARNING STATE (For V7 Retraining) ---
    def _async_ml_worker(self, ticket: str, payload: dict):
        if not self.client: return
        try:
            # Saves each trade's features independently for training later
            self.storage_col.update_one(
                {"_id": f"ml_data_{ticket}"},
                {"$set": {"payload": payload}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"❌ [MONGO ML WRITE FAULT]: {e}")

    def push_ml_record(self, ticket: str, payload: dict):
        """Dedicated thread to save AI features without slowing down execution."""
        threading.Thread(target=self._async_ml_worker, args=(ticket, payload), daemon=True).start()

db_manager = MongoManager()