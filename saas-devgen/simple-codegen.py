#!/usr/bin/env python3
"""Simple codegen service with /generate endpoint - no complex imports."""

from fastapi import FastAPI
import json
import time

app = FastAPI(title="Simple Codegen Service")

@app.post("/generate")
async def generate_code(request: dict):
    """Generate code from tasks - simplified version."""
    tasks = request.get("tasks", [])
    language = request.get("language", "python")
    framework = request.get("framework", "fastapi")
    
    # Simulate code generation
    project_name = f"generated_project_{int(time.time())}"
    
    return {
        "status": "completed",
        "language": language,
        "framework": framework,
        "project_path": f"/tmp/{project_name}",
        "generated_files": [
            "main.py",
            "requirements.txt",
            "README.md"
        ],
        "repo_url": f"local://{project_name}",
        "commit_id": "abc123",
        "setup_instructions": "pip install -r requirements.txt && python main.py",
        "message": "Project generated successfully"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "simple-codegen"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple Codegen Service on port 8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)
