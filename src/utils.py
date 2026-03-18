import json
import os
from datetime import datetime, date

def json_exists(filename):
    """Check if JSON file exists and is valid."""
    return os.path.exists(filename)

def ensure_data_dir():
    """Ensure data directory exists."""
    if not os.path.exists("data"):
        os.makedirs("data")

def read_json(filename):
    """Safely read JSON file, return empty list if not found."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def write_json(filename, data):
    """Write data to JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def append_json(filename, data):
    """Append data to JSON file."""
    existing = read_json(filename)
    existing.append(data)
    write_json(filename, existing)

def get_today_str():
    """Get today's date as string (YYYY-MM-DD)."""
    return str(date.today())

def get_timestamp_str():
    """Get current timestamp as string."""
    return datetime.now().isoformat()

def format_date_for_display(date_str):
    """Format date string for display."""
    if isinstance(date_str, dict):
        # Handle Google API date format
        date_str = f"{date_str.get('year')}-{date_str.get('month'):02d}-{date_str.get('day'):02d}"
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")

def extract_pollen_types_from_forecast(forecast_data):
    """Extract pollen type names and indices from forecast data."""
    pollen_types = {}
    try:
        for entry in forecast_data.get("dailyInfo", []):
            for ptype_info in entry.get("pollenTypeInfo", []):
                code = ptype_info.get("code")
                display_name = ptype_info.get("displayName")
                if code and display_name:
                    if "indexInfo" in ptype_info:
                        value = ptype_info["indexInfo"].get("value")
                        pollen_types[display_name] = value
            break  # Only get today's data
    except KeyError:
        pass
    return pollen_types

def calculate_allergen_profile(pollen_history, symptom_history):
    """
    Calculate correlations between pollen levels and symptoms.
    Returns dict of allergen likelihoods.
    """
    if not pollen_history or not symptom_history:
        return {}
    
    # This is a simplified version. A more robust approach would use pandas/scipy
    allergen_profile = {}
    
    # Group by month and calculate average pollen/symptoms
    monthly_avg_pollen = {}
    monthly_avg_symptoms = {}
    
    # Count co-occurrences
    for pollen_entry in pollen_history:
        pollen_date = pollen_entry.get("date", "")
        pollen_values = pollen_entry.get("pollen_values", {})
        
        for symptom_entry in symptom_history:
            symptom_date = symptom_entry.get("date", "")
            severity = symptom_entry.get("severity", 0)
            
            if pollen_date == symptom_date:
                for pollen_type, value in pollen_values.items():
                    if pollen_type not in allergen_profile:
                        allergen_profile[pollen_type] = {
                            "count": 0,
                            "total_severity": 0,
                            "avg_severity": 0
                        }
                    allergen_profile[pollen_type]["count"] += 1
                    allergen_profile[pollen_type]["total_severity"] += severity
    
    # Calculate averages
    for pollen_type, stats in allergen_profile.items():
        if stats["count"] > 0:
            stats["avg_severity"] = stats["total_severity"] / stats["count"]
    
    return allergen_profile
