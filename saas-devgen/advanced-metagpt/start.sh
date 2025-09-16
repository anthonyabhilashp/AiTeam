#!/bin/bash

# Advanced MetaGPT Service Start Script
echo "Starting Advanced MetaGPT Service..."

# Setup environment
# Use relative path to shared modules
export PYTHONPATH="../shared:$PYTHONPATH"

# Start the service
uvicorn main:app --host 0.0.0.0 --port 8009 --reload --log-level info
