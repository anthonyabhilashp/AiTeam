#!/bin/bash

# Codegen Service startup script
cd "$(dirname "$0")"

echo "Starting Codegen Service..."
source /Users/a.pothula/workspace/unity/AiTeam/venv/bin/activate
export PYTHONPATH="/Users/a.pothula/workspace/unity/AiTeam:$PYTHONPATH"
uvicorn main:app --reload --port 8003 --host 0.0.0.0
