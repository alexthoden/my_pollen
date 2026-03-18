import joblib
import pandas as pd
import os
from src.utils import extract_pollen_types_from_forecast

def extract_features(forecast_json):
    """
    Extract features from pollen forecast JSON.
    Returns a dictionary of pollen type values.
    """
    if not forecast_json:
        return {}
    
    features = {}
    
    try:
        # Handle both direct forecast data and wrapped response
        daily_info = forecast_json.get("dailyInfo", [])
        if not daily_info:
            return {}
        
        today_info = daily_info[0]
        
        for pollen_type_info in today_info.get("pollenTypeInfo", []):
            display_name = pollen_type_info.get("displayName", "Unknown")
            
            # Extract pollen index value (risk level: 0=low, 1=moderate, 2=high, 3=very high)
            if "indexInfo" in pollen_type_info:
                value = pollen_type_info["indexInfo"].get("value", 0)
                features[display_name] = value
            else:
                features[display_name] = 0
    
    except (KeyError, IndexError, TypeError):
        pass
    
    return features

def predict_symptoms(forecast_json, model_path="model.pkl"):
    """
    Predict symptom severity based on pollen forecast.
    
    Args:
        forecast_json: JSON data from Google Pollen API
        model_path: Path to trained model
    
    Returns:
        Predicted severity (0-3) or None if model not found
    """
    if not os.path.exists(model_path):
        return None
    
    try:
        model = joblib.load(model_path)
        
        # Convert forecast JSON → feature dictionary
        features = extract_features(forecast_json)
        
        if not features:
            return None
        
        # Create DataFrame with features
        df = pd.DataFrame([features])
        
        # Make prediction
        prediction = model.predict(df)[0]
        
        return int(prediction)
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

def get_allergen_risk_factors(forecast_json):
    """
    Identify which pollen types are highest risk.
    Returns sorted list of (pollen_type, risk_value) tuples.
    """
    features = extract_features(forecast_json)
    
    # Sort by risk value descending
    sorted_factors = sorted(features.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_factors