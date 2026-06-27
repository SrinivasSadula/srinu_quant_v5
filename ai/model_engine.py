# ai/model_engine.py
import logging
import pickle
import threading
import pandas as pd
import numpy as np
from config.settings import settings

class AIEngine:
    """
    Dedicated Machine Learning Inference Engine.
    Handles model loading, feature validation, and thread-safe predictions.
    """
    def __init__(self):
        self.model = None
        self.expected_features = []
        self._lock = threading.RLock()
        self.is_loaded = False
        self._load_brain()

    def _load_brain(self):
        try:
            logging.info(f"🧠 [AI ENGINE] Loading neural weights from {settings.ai.MODEL_PATH}...")
            with open(settings.ai.MODEL_PATH, 'rb') as f:
                data = pickle.load(f)
                
            self.model = data['model']
            self.expected_features = data['feature_cols']
            self.is_loaded = True
            logging.info(f"✅ [AI ENGINE] V6 Brain online. Expecting {len(self.expected_features)} features.")
        except Exception as e:
            logging.error(f"❌ [AI ENGINE] CRITICAL FAULT - Could not load model: {e}")
            self.is_loaded = False

    def predict(self, df_features: pd.DataFrame) -> dict:
        """
        Takes the raw features from the ICT Engine, cleans them to match 
        the exact training state, and returns probabilities.
        """
        with self._lock:
            if not self.is_loaded or self.model is None:
                return {"buy_prob": 0.0, "sell_prob": 0.0}

            try:
                # 1. Strict Feature Validation (Prevents Training-Serving Skew)
                missing_cols = [col for col in self.expected_features if col not in df_features.columns]
                if missing_cols:
                    logging.error(f"⚠️ [AI ENGINE] Missing features: {missing_cols}")
                    return {"buy_prob": 0.0, "sell_prob": 0.0}

                # 2. Extract exact columns in exact order
                X = df_features[self.expected_features].copy()

                # 3. Handle live market NaNs natively
                X.replace([np.inf, -np.inf], np.nan, inplace=True)
                X.fillna(0.0, inplace=True)

                # 4. Inference
                probs = self.model.predict_proba(X.iloc[-1:]) # Predict on latest bar
                
                # Our V6 model returns Binary Probabilities: [Buy Prob, Sell Prob]
                return {
                    "buy_prob": float(probs[0][0]),
                    "sell_prob": float(probs[0][1])
                }
            except Exception as e:
                logging.error(f"❌ [AI ENGINE] Inference Failed: {e}")
                return {"buy_prob": 0.0, "sell_prob": 0.0}

# Global Singleton
ai_engine = AIEngine()