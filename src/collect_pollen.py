import requests
import os
import json
from datetime import datetime, date
from dotenv import load_dotenv
from src.utils import read_json, write_json, append_json

load_dotenv()
API_KEY = os.getenv("GOOGLE_POLLEN_API_KEY")

def get_pollen_forecast(lat, lng, days=1):
    """
    Fetch pollen forecast from Google Pollen API.
    
    Args:
        lat: Latitude
        lng: Longitude
        days: Number of days to forecast (1-5)
    
    Returns:
        JSON response from Google Pollen API
    """
    if not API_KEY:
        raise ValueError("GOOGLE_POLLEN_API_KEY not set in .env file")
    
    url = "https://pollen.googleapis.com/v1/forecast:lookup"
    params = {
        "key": API_KEY,
        "location.latitude": lat,
        "location.longitude": lng,
        "days": min(days, 5)  # API max is 5 days
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pollen data: {e}")
        raise

def has_pollen_data_for_today():
    """
    Check if pollen data for today already exists in my_pollen.json.
    
    Returns:
        bool: True if today's data exists, False otherwise
    """
    try:
        data = read_json("data/my_pollen.json")
        today = date.today()
        
        for entry in reversed(data):  # Check most recent entries first
            if entry.get("dailyInfo"):
                # Check the first daily entry's date
                daily_entry = entry["dailyInfo"][0]
                if daily_entry.get("date"):
                    date_info = daily_entry["date"]
                    entry_date = date(date_info["year"], date_info["month"], date_info["day"])
                    if entry_date == today:
                        return True
            
            # Stop checking if we've gone past today (entries are in chronological order)
            if entry.get("timestamp"):
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time.date() < today:
                    break
        
        return False
    except Exception as e:
        print(f"Error checking for existing pollen data: {e}")
        return False

def collect_daily_pollen(lat=38.9072, lng=-77.0369, days=5, skip_if_exists=True):
    """
    Fetch pollen data and store it locally.
    
    Args:
        lat: Latitude (default: Washington DC)
        lng: Longitude (default: Washington DC)
        days: Number of days to fetch (1-5)
        skip_if_exists: If True, skip collection if data already exists for today (default: True)
    
    Returns:
        Tuple of (data, collected) where collected is True if new data was fetched
    """
    # Check if today's data already exists
    if skip_if_exists and has_pollen_data_for_today():
        print("Pollen data for today already exists. Skipping collection.")
        latest = get_latest_pollen_data()
        return (latest, False)
    
    data = get_pollen_forecast(lat, lng, days=days)
    
    # Add timestamp
    data["timestamp"] = datetime.now().isoformat()
    
    # Store the forecast
    append_json("data/my_pollen.json", data)
    
    print(f"Successfully collected pollen data for {days} days")
    return (data, True)

def get_latest_pollen_data():
    """Get the most recent pollen forecast."""
    data = read_json("data/my_pollen.json")
    return data[-1] if data else None

def get_pollen_history(days=30):
    """Get pollen history for the last N days."""
    data = read_json("data/my_pollen.json")
    # Return entries from the last N days (simplified)
    return data[-days:] if len(data) > days else data