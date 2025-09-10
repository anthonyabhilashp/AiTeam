#!/bin/bash

# API Gateway startup script
cd "$(dirname "$0")"

echo "Starting API Gateway..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8000 --host 0.0.0.0
