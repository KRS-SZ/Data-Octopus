#!/bin/bash
# ============================================================
# Data Octopus - Run Script (Mac/Linux)
# ============================================================

echo "Starting Data Octopus..."

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run
python main_v5.1.py
