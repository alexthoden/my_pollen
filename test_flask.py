#!/usr/bin/env python
"""
Minimal test version of main.py to debug the startup issue
"""

import sys
import os

print("=" * 60)
print("MINIMAL FLASK TEST")
print("=" * 60)
print()

print("Step 1: Loading environment...")
from dotenv import load_dotenv
load_dotenv()
print("✓ Environment loaded")

print("Step 2: Creating Flask app...")
from flask import Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
print("✓ Flask app created")

print("Step 3: Setting up route...")
@app.route("/")
def index():
    return "Hello from Pollen Tracker!"

print("✓ Route setup complete")

print()
print("=" * 60)
print("Starting Flask server...")
print("=" * 60)
print("📊 Dashboard available at http://localhost:5000")
print()
print("Press Ctrl+C to stop")
print("=" * 60)
print()

sys.stdout.flush()

# Start the app
try:
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
