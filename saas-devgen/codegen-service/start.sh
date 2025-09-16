#!/bin/bash

# Codegen Service startup script
cd "$(dirname "$0")"

echo "Starting Codegen Service..."

# Load environment variables from .env file if it exists
if [ -f "../../../.env" ]; then
    export $(grep -v '^#' ../../../.env | xargs)
fi

# Use relative path to virtual environment
source ../../../venv/bin/activate
# Set PYTHONPATH to include shared modules and project root
export PYTHONPATH="../../../shared:../../../:$PYTHONPATH"
uvicorn main:app --reload --port 8003 --host 0.0.0.0
