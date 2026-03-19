"""
Pollen Tracker - Flask Backend
Main application server with REST API endpoints for pollen tracking and symptom logging
"""

print("[START] Initializing application...")

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from datetime import date, datetime, timedelta

print("[IMPORT] Loading Flask and basic modules...")

# Load environment variables FIRST before importing src modules
load_dotenv()
print("[SETUP] Environment variables loaded from .env")

# Import src modules
from src.collect_pollen import (
    collect_daily_pollen, get_latest_forecast, get_pollen_history, 
    get_forecast, get_legacy_pollen_data, test_api_connection
)
from src.collect_symptoms import log_symptoms, get_symptoms_for_date, get_latest_symptoms
from src.build_dataset import build_dataset
from src.train_model import train_model
from src.predict import predict_symptoms, extract_features
from src.forecast_analysis import build_forecast_summary, get_critical_days, get_preparation_recommendations, format_treatment_schedule
from src.utils import read_json, write_json, ensure_data_dir, calculate_allergen_profile

print("[IMPORT] All src modules loaded successfully")

print("[SETUP] Creating Flask app...")
app = Flask(__name__)
CORS(app)


print("[SETUP] Ensuring data directories...")
ensure_data_dir()

print("[SETUP] Flask app created and configured")

# ============ API ENDPOINTS ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with API diagnostics"""
    try:
        api_key_set = os.getenv("GOOGLE_POLLEN_API_KEY") is not None
        pollen_forecast = get_latest_forecast() is not None
        
        return jsonify({
            'status': 'ok',
            'api_key_configured': api_key_set,
            'forecast_cached': pollen_forecast,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/diagnostics/test-api', methods=['GET'])
def test_api_endpoint():
    """Test Google Pollen API connection and provide diagnostics"""
    try:
        result = test_api_connection()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Diagnostic test failed: {str(e)}'
        }), 500

@app.route('/')
def index():
    """Serve dashboard HTML"""
    return render_template('index.html')

@app.route('/api/pollen/current', methods=['GET'])
def get_current_pollen():
    """Get current/latest pollen forecast"""
    try:
        days = request.args.get('days', 5, type=int)
        data = get_forecast(days=min(days, 5))
        
        if not data:
            # If no forecast data, try to fetch it
            try:
                print("No cached forecast found. Attempting to fetch...")
                api_data, collected = collect_daily_pollen(lat=38.9072, lng=-77.0369, days=5, skip_if_exists=False)
                data = get_forecast(days=min(days, 5))
            except Exception as fetch_err:
                print(f"Failed to auto-fetch pollen data: {fetch_err}")
                return jsonify({
                    'status': 'error',
                    'message': 'No pollen forecast available. Please fetch data using /api/pollen/fetch'
                }), 400
        
        return jsonify({
            'status': 'success',
            'type': 'forecast',
            'data': data
        })
    except Exception as e:
        print(f"Error in /api/pollen/current: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pollen/history', methods=['GET'])
def get_pollen_history_endpoint():
    """Get actual pollen data history for N days"""
    try:
        days = request.args.get('days', 30, type=int)
        data = get_pollen_history(days=min(days, 90))
        
        return jsonify({
            'status': 'success',
            'type': 'history',
            'data': data if isinstance(data, list) else [data]
        })
    except Exception as e:
        print(f"Error in /api/pollen/history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pollen/forecast', methods=['GET'])
def get_pollen_forecast_endpoint():
    """Get 5-day pollen forecast"""
    try:
        days = request.args.get('days', 5, type=int)
        data = get_forecast(days=min(days, 5))
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No pollen forecast available'}), 404
        
        return jsonify({
            'status': 'success',
            'type': 'forecast',
            'forecast_period_days': len(data.get('dailyInfo', [])),
            'data': data
        })
    except Exception as e:
        print(f"Error in /api/pollen/forecast: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pollen/fetch', methods=['POST'])
def fetch_pollen():
    """Manually trigger pollen data fetch"""
    try:
        lat = request.json.get('lat', 38.9072) if request.json else 38.9072
        lng = request.json.get('lng', -77.0369) if request.json else -77.0369
        days = request.json.get('days', 5) if request.json else 5
        skip_if_exists = request.json.get('skip_if_exists', True) if request.json else True
        
        data, collected = collect_daily_pollen(lat=lat, lng=lng, days=days, skip_if_exists=skip_if_exists)
        
        if collected:
            return jsonify({
                'status': 'success',
                'message': f'Pollen data fetched for {days} days',
                'data': data
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'Today\'s pollen data already exists',
                'data': data,
                'skipped': True
            })
    except Exception as e:
        print(f"Error in /api/pollen/fetch: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/forecast/summary', methods=['GET'])
def get_forecast_summary():
    """Get 5-day pollen forecast with treatment recommendations"""
    try:
        latest_forecast = get_latest_forecast()
        
        if not latest_forecast:
            # Try to auto-fetch if no data exists
            try:
                print("No cached forecast found. Attempting to fetch...")
                api_data, collected = collect_daily_pollen(lat=38.9072, lng=-77.0369, days=5, skip_if_exists=False)
                latest_forecast = get_latest_forecast()
            except Exception as fetch_err:
                print(f"Failed to auto-fetch pollen data: {fetch_err}")
                return jsonify({
                    'status': 'error',
                    'message': 'No forecast data available. Please fetch pollen data first using /api/pollen/fetch'
                }), 400
        
        forecast = build_forecast_summary(latest_forecast, days_ahead=5)
        
        return jsonify({
            'status': 'success',
            'forecast': forecast
        })
    except Exception as e:
        print(f"Error in /api/forecast/summary: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/forecast/critical-days', methods=['GET'])
def get_critical_forecast_days():
    """Get days with concerning pollen levels"""
    try:
        latest_forecast = get_latest_forecast()
        
        if not latest_forecast:
            # Try to auto-fetch if no data exists
            try:
                print("No cached forecast found. Attempting to fetch...")
                api_data, collected = collect_daily_pollen(lat=38.9072, lng=-77.0369, days=5, skip_if_exists=False)
                latest_forecast = get_latest_forecast()
            except Exception as fetch_err:
                print(f"Failed to auto-fetch pollen data: {fetch_err}")
                return jsonify({
                    'status': 'success',
                    'critical_days': [],
                    'count': 0,
                    'message': 'No forecast data available yet'
                })
        
        forecast = build_forecast_summary(latest_forecast, days_ahead=5)
        critical = get_critical_days(forecast, threshold=2)
        
        return jsonify({
            'status': 'success',
            'critical_days': critical,
            'count': len(critical)
        })
    except Exception as e:
        print(f"Error in /api/forecast/critical-days: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/forecast/preparations', methods=['GET'])
def get_forecast_preparations():
    """Get advance preparation recommendations for upcoming pollen period"""
    try:
        latest_forecast = get_latest_forecast()
        
        if not latest_forecast:
            # Try to auto-fetch if no data exists
            try:
                print("No cached forecast found. Attempting to fetch...")
                api_data, collected = collect_daily_pollen(lat=38.9072, lng=-77.0369, days=5, skip_if_exists=False)
                latest_forecast = get_latest_forecast()
            except Exception as fetch_err:
                print(f"Failed to auto-fetch pollen data: {fetch_err}")
                return jsonify({
                    'status': 'error',
                    'message': 'No forecast data available. Please fetch pollen data first using /api/pollen/fetch'
                }), 400
        
        forecast = build_forecast_summary(latest_forecast, days_ahead=5)
        preps = get_preparation_recommendations(forecast)
        schedule = format_treatment_schedule(forecast)
        
        return jsonify({
            'status': 'success',
            'preparations': preps,
            'treatment_schedule': schedule
        })
    except Exception as e:
        print(f"Error in /api/forecast/preparations: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/forecast/daily/<date_str>', methods=['GET'])
def get_daily_forecast(date_str):
    """Get detailed forecast and recommendations for a specific date"""
    try:
        latest_forecast = get_latest_forecast()
        
        if not latest_forecast:
            return jsonify({
                'status': 'error',
                'message': 'No forecast data available'
            }), 400
        
        forecast = build_forecast_summary(latest_forecast, days_ahead=5)
        
        # Find the day in forecast
        day_data = None
        for day in forecast.get('days', []):
            if day['date'] == date_str:
                day_data = day
                break
        
        if not day_data:
            return jsonify({
                'status': 'error',
                'message': f'No forecast data for {date_str}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'forecast': day_data
        })
    except Exception as e:
        print(f"Error in /api/forecast/daily: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/symptoms/log', methods=['POST'])
def log_symptom_endpoint():
    """Log a symptom report"""
    try:
        data = request.json or {}
        severity = int(data.get('severity', 0))
        period = data.get('period', 'morning')
        notes = data.get('notes', '')
        location = data.get('location', '')
        
        # Validate severity
        if not 0 <= severity <= 3:
            return jsonify({'status': 'error', 'message': 'Severity must be 0-3'}), 400
        
        result = log_symptoms(severity=severity, period=period, notes=notes, location=location)
        
        return jsonify({
            'status': 'success',
            'message': 'Symptom logged successfully',
            'data': result
        })
    except Exception as e:
        print(f"Error in /api/symptoms/log: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/symptoms/today', methods=['GET'])
def get_today_symptoms():
    """Get today's symptom reports"""
    try:
        today = str(date.today())
        data = get_symptoms_for_date(today)
        
        return jsonify({
            'status': 'success',
            'date': today,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        print(f"Error in /api/symptoms/today: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/symptoms/history', methods=['GET'])
def get_symptoms_history():
    """Get symptom history for N days"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_latest_symptoms(days=min(days, 90))
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        print(f"Error in /api/symptoms/history: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/symptoms/recent', methods=['GET'])
def get_symptoms_recent():
    """Get recent symptom data (frontend compatibility endpoint)"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_latest_symptoms(days=min(days, 90))
        
        return jsonify({
            'status': 'success',
            'symptoms': data
        })
    except Exception as e:
        print(f"Error in /api/symptoms/recent: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/overview/stats', methods=['GET'])
def get_overview():
    """Get dashboard overview statistics"""
    try:
        today = str(date.today())
        today_symptoms = get_symptoms_for_date(today)
        week_symptoms = get_latest_symptoms(days=7)
        history_data = get_pollen_history(days=1)
        
        # Calculate average severity
        avg_severity = None
        if week_symptoms:
            total = sum(s.get('severity', 0) for s in week_symptoms)
            avg_severity = total / len(week_symptoms)
        
        return jsonify({
            'status': 'success',
            'today_symptoms': len(today_symptoms),
            'average_severity': avg_severity,
            'historical_records': len(history_data) if history_data else 0,
            'forecast_available': get_latest_forecast() is not None
        })
    except Exception as e:
        print(f"Error in /api/overview/stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get dashboard overview statistics (frontend compatibility endpoint)"""
    try:
        today = str(date.today())
        today_symptoms = get_symptoms_for_date(today)
        week_symptoms = get_latest_symptoms(days=7)
        history_data = get_pollen_history(days=7)
        
        # Calculate average severity
        avg_severity = None
        if week_symptoms:
            total = sum(s.get('severity', 0) for s in week_symptoms)
            avg_severity = total / len(week_symptoms)
        
        return jsonify({
            'status': 'success',
            'recent_symptoms_count': len(today_symptoms),
            'average_severity': avg_severity,
            'pollen_records': len(history_data) if history_data else 0,
            'forecast_available': get_latest_forecast() is not None
        })
    except Exception as e:
        print(f"Error in /api/dashboard/overview: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/model/train', methods=['POST'])
def train_model_endpoint():
    """Train the ML model"""
    try:
        # Build dataset from collected data
        dataset_built = build_dataset()
        
        if not dataset_built:
            return jsonify({
                'status': 'error',
                'message': 'Insufficient data to build dataset (need at least 3 records)'
            }), 400
        
        # Train model
        model_trained = train_model()
        
        if model_trained:
            return jsonify({
                'status': 'success',
                'message': 'Model trained successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Model training failed'
            }), 500
    except Exception as e:
        print(f"Error in /api/model/train: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/model/status', methods=['GET'])
def get_model_status():
    """Check if model is trained"""
    try:
        import os
        model_exists = os.path.exists('data/model.pkl')
        
        return jsonify({
            'status': 'success',
            'trained': model_exists
        })
    except Exception as e:
        print(f"Error in /api/model/status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/predict/symptoms', methods=['POST'])
def predict_endpoint():
    """Predict symptoms based on pollen forecast"""
    try:
        data = request.json or {}
        pollen_forecast = data.get('forecast')
        
        if not pollen_forecast:
            latest = get_latest_forecast()
            pollen_forecast = latest
        
        prediction = predict_symptoms(pollen_forecast)
        
        return jsonify({
            'status': 'success',
            'prediction': prediction
        })
    except Exception as e:
        print(f"Error in /api/predict/symptoms: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/analysis/profile', methods=['GET'])
def get_allergen_profile():
    """Get personal allergen profile based on trained model"""
    try:
        pollen_history = get_pollen_history(days=90)
        symptom_history = get_latest_symptoms(days=90)
        
        if not pollen_history or not symptom_history:
            return jsonify({
                'status': 'success',
                'data': {},
                'message': 'Insufficient historical data to calculate profile. Collect more data to generate allergen profile.'
            })
        
        profile = calculate_allergen_profile(pollen_history, symptom_history)
        
        return jsonify({
            'status': 'success',
            'data': profile if profile else {}
        })
    except Exception as e:
        print(f"Error in /api/analysis/profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/allergen-profile', methods=['GET'])
def get_allergen_profile_compat():
    """Get personal allergen profile (frontend compatibility endpoint)"""
    try:
        pollen_history = get_pollen_history(days=90)
        symptom_history = get_latest_symptoms(days=90)
        
        if not pollen_history or not symptom_history:
            return jsonify({
                'status': 'success',
                'profile': {},
                'message': 'Insufficient historical data to calculate profile. Collect more data to generate allergen profile.'
            })
        
        profile = calculate_allergen_profile(pollen_history, symptom_history)
        
        return jsonify({
            'status': 'success',
            'profile': profile if profile else {}
        })
    except Exception as e:
        print(f"Error in /api/allergen-profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/export', methods=['GET'])
def export_data():
    """Export all collected data (forecast, history, and symptoms)"""
    try:
        forecast_data = read_json('data/pollen_forecast.json')
        history_data = read_json('data/pollen_history.json')
        legacy_data = read_json('data/my_pollen.json')  # For reference
        symptoms_data = read_json('data/symptoms.json')
        
        return jsonify({
            'status': 'success',
            'forecast': forecast_data,
            'history': history_data,
            'legacy': legacy_data,
            'symptoms': symptoms_data
        })
    except Exception as e:
        print(f"Error in /api/data/export: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/clear', methods=['POST'])
def clear_data():
    """Clear all collected data (requires confirmation)"""
    try:
        confirm = request.json.get('confirm', False) if request.json else False
        
        if not confirm:
            return jsonify({
                'status': 'error',
                'message': 'Confirmation required to clear data'
            }), 400
        
        write_json('data/pollen_forecast.json', {})
        write_json('data/pollen_history.json', [])
        write_json('data/my_pollen.json', [])
        write_json('data/symptoms.json', [])
        
        # Remove model
        if os.path.exists('data/model.pkl'):
            os.remove('data/model.pkl')
        
        return jsonify({
            'status': 'success',
            'message': 'All data cleared'
        })
    except Exception as e:
        print(f"Error in /api/data/clear: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    print(f"[ERROR] Internal server error: {error}")
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ============ STARTUP ============

if __name__ == '__main__':
    print("[STARTUP] All set! Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='localhost', port=5000)