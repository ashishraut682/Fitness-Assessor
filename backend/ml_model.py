import numpy as np
import pickle
from pathlib import Path

try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

MODEL_PATH = Path(__file__).parent / "recommendation_model.pkl"

class MLRecommendationModel:
    """
    RandomForestClassifier trained to predict personalized workout recommendations
    from (strength, flexibility, balance, posture) metric sub-scores.
    """
    def __init__(self):
        self.model = None
        self.classes = [
            "Strength Training Focus (Pushups & Squats)",
            "Flexibility & Mobility (Stretching Exercises)",
            "Core & Balance Stabilization (Single-Leg Drills)",
            "Posture Realignment (Wall Slides & Rear Delt Flyes)",
            "Advanced Athletic Conditioning Circuit"
        ]
        self._load_or_train_model()

    def _generate_synthetic_dataset(self, num_samples=500):
        """Generates realistic synthetic fitness assessment data."""
        np.random.seed(42)
        X = []
        y = []

        for _ in range(num_samples):
            strength = np.random.uniform(30, 100)
            flexibility = np.random.uniform(30, 100)
            balance = np.random.uniform(30, 100)
            posture = np.random.uniform(30, 100)

            X.append([strength, flexibility, balance, posture])

            # Labeling rule for training data ground truth
            min_val = min(strength, flexibility, balance, posture)
            if min_val == strength and strength < 65:
                label = "Strength Training Focus (Pushups & Squats)"
            elif min_val == flexibility and flexibility < 65:
                label = "Flexibility & Mobility (Stretching Exercises)"
            elif min_val == balance and balance < 65:
                label = "Core & Balance Stabilization (Single-Leg Drills)"
            elif min_val == posture and posture < 65:
                label = "Posture Realignment (Wall Slides & Rear Delt Flyes)"
            else:
                label = "Advanced Athletic Conditioning Circuit"

            y.append(label)

        return np.array(X), np.array(y)

    def train(self):
        """Trains the RandomForestClassifier and saves model artifact."""
        if not SKLEARN_AVAILABLE:
            print("[ML Model] scikit-learn not available. Skipping model training.")
            return False

        print("[ML Model] Generating dataset and training RandomForestClassifier...")
        X, y = self._generate_synthetic_dataset()
        self.model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        self.model.fit(X, y)

        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        print(f"[ML Model] Model successfully saved to {MODEL_PATH}")
        return True

    def _load_or_train_model(self):
        if MODEL_PATH.exists() and SKLEARN_AVAILABLE:
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                print("[ML Model] Successfully loaded pre-trained RandomForest model.")
            except Exception as e:
                print(f"[ML Model] Error loading model ({e}). Retraining...")
                self.train()
        else:
            self.train()

    def predict(self, strength, flexibility, balance, posture):
        """Predicts top recommendation given sub-scores."""
        if self.model is not None and SKLEARN_AVAILABLE:
            sample = np.array([[strength, flexibility, balance, posture]])
            pred = self.model.predict(sample)[0]
            probs = self.model.predict_proba(sample)[0]
            confidence = round(float(np.max(probs) * 100), 1)
            return pred, confidence
        else:
            # Fallback prediction if ML is loading
            return "Strength Training Focus (Pushups & Squats)", 85.0

if __name__ == "__main__":
    ml = MLRecommendationModel()
    rec, conf = ml.predict(40, 70, 80, 90)
    print(f"[ML Model Test] Prediction: {rec} (Confidence: {conf}%)")
