# Enterprise AI Code Generators
# Production-ready MetaGPT integration for enterprise software generation
import os
import logging
import json
from datetime import datetime

# MetaGPT imports - using correct version 0.8.1
try:
    from metagpt.roles import ProductManager, Architect, Engineer
    from metagpt.team import Team
    METAGPT_AVAILABLE = True
except ImportError:
    METAGPT_AVAILABLE = False
    logging.warning("MetaGPT not available, will use fallback generation")

# Setup logging (portable, no hardcoded path)
LOG_DIR = os.getenv("CODEGEN_LOG_DIR", "./logs/")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "codegen-service.log")
logging.basicConfig(
    filename=LOG_FILE,
    filemode="w",
    format="%(asctime)s - codegen-service - %(levelname)s - %(message)s",
    level=logging.INFO
)

def _run_metagpt_codegen(requirement_text, tasks, language, framework):
    """
    Run MetaGPT multi-agent codegen and return generated files as a dict.
    """
    if not METAGPT_AVAILABLE:
        logging.warning("MetaGPT not available, using fallback")
        return _generate_fallback_files(requirement_text, tasks, language, framework)

    try:
        # Create team with proper roles for MetaGPT 0.8.1
        team = Team()
        team.hire([ProductManager(), Architect(), Engineer()])

        # Set the goal and context
        team.goal = requirement_text

        logging.info(f"Starting MetaGPT generation for: {requirement_text[:100]}...")

        # Run the team
        result = team.run()

        # Process the result - MetaGPT returns different formats
        if hasattr(result, 'files') and result.files:
            generated_files = {}
            for file_path, content in result.files.items():
                # Extract just the filename
                filename = os.path.basename(file_path)
                generated_files[filename] = content
            return generated_files
        elif isinstance(result, dict):
            return result
        else:
            logging.warning("MetaGPT returned unexpected format, using fallback")
            return _generate_fallback_files(requirement_text, tasks, language, framework)

    except Exception as e:
        logging.error(f"MetaGPT codegen failed: {str(e)}")
        return _generate_fallback_files(requirement_text, tasks, language, framework)

def _generate_fallback_files(requirement_text, tasks, language, framework):
    """Generate basic fallback files when MetaGPT fails."""
    files = {}

    if language.lower() == "python" and framework.lower() == "fastapi":
        files["main.py"] = f'''"""Generated FastAPI application."""
from fastapi import FastAPI

app = FastAPI(title="Generated API", version="1.0.0")

@app.get("/")
async def root():
    return {{"message": "Generated API", "requirement": "{requirement_text[:50]}..."}}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}
'''

        files["requirements.txt"] = """fastapi==0.104.1
uvicorn[standard]==0.24.0
"""

        files["README.md"] = f"""# Generated FastAPI Application

Generated from requirement: {requirement_text}

## Features
{chr(10).join(f"- {task}" for task in tasks)}

## Setup
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
"""

    return files

def _write_files_to_repo(result, repo_path):
    """
    Write generated files to repo_path and return list of filenames.
    """
    generated_files = []
    for filename, content in result.items():
        file_path = os.path.join(repo_path, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(content)
        generated_files.append(filename)
    return generated_files

def generate_code_from_tasks(requirement_text, tasks, language, framework, output_dir=None):
    """Main function to generate code from tasks using MetaGPT."""
    logging.info("Starting code generation from task list")
    logging.info(f"Generated requirement text: {requirement_text}")

    if not output_dir:
        output_dir = os.getenv("CODEGEN_OUTPUT_DIR", "./generated_projects/")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    project_name = f"ai_generated_{language}_{framework}_{timestamp}"
    repo_path = os.path.join(output_dir, project_name)
    os.makedirs(repo_path, exist_ok=True)

    try:
        result = _run_metagpt_codegen(requirement_text, tasks, language, framework)
        generated_files = _write_files_to_repo(result, repo_path)
        logging.info(f"Code generation successful. Repo: {repo_path}")

        return {
            "repo_url": f"file://{repo_path}",
            "commit_id": "initial",
            "status": "ready",
            "generated_files": generated_files,
            "metadata": {
                "language": language,
                "framework": framework,
                "generated_files": generated_files,
                "generation_timestamp": timestamp
            }
        }
    except Exception as e:
        logging.error(f"AI code generation failed: {str(e)}")

        # Return error result
        return {
            "repo_url": None,
            "commit_id": None,
            "status": "error",
            "error": str(e)
        }
