#!/bin/bash

# Executor Service startup script
cd "$(dirname "$0")"

echo "Starting Executor Service..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8004 --host 0.0.0.0
