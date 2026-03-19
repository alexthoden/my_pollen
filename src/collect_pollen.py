import requests
import os
import json
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from src.utils import read_json, write_json, append_json

load_dotenv()
API_KEY = os.getenv("GOOGLE_POLLEN_API_KEY")

# File paths
FORECAST_FILE = "data/pollen_forecast.json"
HISTORY_FILE = "data/pollen_history.json"
LEGACY_FILE = "data/my_pollen.json"  # Keep for backward compatibility

def test_api_connection():
    """
    Test the Google Pollen API connection with diagnostics.
    Returns detailed error information for troubleshooting.
    
    Returns:
        dict: Status and diagnostic information
    """
    if not API_KEY:
        return {
            'status': 'error',
            'message': 'GOOGLE_POLLEN_API_KEY not set in environment',
            'api_key_set': False
        }
    
    url = "https://pollen.googleapis.com/v1/forecast:lookup"
    lat = 38.9072
    lng = -77.0369
    
    # Only API key in query parameters
    params = {
        "key": API_KEY,
        "location.latitude": lat,
        "location.longitude": lng,
        "days": 5
    }
    
    try:
        print(f"Testing API connection to: {url}")
        print(f"Request method: GET")
        print(f"Parameters: lat={lat}, lng={lng}")
        print(f"Payload: {json.dumps(params)}")
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return {
                'status': 'success',
                'message': 'API connection successful',
                'http_status': 200,
                'data': response.json()
            }
        else:
            return {
                'status': 'error',
                'message': f'API returned HTTP {response.status_code}',
                'http_status': response.status_code,
                'response_text': response.text[:500],
                'url': response.url if hasattr(response, 'url') else url
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Connection error: {str(e)}',
            'error_type': type(e).__name__,
            'url': url
        }

def get_pollen_forecast_api(lat, lng, days=5):
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
    
    # Only API key in query parameters
    params = {
        "key": API_KEY,
        "location.latitude": lat,
        "location.longitude": lng,
        "days": 5
    }
    
    try:
        print(f"Fetching pollen forecast from: {url}")
        print(f"Parameters: lat={lat}, lng={lng}, days={days}")
        
        # POST request with key in query params, location/days in JSON body
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching pollen data from API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"API Error Details: {error_detail}")
            except:
                print(f"API Response: {e.response.text}")
        raise

def extract_date_from_forecast_entry(daily_info_entry):
    """Extract date from a dailyInfo entry."""
    if not daily_info_entry.get("date"):
        return None
    date_info = daily_info_entry["date"]
    return date(date_info["year"], date_info["month"], date_info["day"])

def archive_forecast_to_history(forecast_json):
    """
    Archive forecast data to history.
    Moves the first day (today/oldest) from forecast to historical data.
    Should be called daily to keep historical record.
    
    Args:
        forecast_json: Forecast data from API
    """
    try:
        if not forecast_json.get("dailyInfo") or len(forecast_json["dailyInfo"]) == 0:
            return
        
        # Get today's date
        today = date.today()
        first_daily_info = forecast_json["dailyInfo"][0]
        entry_date = extract_date_from_forecast_entry(first_daily_info)
        
        # Only archive if this is past data (yesterday or earlier)
        if entry_date and entry_date < today:
            historical_entry = {
                "date": entry_date.isoformat(),
                "dailyInfo": first_daily_info,
                "archived_timestamp": datetime.now().isoformat(),
                "type": "actual"  # Mark as actual pollen data
            }
            append_json(HISTORY_FILE, historical_entry)
            print(f"Archived pollen data for {entry_date} to history")
    except Exception as e:
        print(f"Error archiving forecast to history: {e}")

def save_forecast(forecast_json):
    """
    Save forecast to rolling 5-day forecast file.
    Replaces the entire forecast (rolling window).
    
    Args:
        forecast_json: Forecast data from API
    """
    try:
        # Add fetch timestamp
        forecast_json["fetched_timestamp"] = datetime.now().isoformat()
        
        # Convert to list format with metadata
        forecast_data = {
            "forecast_date": date.today().isoformat(),
            "forecast": forecast_json,
            "fetched_timestamp": datetime.now().isoformat(),
            "days": len(forecast_json.get("dailyInfo", []))
        }
        
        write_json(FORECAST_FILE, forecast_data)
        print(f"Saved 5-day forecast to {FORECAST_FILE}")
    except Exception as e:
        print(f"Error saving forecast: {e}")

def has_forecast_for_today():
    """
    Check if forecast for today already exists and has valid data.
    
    Returns:
        bool: True if today's forecast exists with data, False otherwise
    """
    try:
        forecast_data = read_json(FORECAST_FILE)
        if not forecast_data:
            return False
        
        # Check if the forecast was fetched today AND has actual data
        forecast_date_str = forecast_data.get("forecast_date")
        if forecast_date_str:
            forecast_date = datetime.fromisoformat(forecast_date_str).date()
            # Also check that forecast has valid daily info
            forecast = forecast_data.get("forecast", {})
            daily_info = forecast.get("dailyInfo", [])
            return forecast_date == date.today() and len(daily_info) > 0
        
        return False
    except Exception as e:
        print(f"Error checking for today's forecast: {e}")
        return False

def collect_daily_pollen(lat=38.9072, lng=-77.0369, days=5, skip_if_exists=True):
    """
    Fetch pollen data and store it locally (separated into forecast/history).
    
    Args:
        lat: Latitude (default: Washington DC)
        lng: Longitude (default: Washington DC)
        days: Number of days to fetch (1-5)
        skip_if_exists: If True, skip collection if forecast already exists for today (default: True)
    
    Returns:
        Tuple of (data, collected) where collected is True if new data was fetched
    """
    # Check if today's forecast already exists
    if skip_if_exists and has_forecast_for_today():
        print("Forecast for today already exists. Skipping collection.")
        latest = get_latest_forecast()
        return (latest, False)
    
    # Fetch from API
    forecast_data = get_pollen_forecast_api(lat, lng, days=days)
    
    # Archive any past data to history
    archive_forecast_to_history(forecast_data)
    
    # Save the new forecast
    save_forecast(forecast_data)
    
    # Also append to legacy file for backward compatibility
    forecast_data["timestamp"] = datetime.now().isoformat()
    append_json(LEGACY_FILE, forecast_data)
    
    print(f"Successfully collected pollen forecast for {days} days")
    return (forecast_data, True)

def get_latest_forecast():
    """Get the most recent 5-day forecast."""
    forecast_data = read_json(FORECAST_FILE)
    if forecast_data and forecast_data.get("forecast"):
        return forecast_data["forecast"]
    return None

def get_forecast(days=5):
    """
    Get the current rolling 5-day forecast.
    
    Args:
        days: Number of days to return (capped at actual forecast length)
    
    Returns:
        Forecast data
    """
    forecast_data = read_json(FORECAST_FILE)
    if not forecast_data:
        return None
    
    forecast = forecast_data.get("forecast", {})
    daily_info = forecast.get("dailyInfo", [])
    
    # Return requested number of days (or all if less than requested)
    if daily_info:
        return {
            **forecast,
            "dailyInfo": daily_info[:min(days, len(daily_info))]
        }
    
    return forecast

def get_pollen_history(days=30):
    """
    Get pollen history for the last N days (actual pollen data that occurred).
    
    Args:
        days: Number of days to retrieve
    
    Returns:
        List of historical pollen entries
    """
    history = read_json(HISTORY_FILE)
    
    if not history:
        return []
    
    # Filter to last N days
    cutoff_date = date.today() - timedelta(days=days)
    recent_history = []
    
    for entry in reversed(history):  # Process in reverse (newest first)
        try:
            entry_date = datetime.fromisoformat(entry.get("date")).date()
            if entry_date >= cutoff_date:
                recent_history.insert(0, entry)  # Insert at beginning to maintain order
        except (ValueError, TypeError):
            continue
    
    return recent_history

def get_latest_pollen_data():
    """
    Get the latest pollen data (from forecast or history).
    Alias for compatibility with forecast_analysis module.
    
    Returns:
        Latest pollen forecast data
    """
    return get_latest_forecast()

def get_legacy_pollen_data():
    """
    Get all legacy pollen data from my_pollen.json.
    Used for data migration and backward compatibility.
    
    Returns:
        Legacy pollen data
    """
    return read_json(LEGACY_FILE)