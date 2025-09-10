#!/bin/bash

# Auth Service startup script
cd "$(dirname "$0")"

echo "Starting Auth Service..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8001 --host 0.0.0.0
