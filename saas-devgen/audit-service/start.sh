#!/bin/bash

# Audit Service startup script
cd "$(dirname "$0")"

echo "Starting Audit Service..."
# Use relative path to virtual environment
source ../../../venv/bin/activate
# Set PYTHONPATH to include shared modules and project root
export PYTHONPATH="../../../shared:../../../:$PYTHONPATH"
uvicorn main:app --reload --port 8006 --host 0.0.0.0
