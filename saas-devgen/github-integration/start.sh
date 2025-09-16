#!/bin/bash

# Enterprise GitHub Integration Service Start Script
echo "Starting GitHub Integration Service..."

# Setup environment
# Use relative path to shared modules
export PYTHONPATH="../shared:$PYTHONPATH"

# Start the service
uvicorn main:app --host 0.0.0.0 --port 8007 --reload --log-level info
