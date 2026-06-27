# ai/retrainer.py
import logging
import pickle
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from database.mongo import db_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class AIRetrainer:
    """
    The Institutional Evolution Engine.
    Queries MongoDB for live-trading feedback, compiles a dataset, 
    and trains the next generation of the AI brain.
    """
    def __init__(self, new_version_name="v7"):
        self.version = new_version_name
        self.output_file = f"models/nifty_ai_brain_{self.version}.pkl"

    def fetch_training_data(self) -> pd.DataFrame:
        logging.info("📥 [RETRAINER] Fetching live trade history from MongoDB...")
        
        # In MongoDB, we saved collections with prefix 'ml_data_'
        # For this script, we query all documents in the state collection that have ML data
        cursor = db_manager.storage_col.find({"_id": {"$regex": "^ml_data_"}})
        
        raw_data = []
        for doc in cursor:
            payload = doc.get("payload", {})
            features = payload.get("features", {})
            target = payload.get("target") # 1 for Win, 0 for Loss
            
            if features and target is not None:
                features["target"] = target
                raw_data.append(features)

        df = pd.DataFrame(raw_data)
        logging.info(f"✅ [RETRAINER] Extracted {len(df)} live trading samples.")
        return df

    def train_new_brain(self):
        df = self.fetch_training_data()
        if len(df) < 100:
            logging.warning("⚠️ [RETRAINER] Not enough data to retrain (Need at least 100 trades). Aborting.")
            return

        feature_cols = [col for col in df.columns if col != "target"]
        X = df[feature_cols]
        y = df["target"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        logging.info(f"🧠 [RETRAINER] Training generation {self.version.upper()} on {len(X_train)} samples...")
        
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.01,
            subsample=0.7,
            colsample_bytree=0.7,
            gamma=1.5,
            objective='binary:logistic',
            random_state=42,
            tree_method='hist',
            eval_metric='logloss'
        )

        model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

        # Save the new brain
        with open(self.output_file, 'wb') as f:
            pickle.dump({
                'model': model,
                'feature_cols': feature_cols,
                'version': self.version
            }, f)
            
        logging.info(f"🏆 [RETRAINER] Evolution complete! Saved as {self.output_file}")
        logging.info("Update settings.py AI_MODEL_PATH and restart the system to apply.")

if __name__ == "__main__":
    retrainer = AIRetrainer(new_version_name="v7")
    retrainer.train_new_brain()