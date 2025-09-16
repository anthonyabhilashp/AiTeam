#!/bin/bash

# Enterprise Testing Framework Service Start Script
echo "Starting Testing Framework Service..."

# Setup environment
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam/saas-devgen/shared:$PYTHONPATH"

# Start the service
uvicorn main:app --host 0.0.0.0 --port 8008 --reload --log-level info
