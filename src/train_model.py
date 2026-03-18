import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

def train_model():
    """
    Train a Random Forest model to predict symptom severity based on pollen levels.
    """
    if not os.path.exists("data/dataset.csv"):
        print("Dataset not found. Run build_dataset.py first.")
        return False
    
    try:
        df = pd.read_csv("data/dataset.csv")
        
        if len(df) < 3 or df.empty:
            print(f"Insufficient training data: {len(df)} records (need at least 3)")
            return False
        
        print(f"Training model with {len(df)} records...")
        
        # Identify feature columns (pollen types)
        exclude_cols = ["date", "severity", "notes"]
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not feature_cols:
            print("No pollen features found in dataset")
            return False
        
        # Prepare features and target
        X = df[feature_cols].fillna(0)
        y = df["severity"].fillna(0).astype(int)
        
        print(f"Features: {feature_cols}")
        print(f"Target distribution:\n{y.value_counts().sort_index()}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None
        )
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        print(f"Training accuracy: {train_score:.3f}")
        print(f"Testing accuracy: {test_score:.3f}")
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        print(f"\nTop allergens:")
        for idx, row in importance.head(5).iterrows():
            print(f"  {row['feature']}: {row['importance']:.3f}")
        
        # Save model
        joblib.dump(model, "model.pkl")
        print(f"\nModel saved to model.pkl")
        return True
        
    except Exception as e:
        print(f"Error training model: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_model():
    """Load trained model."""
    if not os.path.exists("model.pkl"):
        return None
    return joblib.load("model.pkl")

if __name__ == "__main__":
    train_model()