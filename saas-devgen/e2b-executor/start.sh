#!/bin/bash

# E2B Executor startup script
cd "$(dirname "$0")"

echo "Starting Enterprise E2B Executor Service..."

# Set E2B environment variables
export E2B_API_KEY="${E2B_API_KEY:-demo_key}"
export E2B_DOMAIN="${E2B_DOMAIN:-e2b.dev}"

# Docker environment
export DOCKER_HOST="${DOCKER_HOST:-unix:///var/run/docker.sock}"

# Activate virtual environment
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"

# Start the service
uvicorn main:app --reload --port 8009 --host 0.0.0.0
