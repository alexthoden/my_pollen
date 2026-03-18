import json
import pandas as pd
from datetime import datetime
from src.utils import read_json

def load_pollen():
    """Load pollen data from JSON file."""
    data = read_json("data/my_pollen.json")
    return data

def load_symptoms():
    """Load symptoms data from JSON file."""
    data = read_json("data/symptoms.json")
    return data

def format_pollen_date(date_dict):
    """Convert date dict from API to string format."""
    if isinstance(date_dict, dict):
        return f"{date_dict['year']}-{date_dict['month']:02d}-{date_dict['day']:02d}"
    return str(date_dict)

def build_dataset():
    """
    Build training dataset from pollen and symptom data.
    Merges pollen levels with reported symptoms by date.
    
    Returns:
        True if dataset was built successfully, False otherwise
    """
    pollen_data = load_pollen()
    symptoms_data = load_symptoms()
    
    if not pollen_data or not symptoms_data:
        print("Insufficient data to build dataset (need both pollen AND symptom data)")
        return False
    
    try:
        # Flatten pollen JSON into rows
        pollen_rows = []
        for entry in pollen_data:
            try:
                daily_info = entry.get("dailyInfo", [])
                if not daily_info:
                    continue
                
                date_dict = daily_info[0].get("date", {})
                date_str = format_pollen_date(date_dict)
                
                # Extract pollen types for this day
                row = {"date": date_str}
                for ptype in daily_info[0].get("pollenTypeInfo", []):
                    display_name = ptype.get("displayName", "Unknown")
                    if "indexInfo" in ptype:
                        value = ptype["indexInfo"].get("value", 0)
                        row[display_name] = value
                
                if len(row) > 1:  # Only add if we have pollen data
                    pollen_rows.append(row)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error processing pollen entry: {e}")
                continue
        
        if not pollen_rows:
            print("No valid pollen data to process")
            return False
        
        # Create DataFrame and aggregate by date (take max values)
        df_pollen = pd.DataFrame(pollen_rows)
        df_pollen["date"] = pd.to_datetime(df_pollen["date"])
        
        # Fill NaN with 0 and group by date
        pollen_cols = [col for col in df_pollen.columns if col != "date"]
        for col in pollen_cols:
            df_pollen[col] = pd.to_numeric(df_pollen[col], errors="coerce").fillna(0)
        
        df_pollen = df_pollen.groupby("date")[pollen_cols].max().reset_index()
        df_pollen["date"] = df_pollen["date"].dt.strftime("%Y-%m-%d")
        
        # Process symptoms data
        symptom_rows = []
        for entry in symptoms_data:
            row = {
                "date": entry.get("date", ""),
                "severity": entry.get("severity", 0),
                "notes": entry.get("notes", "")
            }
            symptom_rows.append(row)
        
        if not symptom_rows:
            print("No symptom data to process")
            return False
        
        df_symptoms = pd.DataFrame(symptom_rows)
        
        # Group symptoms by date (calculate average severity)
        df_symptoms_daily = df_symptoms.groupby("date").agg({
            "severity": "mean",
            "notes": lambda x: "; ".join(x)
        }).reset_index()
        
        # Merge pollen and symptoms on date
        df = df_pollen.merge(df_symptoms_daily, on="date", how="inner")
        
        if len(df) == 0:
            print("No matching dates between pollen and symptom data")
            return False
        
        # Save dataset
        df.to_csv("data/dataset.csv", index=False)
        print(f"Dataset built successfully: {len(df)} records")
        return True
        
    except Exception as e:
        print(f"Error building dataset: {e}")
        return False

if __name__ == "__main__":
    build_dataset()