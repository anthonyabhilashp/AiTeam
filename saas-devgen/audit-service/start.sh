#!/bin/bash

# Audit Service startup script
cd "$(dirname "$0")"

echo "Starting Audit Service..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8006 --host 0.0.0.0
