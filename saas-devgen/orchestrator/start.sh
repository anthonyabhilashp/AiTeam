#!/bin/bash

# Orchestrator Service startup script
cd "$(dirname "$0")"

echo "Starting Orchestrator Service..."
# Use relative path to virtual environment
source ../../../venv/bin/activate
# Set PYTHONPATH to include shared modules and project root
export PYTHONPATH="../../../shared:../../../:$PYTHONPATH"
uvicorn main:app --reload --port 8002 --host 0.0.0.0
