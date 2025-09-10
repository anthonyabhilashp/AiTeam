#!/bin/bash

# Storage Service startup script
cd "$(dirname "$0")"

echo "Starting Storage Service..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8005 --host 0.0.0.0
