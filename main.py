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

# Import src modules
from src.collect_pollen import collect_daily_pollen, get_latest_pollen_data, get_pollen_history
from src.collect_symptoms import log_symptoms, get_symptoms_for_date, get_latest_symptoms
from src.build_dataset import build_dataset
from src.train_model import train_model
from src.predict import predict_symptoms, extract_features
from src.forecast_analysis import build_forecast_summary, get_critical_days, get_preparation_recommendations, format_treatment_schedule
from src.utils import read_json, write_json, ensure_data_dir, calculate_allergen_profile

print("[IMPORT] All src modules loaded successfully")

# Load environment variables
load_dotenv()

print("[SETUP] Creating Flask app...")
app = Flask(__name__)
CORS(app)

print("[SETUP] Ensuring data directories...")
ensure_data_dir()

print("[SETUP] Flask app created and configured")

# ============ API ENDPOINTS ============

@app.route('/')
def index():
    """Serve dashboard HTML"""
    return render_template('index.html')

@app.route('/api/pollen/current', methods=['GET'])
def get_current_pollen():
    """Get current pollen forecast"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_pollen_history(days=min(days, 30))
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No pollen data available'}), 404
        
        return jsonify({
            'status': 'success',
            'data': data[-1] if isinstance(data, list) else data
        })
    except Exception as e:
        print(f"Error in /api/pollen/current: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/pollen/history', methods=['GET'])
def get_pollen_history_endpoint():
    """Get pollen history for N days"""
    try:
        days = request.args.get('days', 30, type=int)
        data = get_pollen_history(days=min(days, 60))
        
        return jsonify({
            'status': 'success',
            'data': data if isinstance(data, list) else [data]
        })
    except Exception as e:
        print(f"Error in /api/pollen/history: {e}")
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
        latest_data = get_latest_pollen_data()
        
        if not latest_data:
            return jsonify({
                'status': 'error',
                'message': 'No forecast data available. Fetch pollen data first.'
            }), 400
        
        forecast = build_forecast_summary(latest_data, days_ahead=5)
        
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
        latest_data = get_latest_pollen_data()
        
        if not latest_data:
            return jsonify({
                'status': 'error',
                'message': 'No forecast data available'
            }), 400
        
        forecast = build_forecast_summary(latest_data, days_ahead=5)
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
        latest_data = get_latest_pollen_data()
        
        if not latest_data:
            return jsonify({
                'status': 'error',
                'message': 'No forecast data available'
            }), 400
        
        forecast = build_forecast_summary(latest_data, days_ahead=5)
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
        latest_data = get_latest_pollen_data()
        
        if not latest_data:
            return jsonify({
                'status': 'error',
                'message': 'No forecast data available'
            }), 400
        
        forecast = build_forecast_summary(latest_data, days_ahead=5)
        
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

@app.route('/api/overview/stats', methods=['GET'])
def get_overview():
    """Get dashboard overview statistics"""
    try:
        today = str(date.today())
        today_symptoms = get_symptoms_for_date(today)
        week_symptoms = get_latest_symptoms(days=7)
        pollen_data = get_pollen_history(days=1)
        
        # Calculate average severity
        avg_severity = None
        if week_symptoms:
            total = sum(s.get('severity', 0) for s in week_symptoms)
            avg_severity = total / len(week_symptoms)
        
        return jsonify({
            'status': 'success',
            'today_symptoms': len(today_symptoms),
            'average_severity': avg_severity,
            'pollen_records': len(pollen_data) if pollen_data else 0
        })
    except Exception as e:
        print(f"Error in /api/overview/stats: {e}")
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
    """Predict symptoms based on pollen data"""
    try:
        data = request.json or {}
        pollen_forecast = data.get('forecast')
        
        if not pollen_forecast:
            latest = get_latest_pollen_data()
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
        profile = calculate_allergen_profile()
        
        if not profile:
            return jsonify({
                'status': 'error',
                'message': 'Model not trained yet. Collect more data first.'
            }), 400
        
        return jsonify({
            'status': 'success',
            'data': profile
        })
    except Exception as e:
        print(f"Error in /api/analysis/profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/export', methods=['GET'])
def export_data():
    """Export all collected data"""
    try:
        pollen_data = read_json('data/my_pollen.json')
        symptoms_data = read_json('data/symptoms.json')
        
        return jsonify({
            'status': 'success',
            'pollen': pollen_data,
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