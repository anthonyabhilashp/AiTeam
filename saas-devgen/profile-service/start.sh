#!/bin/bash
# Profile Service Startup Script
cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH}:../.."
uvicorn main:app --host 0.0.0.0 --port 8007 --reload
