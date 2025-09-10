#!/bin/bash

# Orchestrator Service startup script
cd "$(dirname "$0")"

echo "Starting Orchestrator Service..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8002 --host 0.0.0.0
