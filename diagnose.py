#!/usr/bin/env python
"""
Diagnostic script to test if the app can start
"""

import sys
import traceback

print("=" * 60)
print("POLLEN TRACKER - DIAGNOSTIC TEST")
print("=" * 60)
print()

# Test 1: Check Python version
print("✓ Python version:", sys.version)
print()

# Test 2: Check imports
print("Testing imports...")
try:
    print("  - flask...", end=" ")
    from flask import Flask
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - flask_cors...", end=" ")
    from flask_cors import CORS
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    sys.exit(1)

try:
    print("  - dotenv...", end=" ")
    from dotenv import load_dotenv
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    sys.exit(1)

try:
    print("  - src.utils...", end=" ")
    from src.utils import ensure_data_dir
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - src.collect_pollen...", end=" ")
    from src.collect_pollen import get_pollen_forecast
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - src.collect_symptoms...", end=" ")
    from src.collect_symptoms import log_symptoms
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - src.build_dataset...", end=" ")
    from src.build_dataset import build_dataset
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - src.train_model...", end=" ")
    from src.train_model import train_model
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    print("  - src.predict...", end=" ")
    from src.predict import predict_symptoms
    print("✓")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

print()
print("✓ All imports successful!")
print()

# Test 3: Check Flask app creation
print("Testing Flask app creation...")
try:
    from flask import Flask
    app = Flask(__name__, template_folder="templates", static_folder="static")
    print("✓ Flask app created successfully")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check data directory
print()
print("Testing data directory...")
try:
    from src.utils import ensure_data_dir
    ensure_data_dir()
    print("✓ Data directory OK")
except Exception as e:
    print("✗ FAILED:", e)
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✓ ALL TESTS PASSED - App should start successfully!")
print("=" * 60)
print()
print("Now run: python main.py")
