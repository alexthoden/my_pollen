import json
import pandas as pd
from datetime import datetime
from src.utils import read_json

def load_pollen():
    """
    Load pollen history data from JSON file.
    Uses the historical pollen data (actual pollen that occurred).
    Falls back to legacy my_pollen.json if history file doesn't exist.
    """
    # Try to load from history first (new structure)
    data = read_json("data/pollen_history.json")
    
    # If history is empty or doesn't exist, fall back to legacy file
    if not data:
        print("Warning: No pollen history found. Attempting to load from legacy file...")
        # Load legacy data and convert to history format
        legacy_data = read_json("data/my_pollen.json")
        if legacy_data:
            print(f"Found {len(legacy_data)} entries in legacy file. Using for dataset building...")
        return legacy_data
    
    return data

def load_symptoms():
    """Load symptoms data from JSON file."""
    data = read_json("data/symptoms.json")
    return data

def format_pollen_date(date_dict):
    """Convert date dict from API to string format."""
    if isinstance(date_dict, dict):
        return f"{date_dict['year']}-{date_dict['month']:02d}-{date_dict['day']:02d}"
    elif isinstance(date_dict, str):
        # Already in string format (from history file)
        return date_dict
    return str(date_dict)

def extract_pollen_from_history_entry(entry):
    """
    Extract pollen data from a history entry.
    Handles both new history format and legacy format.
    """
    # New history format
    if entry.get("type") == "actual" and entry.get("dailyInfo"):
        daily_info = entry.get("dailyInfo", {})
        date_dict = daily_info.get("date", {})
        date_str = format_pollen_date(date_dict)
        
        row = {"date": date_str}
        for ptype in daily_info.get("pollenTypeInfo", []):
            display_name = ptype.get("displayName", "Unknown")
            if "indexInfo" in ptype:
                value = ptype["indexInfo"].get("value", 0)
                row[display_name] = value
        
        return row if len(row) > 1 else None
    
    # Legacy format (for backward compatibility)
    try:
        daily_info = entry.get("dailyInfo", [])
        if not daily_info:
            return None
        
        date_dict = daily_info[0].get("date", {})
        date_str = format_pollen_date(date_dict)
        
        row = {"date": date_str}
        for ptype in daily_info[0].get("pollenTypeInfo", []):
            display_name = ptype.get("displayName", "Unknown")
            if "indexInfo" in ptype:
                value = ptype["indexInfo"].get("value", 0)
                row[display_name] = value
        
        return row if len(row) > 1 else None
    except (KeyError, IndexError, TypeError):
        return None

def build_dataset():
    """
    Build training dataset from pollen and symptom data.
    Merges pollen levels with reported symptoms by date.
    Uses historical pollen data (actual pollen that occurred).
    
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
                row = extract_pollen_from_history_entry(entry)
                if row and len(row) > 1:  # Only add if we have pollen data
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
        print(f"Dataset built successfully: {len(df)} records using historical pollen data")
        return True
        
    except Exception as e:
        print(f"Error building dataset: {e}")
        return False

if __name__ == "__main__":
    build_dataset()