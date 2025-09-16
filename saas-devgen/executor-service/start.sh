#!/bin/bash

# Executor Service startup script
cd "$(dirname "$0")"

echo "Starting Executor Service..."
# Use relative path to virtual environment
source ../../../venv/bin/activate
# Set PYTHONPATH to include shared modules and project root
export PYTHONPATH="../../../shared:../../../:$PYTHONPATH"
uvicorn main:app --reload --port 8004 --host 0.0.0.0
