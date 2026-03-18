#!/usr/bin/env python
"""
Pollen Tracker - Main Application Entry Point
Provides Flask API backend and web-based dashboard
"""

import sys
import os
from datetime import datetime, timedelta

print("[START] Initializing Pollen Tracker...", flush=True)

print("[IMPORT] Loading Flask...", flush=True)
from flask import Flask, render_template, request, jsonify

print("[IMPORT] Loading Flask-CORS...", flush=True)
from flask_cors import CORS

print("[IMPORT] Loading dotenv...", flush=True)
from dotenv import load_dotenv
load_dotenv()

print("[IMPORT] Loading json...", flush=True)
import json

print("[IMPORT] Loading src.utils...", flush=True)
from src.utils import (
    ensure_data_dir, read_json, write_json, get_today_str,
    calculate_allergen_profile
)

print("[IMPORT] Loading src.collect_pollen...", flush=True)
from src.collect_pollen import get_pollen_forecast, collect_daily_pollen

print("[IMPORT] Loading src.collect_symptoms...", flush=True)
from src.collect_symptoms import log_symptoms, get_symptoms_for_date, get_latest_symptoms

print("[IMPORT] Loading src.predict...", flush=True)
from src.predict import predict_symptoms, get_allergen_risk_factors, extract_features

print("[IMPORT] Loading src.build_dataset...", flush=True)
from src.build_dataset import build_dataset

print("[IMPORT] Loading src.train_model...", flush=True)
from src.train_model import train_model

print("[SETUP] Creating Flask app...", flush=True)
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Configuration
POLLEN_LAT = os.getenv("POLLEN_LAT", 38.9072)  # Default: Washington DC
POLLEN_LNG = os.getenv("POLLEN_LNG", -77.0369)

# Ensure data directory exists
ensure_data_dir()

# ==================== API ENDPOINTS ====================

@app.route("/")
def index():
    """Serve main dashboard page."""
    return render_template("index.html")

@app.route("/api/pollen/current", methods=["GET"])
def get_current_pollen():
    """Get current pollen forecast."""
    try:
        days = request.args.get("days", 1, type=int)
        pollen_data = get_pollen_forecast(float(POLLEN_LAT), float(POLLEN_LNG), days=days)
        return jsonify(pollen_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pollen/fetch", methods=["POST"])
def fetch_pollen():
    """Fetch and store pollen data."""
    try:
        collect_daily_pollen()
        return jsonify({"status": "success", "message": "Pollen data collected"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/symptoms/log", methods=["POST"])
def log_symptom_report():
    """Log symptom report."""
    try:
        data = request.json
        severity = data.get("severity")
        period = data.get("period", "morning")
        notes = data.get("notes", "")
        
        if severity is None:
            return jsonify({"error": "Severity required"}), 400
        
        result = log_symptoms(severity, period=period, notes=notes)
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/symptoms/today", methods=["GET"])
def get_today_symptoms():
    """Get today's symptom reports."""
    try:
        today = get_today_str()
        symptoms = get_symptoms_for_date(today)
        return jsonify({
            "date": today,
            "symptoms": symptoms,
            "count": len(symptoms)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/symptoms/recent", methods=["GET"])
def get_recent_symptoms():
    """Get recent symptom reports."""
    try:
        days = request.args.get("days", 7, type=int)
        symptoms = get_latest_symptoms(days=days)
        return jsonify({
            "days": days,
            "symptoms": symptoms,
            "count": len(symptoms)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/predict/symptoms", methods=["POST"])
def predict_symptoms_endpoint():
    """Predict symptom severity based on pollen forecast."""
    try:
        data = request.json
        forecast = data.get("forecast")
        
        if not forecast:
            return jsonify({"error": "Forecast data required"}), 400
        
        prediction = predict_symptoms(forecast)
        risk_factors = get_allergen_risk_factors(forecast)
        
        return jsonify({
            "prediction": prediction,
            "risk_factors": risk_factors
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dashboard/overview", methods=["GET"])
def dashboard_overview():
    """Get dashboard overview data."""
    try:
        today = get_today_str()
        recent_symptoms = get_latest_symptoms(days=7)
        pollen_data = read_json("data/my_pollen.json")
        
        # Calculate statistics
        avg_severity = None
        if recent_symptoms:
            severities = [s.get("severity", 0) for s in recent_symptoms]
            avg_severity = sum(severities) / len(severities)
        
        return jsonify({
            "date": today,
            "recent_symptoms_count": len(recent_symptoms),
            "average_severity": avg_severity,
            "pollen_records": len(pollen_data),
            "last_pollen_fetch": pollen_data[-1].get("regionCode") if pollen_data else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/allergen-profile", methods=["GET"])
def get_allergen_profile():
    """Get calculated allergen profile."""
    try:
        pollen_history = read_json("data/my_pollen.json")
        symptom_history = read_json("data/symptoms.json")
        
        profile = calculate_allergen_profile(pollen_history, symptom_history)
        
        return jsonify({
            "profile": profile,
            "total_samples": len(symptom_history)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/model/train", methods=["POST"])
def train_allergen_model():
    """Train the allergen prediction model."""
    try:
        # First build dataset from existing data
        built = build_dataset()
        if not built:
            return jsonify({
                "error": "Insufficient data. Collect more pollen and symptom data first.",
                "status": "error"
            }), 400
        
        # Then train model
        trained = train_model()
        if not trained:
            return jsonify({
                "error": "Failed to train model. Check data format.",
                "status": "error"
            }), 400
        
        return jsonify({"status": "success", "message": "Model trained successfully"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/api/model/status", methods=["GET"])
def model_status():
    """Check if model exists and is ready."""
    model_exists = os.path.exists("model.pkl")
    dataset_exists = os.path.exists("data/dataset.csv")
    
    return jsonify({
        "model_exists": model_exists,
        "dataset_exists": dataset_exists,
        "ready": model_exists and dataset_exists
    })

@app.route("/api/data/export", methods=["GET"])
def export_data():
    """Export all collected data."""
    try:
        export_data_dict = {
            "exported_at": datetime.now().isoformat(),
            "pollen": read_json("data/my_pollen.json"),
            "symptoms": read_json("data/symptoms.json")
        }
        return jsonify(export_data_dict)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server error"}), 500

# ==================== INITIALIZATION ====================

def init_app():
    """Initialize the application."""
    ensure_data_dir()
    # Create empty data files if they don't exist
    if not os.path.exists("data/my_pollen.json"):
        write_json("data/my_pollen.json", [])
    if not os.path.exists("data/symptoms.json"):
        write_json("data/symptoms.json", [])

if __name__ == "__main__":
    print("[SETUP] Initializing app data...", flush=True)
    init_app()
    
    print("[STARTUP] All set! Starting Flask server...", flush=True)
    print()
    print("=" * 60)
    print("Starting Pollen Tracker Server...")
    print("=" * 60)
    print("📊 Dashboard available at http://localhost:5000")
    print("📈 Use the web interface to track your symptoms and pollen")
    print("")
    print("Optional: Use --gui flag to also launch symptom logger GUI")
    print("  python main.py --gui")
    print("=" * 60)
    print()
    sys.stdout.flush()
    
    try:
        app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()