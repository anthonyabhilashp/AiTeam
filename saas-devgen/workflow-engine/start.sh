#!/bin/bash

# Workflow Engine startup script
cd "$(dirname "$0")"

echo "Starting Enterprise Workflow Engine..."

# Set environment variables
export TEMPORAL_ADDRESS="localhost:7233"
export TEMPORAL_NAMESPACE="default"
export TEMPORAL_TASK_QUEUE="code-generation-queue"

# Activate virtual environment
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"

# Start the service
uvicorn main:app --reload --port 8008 --host 0.0.0.0
