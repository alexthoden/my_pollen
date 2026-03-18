import json
from datetime import date
from src.utils import json_exists, read_json, write_json, get_today_str

def log_symptoms(severity, period="morning", notes="", location=""):
    """
    Log symptoms for a specific time of day.
    
    Args:
        severity: int 0-3 scale (0=none, 1=mild, 2=moderate, 3=severe)
        period: str "morning" or "afternoon"
        notes: str optional notes about symptoms
        location: str optional location (can be used to query pollen data)
    """
    entry = {
        "date": get_today_str(),
        "period": period,
        "severity": severity,
        "notes": notes,
        "location": location if location else None
    }
    filename = "data/symptoms.json"
    
    existing = read_json(filename)
    existing.append(entry)
    write_json(filename, existing)
    
    return entry

def get_symptoms_for_date(date_str):
    """Get all symptom entries for a specific date."""
    symptoms = read_json("data/symptoms.json")
    return [s for s in symptoms if s.get("date") == date_str]

def get_latest_symptoms(days=7):
    """Get symptom entries from the last N days."""
    symptoms = read_json("data/symptoms.json")
    # Return last N entries
    return symptoms[-days:] if len(symptoms) > days else symptoms

def calculate_daily_severity(date_str):
    """Calculate average severity for a day."""
    daily_symptoms = get_symptoms_for_date(date_str)
    if not daily_symptoms:
        return None
    
    total_severity = sum(s.get("severity", 0) for s in daily_symptoms)
    return total_severity / len(daily_symptoms)