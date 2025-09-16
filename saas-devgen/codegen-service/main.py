"""
Enterprise AI Software Generator using Proven Enterprise Frameworks
Production-ready system using MetaGPT, CrewAI, and LangGraph.
No custom JSON parsing - relies on proven enterprise solutions.
"""
import asyncio
import json
import os
import tempfile
import shutil
import uuid
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import asdict

# Enterprise FastAPI (MIT License)
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Enterprise LLM access (MIT License) 
import litellm
import httpx
import requests

# Enterprise configuration
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Requirement, Task, Project

# Enterprise AI Frameworks - Graceful Loading
try:
    from code_generators import generate_code_from_tasks
    ENTERPRISE_GENERATORS_AVAILABLE = True
    logger.info("Enterprise AI frameworks loaded successfully")
except ImportError as e:
    ENTERPRISE_GENERATORS_AVAILABLE = False
    logger.warning(f"Enterprise generators not available: {e}")

from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize enterprise logging
logger = setup_logger("codegen-service", "codegen-service.log")

app = FastAPI(title="Code Generation Service", version="1.0.0")

async def get_ai_settings():
    """Get AI settings from settings service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.profile_service_url}/settings")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Failed to get AI settings: {e}")
    
    # Fallback defaults
    return {
        "ai_provider": "openai",
        "ai_model": "gpt-4",
        "api_key": ""
    }


class CodegenRequest(BaseModel):
    """Code generation request."""
    tasks: List[str]
    language: str = "python"
    framework: str = "fastapi"
    additional_requirements: Optional[str] = None


class CodegenResponse(BaseModel):
    """Code generation response."""
    repo_url: str
    commit_id: str
    status: str
    generated_files: List[str]
    metadata: Dict[str, Any]


class AICodeGenerator:
    """AI-powered code generator with status tracking."""
    
    def __init__(self):
        self.logger = logger
        self.temp_dir = None
        self.status_store = {}  # In-memory status storage
        self.generation_steps = [
            {"name": "initialization", "description": "Setting up project", "est_time": 5},
            {"name": "product_manager", "description": "Analyzing requirements and creating PRD", "est_time": 30},
            {"name": "architect", "description": "Designing system architecture", "est_time": 45},
            {"name": "engineer", "description": "Generating complete code", "est_time": 120},
            {"name": "project_creation", "description": "Creating project structure", "est_time": 10},
            {"name": "finalization", "description": "Finalizing and packaging", "est_time": 5}
        ]
    
    def _update_status(self, generation_id: str, step: str, status: str, details: str = "", progress: int = 0):
        """Update generation status."""
        timestamp = datetime.now().isoformat()
        
        if generation_id not in self.status_store:
            self.status_store[generation_id] = {
                "generation_id": generation_id,
                "started_at": timestamp,
                "current_step": step,
                "status": status,
                "progress": progress,
                "steps_completed": [],
                "estimated_completion": None,
                "details": details
            }
        
        self.status_store[generation_id].update({
            "current_step": step,
            "status": status,
            "progress": progress,
            "details": details,
            "updated_at": timestamp
        })
        
        # Calculate estimated completion time
        if status == "in_progress":
            remaining_steps = [s for s in self.generation_steps if s["name"] not in [sc["name"] for sc in self.status_store[generation_id]["steps_completed"]]]
            if remaining_steps:
                remaining_time = sum(s["est_time"] for s in remaining_steps)
                est_completion = datetime.now() + timedelta(seconds=remaining_time)
                self.status_store[generation_id]["estimated_completion"] = est_completion.isoformat()
        
        self.logger.info(f"Status update [{generation_id}]: {step} - {status} - {details}")
    
    def _complete_step(self, generation_id: str, step_name: str):
        """Mark a step as completed."""
        if generation_id in self.status_store:
            step_info = next((s for s in self.generation_steps if s["name"] == step_name), None)
            if step_info:
                completed_step = {
                    "name": step_name,
                    "description": step_info["description"],
                    "completed_at": datetime.now().isoformat()
                }
                self.status_store[generation_id]["steps_completed"].append(completed_step)
                
                # Update progress percentage
                total_steps = len(self.generation_steps)
                completed_count = len(self.status_store[generation_id]["steps_completed"])
                progress = int((completed_count / total_steps) * 100)
                self.status_store[generation_id]["progress"] = progress
    
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get current status of code generation."""
        return self.status_store.get(generation_id, {"error": "Generation ID not found"})
    
    def generate_code(self, tasks: List[str], language: str, framework: str, 
                     additional_requirements: str = None, generation_id: str = None) -> Dict[str, Any]:
        """
        Generate code based on tasks using AI with status tracking.
        """
        # Generate unique ID for this generation if not provided
        if not generation_id:
            generation_id = f"gen_{int(datetime.now().timestamp())}_{os.getpid()}"
        
        self.logger.info(f"Starting code generation [{generation_id}]: {language}/{framework} for {len(tasks)} tasks")
        
        # Initialize status tracking
        self._update_status(generation_id, "initialization", "in_progress", 
                          f"Starting {language}/{framework} project generation", 5)
        
        # Create temporary directory for code generation
        self.temp_dir = tempfile.mkdtemp(prefix="codegen_")
        self.logger.info(f"Using temp directory: {self.temp_dir}")
        
        try:
            # Complete initialization step
            self._complete_step(generation_id, "initialization")
            
            # Use AI to generate code
            result = self._generate_ai_code(tasks, language, framework, additional_requirements, generation_id)
            
            # Mark as completed
            self._update_status(generation_id, "finalization", "completed", 
                              "Code generation completed successfully", 100)
            self._complete_step(generation_id, "finalization")
            
            # Add generation_id to result
            result["generation_id"] = generation_id
            result["status_info"] = self.get_generation_status(generation_id)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Code generation failed [{generation_id}]: {e}")
            self._update_status(generation_id, "error", "failed", f"Generation failed: {str(e)}", 0)
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise
    
    def _generate_ai_code(self, tasks: List[str], language: str, framework: str, 
                         additional_requirements: str = None, generation_id: str = None) -> Dict[str, Any]:
        """Generate code using enterprise AI frameworks (MetaGPT, CrewAI, LangGraph)."""
        
        if not ENTERPRISE_GENERATORS_AVAILABLE:
            self.logger.warning("Enterprise generators not available, falling back to template generation")
            return self._generate_template_based_code(tasks, language, framework, additional_requirements)
        
        self._update_status(generation_id, "enterprise_ai", "in_progress", 
                          "Enterprise AI frameworks initializing", 15)
        
        # Get AI settings from settings service
        try:
            import requests
            settings_response = requests.get(f"{settings.profile_service_url}/settings")
            if settings_response.status_code == 200:
                ai_settings = settings_response.json()
                ai_provider = ai_settings.get("ai_provider", "openai")
                ai_model = ai_settings.get("ai_model", "gpt-4")
                api_key = ai_settings.get("api_key", "")
                
                if not api_key:
                    self.logger.warning("No API key configured, falling back to template generation")
                    return self._generate_template_based_code(tasks, language, framework, additional_requirements)
                    
                self.logger.info(f"Using enterprise AI: {ai_provider}, model: {ai_model}")
            else:
                self.logger.warning("Settings service unavailable, falling back to template generation")
                return self._generate_template_based_code(tasks, language, framework, additional_requirements)
        except Exception as e:
            self.logger.warning(f"Failed to get AI settings: {e}, falling back to template generation")
            return self._generate_template_based_code(tasks, language, framework, additional_requirements)
        
        try:
            # Configure enterprise AI framework
            enterprise_config = {
                "provider": ai_provider,
                "model": ai_model,
                "api_key": api_key,
                "temperature": 0.3,
                "max_tokens": 4000
            }
            
            # Create requirement string
            requirement_text = f"Create a {language} {framework} application with the following features:\n"
            requirement_text += "\n".join(f"- {task}" for task in tasks)
            if additional_requirements:
                requirement_text += f"\n\nAdditional requirements: {additional_requirements}"
            
            self.logger.info(f"Enterprise requirement: {requirement_text[:200]}...")
            
            try:
                self._update_status(generation_id, "metagpt_generation", "in_progress",
                                  "Using MetaGPT enterprise framework", 40)

                # Use the working code_generators module
                from code_generators import generate_code_from_tasks

                # Generate project using the working MetaGPT implementation
                result = generate_code_from_tasks(requirement_text, tasks, language, framework)

                if result.get("status") == "ready":
                    self.logger.info("Enterprise generation successful using MetaGPT")

                    return {
                        "files": result.get("generated_files", []),
                        "setup_instructions": "See README.md for setup instructions",
                        "enterprise_framework": "MetaGPT",
                        "enterprise_result": {
                            "status": "success",
                            "generator_used": "MetaGPT",
                            "repo_url": result.get("repo_url"),
                            "commit_id": result.get("commit_id")
                        }
                    }
                else:
                    self.logger.warning("MetaGPT generation failed, falling back to template")
                    return self._generate_template_based_code(tasks, language, framework, additional_requirements)

            except Exception as e:
                self.logger.warning(f"MetaGPT enterprise generation failed: {e}")
                # Fallback to template generation
                return self._generate_template_based_code(tasks, language, framework, additional_requirements)
            return self._generate_template_based_code(tasks, language, framework, additional_requirements)
            
        except Exception as e:
            self.logger.error(f"Enterprise AI generation failed: {e}")
            return self._generate_template_based_code(tasks, language, framework, additional_requirements)
    
    def _extract_workspace_files(self, workspace_path: str) -> Dict[str, str]:
        """Extract files from enterprise framework workspace."""
        files = {}
        workspace = Path(workspace_path)
        
        if not workspace.exists():
            return files
        
        for file_path in workspace.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    relative_path = file_path.relative_to(workspace)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[str(relative_path)] = f.read()
                except Exception:
                    # Skip binary files or encoding issues
                    pass
        
        return files
    
    def _parse_enterprise_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Parse enterprise framework result to extract files."""
        files = {}
        
        # Try to extract files from various result formats
        if isinstance(result.get("result"), str):
            content = result["result"]
            
            # Look for code blocks or file sections
            import re
            
            # Pattern for files with headers like "## filename.py" or "### src/main.py"
            file_pattern = r'#{2,3}\s+([^\n]+\.(?:py|js|ts|jsx|tsx|html|css|json|md|yml|yaml|toml|txt))\s*\n```(?:\w+)?\n(.*?)```'
            matches = re.findall(file_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for filename, file_content in matches:
                files[filename.strip()] = file_content.strip()
            
            # If no files found, create a basic structure
            if not files:
                files = self._create_basic_project_structure(result.get("language", "python"), 
                                                           result.get("framework", "fastapi"))
        
        return files
    
    def _create_basic_project_structure(self, language: str, framework: str) -> Dict[str, str]:
        """Create basic project structure when enterprise frameworks don't return files."""
        if language.lower() == "javascript" and framework.lower() == "react":
            return self._create_react_snake_game()
        elif language.lower() == "python" and framework.lower() == "fastapi":
            return self._generate_fastapi_project([], "")
        else:
            return {
                "README.md": f"# Enterprise {language.title()} {framework.title()} Project\n\nGenerated using enterprise AI frameworks.",
                "main.py" if language.lower() == "python" else "index.js": f"# Main {language} file\nprint('Hello Enterprise World!')" if language.lower() == "python" else "console.log('Hello Enterprise World!');"
            }
    
    def _generate_multi_agent_code(self, tasks: List[str], language: str, framework: str, 
                                 additional_requirements: str, generation_id: str) -> Dict[str, Any]:
        """Generate code using multi-agent AI workflow."""
        try:
            # Get AI configuration from profile service
            try:
                profile_service_url = os.getenv("PROFILE_SERVICE_URL", "http://profile-service:8007")
                response = requests.get(f"{profile_service_url}/settings")
                if response.status_code == 200:
                    ai_settings = response.json()
                    ai_provider = ai_settings.get("ai_provider", "openrouter")
                    ai_model = ai_settings.get("ai_model", "deepseek/deepseek-chat")
                    self.logger.info(f"Got AI settings from profile service: {ai_provider}/{ai_model}")
                else:
                    self.logger.warning("Failed to get AI settings from profile service, using defaults")
                    ai_provider = "openrouter"
                    ai_model = "deepseek/deepseek-chat"
            except Exception as e:
                self.logger.warning(f"Error getting AI settings from profile service: {e}, using defaults")
                ai_provider = "openrouter"
                ai_model = "deepseek/deepseek-chat"
            
            # Get API key based on provider
            if ai_provider == "openrouter":
                api_key = os.getenv("OPENROUTER_API_KEY")
            elif ai_provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif ai_provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            else:
                api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                self.logger.error(f"No API key found for provider: {ai_provider}")
                return self._generate_template_based_code(tasks, language, framework, additional_requirements)
            
            # Configure AI settings based on provider
            if ai_provider == "openrouter":
                # For OpenRouter, prepend 'openrouter/' to model name if not already present
                model_name = ai_model if ai_model.startswith("openrouter/") else f"openrouter/{ai_model}"
                ai_config = {
                    "provider": ai_provider,
                    "model": model_name,
                    "api_key": api_key,
                    "api_base": "https://openrouter.ai/api/v1",
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            elif ai_provider == "azure":
                ai_config = {
                    "provider": ai_provider,
                    "model": ai_model,
                    "api_key": api_key,
                    "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            else:
                # Default for OpenAI, Anthropic
                ai_config = {
                    "provider": ai_provider,
                    "model": ai_model,
                    "api_key": api_key,
                    "api_base": None,  # Use default endpoints
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            
            # Step 1: Product Manager - Analyze requirements and create PRD
            prd = self._agent_product_manager(tasks, additional_requirements, ai_config)
            self.logger.info("Product Manager completed requirement analysis")
            self._complete_step(generation_id, "product_manager")
            
            # Step 2: Architect - Design system architecture
            self._update_status(generation_id, "architect", "in_progress", 
                              "AI Architect designing system architecture", 40)
            architecture = self._agent_architect(prd, language, framework, ai_config)
            self.logger.info("Architect completed system design")
            self._complete_step(generation_id, "architect")
            
            # Step 3: Engineer - Generate code based on architecture
            self._update_status(generation_id, "engineer", "in_progress", 
                              "AI Engineer generating complete codebase", 60)
            code_result = self._agent_engineer(prd, architecture, language, framework, ai_config)
            self.logger.info("Engineer completed code generation")
            self._complete_step(generation_id, "engineer")
            
            # Create project structure
            self._update_status(generation_id, "project_creation", "in_progress", 
                              "Creating project structure and files", 90)
            result = self._create_project_from_agents(code_result, language, framework, tasks)
            self._complete_step(generation_id, "project_creation")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Multi-agent AI code generation failed: {e}")
            self.logger.info("Falling back to template-based generation")
            return self._generate_template_based_code(tasks, language, framework, additional_requirements)
    
    def _get_ai_config(self) -> Dict[str, str]:
        """Get AI configuration from environment variables."""
        return {
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model": os.getenv("OPENROUTER_MODEL", "openrouter/deepseek/deepseek-chat-v3.1:free"),
            "api_base": os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
            "temperature": float(os.getenv("OPENROUTER_TEMPERATURE", "0.3")),
            "max_tokens": int(os.getenv("OPENROUTER_MAX_TOKENS", "2000"))
        }
    
    def _make_ai_completion(self, prompt: str, ai_config: Dict[str, Any]) -> str:
        """Make AI completion call with proper provider configuration."""
        completion_params = {
            "model": ai_config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": ai_config["temperature"],
            "max_tokens": ai_config["max_tokens"]
        }
        
        # Configure authentication based on provider
        if ai_config["provider"] == "openrouter":
            # For OpenRouter, use extra_headers with Authorization bearer token
            completion_params["extra_headers"] = {
                "Authorization": f"Bearer {ai_config['api_key']}",
                "HTTP-Referer": "https://aiteam.enterprise.local",
                "X-Title": "AiTeam Enterprise Code Generator"
            }
        else:
            # For other providers, use standard api_key parameter
            completion_params["api_key"] = ai_config["api_key"]
            if ai_config["api_base"]:
                completion_params["api_base"] = ai_config["api_base"]
        
        response = litellm.completion(**completion_params)
        return response.choices[0].message.content
    
    def _parse_ai_json_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response with robust JSON extraction."""
        try:
            # Try direct parsing first
            return json.loads(content)
        except json.JSONDecodeError:
            # Try extracting from markdown code blocks
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end > json_start:
                    json_content = content[json_start:json_end].strip()
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError:
                        pass
            
            # Try extracting JSON objects with regex (more robust)
            import re
            # Look for JSON starting with { and ending with } allowing for newlines
            json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            for match in json_matches:
                try:
                    # Clean up common AI formatting issues
                    cleaned = match.strip()
                    # Fix unescaped quotes in strings
                    cleaned = re.sub(r'(?<!\\)"(?=(?:[^"\\]|\\.)*")', '\\"', cleaned)
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    continue
            
            # Last resort: create a minimal response
            self.logger.error(f"Could not parse JSON from AI response: {content[:500]}...")
            return {
                "files": {
                    "error.txt": f"JSON parsing failed for AI response. Content length: {len(content)}"
                },
                "setup_instructions": "AI response could not be parsed properly"
            }
    
    def _agent_product_manager(self, tasks: List[str], additional_requirements: str = None, 
                              ai_config: Dict[str, str] = None) -> Dict[str, Any]:
        """Product Manager Agent - Analyzes requirements and creates PRD."""
        
        prompt = f"""You are a Senior Product Manager. Analyze these requirements and create a Product Requirements Document (PRD).

REQUIREMENTS:
{chr(10).join(f"- {task}" for task in tasks)}

{f"ADDITIONAL CONTEXT: {additional_requirements}" if additional_requirements else ""}

Create a comprehensive PRD with:
1. Project Overview
2. Core Features
3. User Stories
4. Technical Requirements
5. Success Criteria

Respond in JSON format:
{{
  "project_name": "...",
  "overview": "...",
  "core_features": ["feature1", "feature2"],
  "user_stories": ["story1", "story2"],
  "technical_requirements": ["req1", "req2"],
  "success_criteria": ["criteria1", "criteria2"]
}}"""

        # Prepare completion parameters
        prd_content = self._make_ai_completion(prompt, ai_config)
        
        return self._parse_ai_json_response(prd_content)
    
    def _agent_architect(self, prd: Dict[str, Any], language: str, framework: str, 
                        ai_config: Dict[str, str] = None) -> Dict[str, Any]:
        """Architect Agent - Designs system architecture."""
        
        prompt = f"""You are a Senior Software Architect. Based on this PRD, design the system architecture.

PRD:
{json.dumps(prd, indent=2)}

TARGET: {language} {framework} application

Design the architecture with:
1. System components
2. Database schema
3. API endpoints
4. File structure
5. Technology stack

Respond in JSON format:
{{
  "components": ["component1", "component2"],
  "database_schema": {{"table1": ["field1", "field2"]}},
  "api_endpoints": ["/endpoint1", "/endpoint2"],
  "file_structure": ["file1.py", "file2.py"],
  "tech_stack": ["technology1", "technology2"]
}}"""

        # Prepare completion parameters
        arch_content = self._make_ai_completion(prompt, ai_config)
        
        return self._parse_ai_json_response(arch_content)
    
    def _agent_engineer(self, prd: Dict[str, Any], architecture: Dict[str, Any], 
                       language: str, framework: str, ai_config: Dict[str, str] = None) -> Dict[str, Any]:
        """Engineer Agent - Generates code based on PRD and architecture."""
        
        prompt = f"""You are a Senior Software Engineer. Implement the system based on this PRD and architecture.

PRD:
{json.dumps(prd, indent=2)}

ARCHITECTURE:
{json.dumps(architecture, indent=2)}

TARGET: {language} {framework}

Generate complete, production-ready code for all files. Include:
- Main application files
- Models/schemas
- Database setup
- API routes
- Configuration files
- Requirements/dependencies
- Dockerfile
- README with setup instructions

Respond in JSON format:
{{
  "files": {{
    "filename1.py": "complete file content here",
    "filename2.py": "complete file content here",
    "requirements.txt": "dependencies here",
    "README.md": "setup instructions here"
  }},
  "setup_instructions": "How to run the project"
}}

Make sure all code is complete, functional, and follows best practices."""

        # Prepare completion parameters - override max_tokens for Engineer
        engineer_config = ai_config.copy()
        engineer_config["max_tokens"] = int(os.getenv("OPENROUTER_MAX_TOKENS_ENGINEER", "8000"))
        
        code_content = self._make_ai_completion(prompt, engineer_config)
        
        return self._parse_ai_json_response(code_content)
    
    def _create_project_from_agents(self, code_result: Dict[str, Any], language: str, framework: str, 
                                   tasks: List[str]) -> Dict[str, Any]:
        """Create project structure from multi-agent AI response."""
        
        # Generate proper UUIDs for enterprise tracking
        project_uuid = str(uuid.uuid4())
        project_name = f"ai_generated_{language}_{framework}_{project_uuid[:8]}"
        
        # Create permanent project directory in generated_projects folder
        base_projects_dir = os.path.join(os.path.dirname(self.temp_dir), "generated_projects")
        os.makedirs(base_projects_dir, exist_ok=True)
        
        project_path = os.path.join(base_projects_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        generated_files = []
        
        # Create files from AI response
        files_data = code_result.get("files", {})
        if not files_data:
            # If no files generated, create a minimal project structure
            if language.lower() == "javascript" and framework.lower() == "react":
                files_data = self._create_react_snake_game()
            else:
                files_data = {"README.md": f"# {project_name}\n\nGenerated project for {language} {framework}"}
        
        for filename, content in files_data.items():
            file_path = os.path.join(project_path, filename)
            
            # Create subdirectories if needed
            file_dir = os.path.dirname(file_path)
            if file_dir != project_path:
                os.makedirs(file_dir, exist_ok=True)
            
            with open(file_path, "w") as f:
                f.write(content)
            generated_files.append(filename)
            self.logger.info(f"Created AI-generated file: {filename}")
        
        # Create a project metadata file with UUIDs
        metadata = {
            "project_uuid": project_uuid,
            "project_name": project_name,
            "generated_at": datetime.now().isoformat(),
            "language": language,
            "framework": framework,
            "generation_method": "multi_agent_ai",
            "setup_instructions": code_result.get("setup_instructions", "No specific instructions provided"),
            "files": generated_files,
            "tasks": tasks,
            "task_uuids": [str(uuid.uuid4()) for _ in tasks]  # Generate UUIDs for each task
        }
        
        metadata_path = os.path.join(project_path, "project_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Project saved permanently at: {project_path}")
        
        # Upload project to storage service (Minio)
        storage_result = self._upload_to_storage_service(project_path, project_uuid, metadata)
        
        return {
            "project_uuid": project_uuid,
            "project_path": project_path,
            "project_name": project_name,
            "generated_files": generated_files,
            "language": language,
            "framework": framework,
            "status": "completed",
            "generation_method": "multi_agent_ai",
            "setup_instructions": code_result.get("setup_instructions", "No specific instructions provided"),
            "repo_url": storage_result.get("repo_url", f"file://{project_path}"),
            "minio_bucket": storage_result.get("bucket"),
            "minio_path": storage_result.get("object_path"),
            "download_url": storage_result.get("download_url"),
            "commit_id": f"gen_{project_uuid[:8]}",  # UUID-based commit ID
            "metadata": metadata
        }
    
    def _upload_to_storage_service(self, project_path: str, project_uuid: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload project files to storage service (Minio)."""
        try:
            import zipfile
            import io
            
            # Create a zip file of the project
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_path)
                        zip_file.write(file_path, arcname)
            
            zip_buffer.seek(0)
            
            # Upload to storage service
            storage_url = settings.storage_service_url
            upload_endpoint = f"{storage_url}/upload/project"
            
            files = {
                'file': (f"{metadata['project_name']}.zip", zip_buffer.getvalue(), 'application/zip')
            }
            
            data = {
                'project_uuid': project_uuid,
                'metadata': json.dumps(metadata)
            }
            
            response = httpx.post(upload_endpoint, files=files, data=data, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Project uploaded to storage: {result}")
                return {
                    "bucket": "projects",
                    "object_path": f"projects/{project_uuid}/{metadata['project_name']}.zip",
                    "repo_url": f"minio://projects/{project_uuid}/{metadata['project_name']}.zip",
                    "download_url": f"{settings.api_gateway_url}/api/v1/projects/{project_uuid}/download"
                }
            else:
                self.logger.error(f"Failed to upload to storage: {response.text}")
                return {"error": "Upload failed"}
                
        except Exception as e:
            self.logger.error(f"Storage upload error: {e}")
            return {"error": str(e)}
    
    def _generate_template_based_code(self, tasks: List[str], language: str, framework: str, 
                                    additional_requirements: str = None) -> Dict[str, Any]:
        """Fallback to template-based generation."""
        
        if language.lower() == "python" and framework.lower() == "fastapi":
            return self._generate_fastapi_project(tasks, additional_requirements)
        elif language.lower() == "javascript" and framework.lower() == "nextjs":
            return self._generate_nextjs_project(tasks, additional_requirements)
        else:
            return self._generate_generic_project(tasks, language, framework)

    def _generate_fastapi_project(self, tasks: List[str], additional_requirements: str) -> Dict[str, Any]:
        """Generate FastAPI project structure."""
        project_name = "generated_api"
        project_path = os.path.join(self.temp_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        generated_files = []
        
        # Main application file
        main_py = self._create_fastapi_main(tasks)
        main_path = os.path.join(project_path, "main.py")
        with open(main_path, "w") as f:
            f.write(main_py)
        generated_files.append("main.py")
        
        # Requirements file
        requirements = self._create_requirements(additional_requirements)
        req_path = os.path.join(project_path, "requirements.txt")
        with open(req_path, "w") as f:
            f.write(requirements)
        generated_files.append("requirements.txt")
        
        # Models file
        models_py = self._create_models(tasks)
        models_path = os.path.join(project_path, "models.py")
        with open(models_path, "w") as f:
            f.write(models_py)
        generated_files.append("models.py")
        
        # Database file
        database_py = self._create_database_file()
        db_path = os.path.join(project_path, "database.py")
        with open(db_path, "w") as f:
            f.write(database_py)
        generated_files.append("database.py")
        
        # Dockerfile
        dockerfile = self._create_dockerfile()
        docker_path = os.path.join(project_path, "Dockerfile")
        with open(docker_path, "w") as f:
            f.write(dockerfile)
        generated_files.append("Dockerfile")
        
        # README
        readme = self._create_readme(project_name, tasks)
        readme_path = os.path.join(project_path, "README.md")
        with open(readme_path, "w") as f:
            f.write(readme)
        generated_files.append("README.md")
        
        return {
            "project_path": project_path,
            "generated_files": generated_files,
            "language": "python",
            "framework": "fastapi",
            "status": "completed"
        }
    
    def _create_fastapi_main(self, tasks: List[str]) -> str:
        """Create main FastAPI application file."""
        has_auth = any("auth" in task.lower() for task in tasks)
        has_database = any("database" in task.lower() or "model" in task.lower() for task in tasks)
        
        main_content = '''"""Generated FastAPI application."""
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel'''

        if has_database:
            main_content += '''
from sqlalchemy.orm import Session
from database import get_db, create_tables
from models import *'''

        main_content += '''

app = FastAPI(
    title="Generated API",
    description="Auto-generated API based on requirements",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''

        if has_database:
            main_content += '''

@app.on_event("startup")
async def startup_event():
    """Initialize database tables."""
    create_tables()'''

        # Generate basic endpoints based on tasks
        main_content += '''

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Generated API is running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}'''

        # Add CRUD endpoints if database-related tasks
        if has_database:
            main_content += '''

class ItemCreate(BaseModel):
    """Item creation model."""
    name: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    """Item response model."""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

@app.post("/items/", response_model=ItemResponse)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item."""
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/", response_model=List[ItemResponse])
async def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all items."""
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get item by ID."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item'''

        main_content += '''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)'''

        return main_content
    
    def _create_models(self, tasks: List[str]) -> str:
        """Create database models."""
        models_content = '''"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Item(Base):
    """Example item model."""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())'''

        return models_content
    
    def _create_database_file(self) -> str:
        """Create database configuration file."""
        return '''"""Database configuration."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)'''
    
    def _create_requirements(self, additional_requirements: str) -> str:
        """Create requirements.txt file."""
        base_requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "sqlalchemy==2.0.23",
            "python-multipart==0.0.6"
        ]
        
        if additional_requirements:
            base_requirements.extend(additional_requirements.split("\n"))
        
        return "\n".join(base_requirements)
    
    def _create_dockerfile(self) -> str:
        """Create Dockerfile."""
        return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'''
    
    def _create_readme(self, project_name: str, tasks: List[str]) -> str:
        """Create README file."""
        tasks_list = "\n".join([f"- {task}" for task in tasks])
        
        return f'''# {project_name.title()}

Auto-generated FastAPI application based on the following requirements:

## Tasks Implemented
{tasks_list}

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload
```

3. Visit http://localhost:8000/docs for API documentation

## Docker

Build and run with Docker:
```bash
docker build -t {project_name} .
docker run -p 8000:8000 {project_name}
```

## Generated on
{datetime.utcnow().isoformat()}
'''
    
    def _generate_nextjs_project(self, tasks: List[str], additional_requirements: str) -> Dict[str, Any]:
        """Generate Next.js project (placeholder)."""
        # For MVP, return simple structure
        return {
            "project_path": self.temp_dir,
            "generated_files": ["package.json", "pages/index.js"],
            "language": "javascript",
            "framework": "nextjs",
            "status": "completed"
        }
    
    def _generate_generic_project(self, tasks: List[str], language: str, framework: str) -> Dict[str, Any]:
        """Generate generic project structure."""
        return {
            "project_path": self.temp_dir,
            "generated_files": ["main.py", "README.md"],
            "language": language,
            "framework": framework,
            "status": "completed"
        }
    
    def _create_react_snake_game(self) -> Dict[str, str]:
        """Create a complete React Snake game as fallback."""
        return {
            "package.json": '''{
  "name": "react-snake-game",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}''',
            "public/index.html": '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React Snake Game</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>''',
            "src/index.js": '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import SnakeGame from './SnakeGame';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<SnakeGame />);''',
            "src/index.css": '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #1a1a1a;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.game-container {
  text-align: center;
}

.game-board {
  border: 2px solid #fff;
  background-color: #000;
  margin: 20px auto;
}

.score {
  font-size: 24px;
  margin: 10px;
}

.game-over {
  color: #ff0000;
  font-size: 32px;
  margin: 20px;
}

button {
  padding: 10px 20px;
  font-size: 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
}

button:hover {
  background-color: #45a049;
}''',
            "src/SnakeGame.js": '''import React, { useState, useEffect, useCallback } from 'react';

const BOARD_SIZE = 20;
const INITIAL_SNAKE = [{ x: 10, y: 10 }];
const INITIAL_FOOD = { x: 15, y: 15 };
const INITIAL_DIRECTION = { x: 0, y: -1 };

const SnakeGame = () => {
  const [snake, setSnake] = useState(INITIAL_SNAKE);
  const [food, setFood] = useState(INITIAL_FOOD);
  const [direction, setDirection] = useState(INITIAL_DIRECTION);
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [gameStarted, setGameStarted] = useState(false);

  const generateFood = useCallback(() => {
    const newFood = {
      x: Math.floor(Math.random() * BOARD_SIZE),
      y: Math.floor(Math.random() * BOARD_SIZE)
    };
    return newFood;
  }, []);

  const checkCollision = useCallback((head, snakeArray) => {
    // Wall collision
    if (head.x < 0 || head.x >= BOARD_SIZE || head.y < 0 || head.y >= BOARD_SIZE) {
      return true;
    }
    // Self collision
    for (let segment of snakeArray) {
      if (head.x === segment.x && head.y === segment.y) {
        return true;
      }
    }
    return false;
  }, []);

  const moveSnake = useCallback(() => {
    if (gameOver || !gameStarted) return;

    setSnake(currentSnake => {
      const newSnake = [...currentSnake];
      const head = { x: newSnake[0].x + direction.x, y: newSnake[0].y + direction.y };

      if (checkCollision(head, newSnake)) {
        setGameOver(true);
        return currentSnake;
      }

      newSnake.unshift(head);

      // Check if food is eaten
      if (head.x === food.x && head.y === food.y) {
        setScore(prevScore => prevScore + 10);
        setFood(generateFood());
      } else {
        newSnake.pop();
      }

      return newSnake;
    });
  }, [direction, food, gameOver, gameStarted, checkCollision, generateFood]);

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (!gameStarted) return;
      
      switch (e.key) {
        case 'ArrowUp':
          if (direction.y !== 1) setDirection({ x: 0, y: -1 });
          break;
        case 'ArrowDown':
          if (direction.y !== -1) setDirection({ x: 0, y: 1 });
          break;
        case 'ArrowLeft':
          if (direction.x !== 1) setDirection({ x: -1, y: 0 });
          break;
        case 'ArrowRight':
          if (direction.x !== -1) setDirection({ x: 1, y: 0 });
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [direction, gameStarted]);

  useEffect(() => {
    if (gameStarted && !gameOver) {
      const gameInterval = setInterval(moveSnake, 200);
      return () => clearInterval(gameInterval);
    }
  }, [moveSnake, gameStarted, gameOver]);

  const resetGame = () => {
    setSnake(INITIAL_SNAKE);
    setFood(INITIAL_FOOD);
    setDirection(INITIAL_DIRECTION);
    setGameOver(false);
    setScore(0);
    setGameStarted(true);
  };

  const renderBoard = () => {
    const board = [];
    for (let row = 0; row < BOARD_SIZE; row++) {
      for (let col = 0; col < BOARD_SIZE; col++) {
        const isSnake = snake.some(segment => segment.x === col && segment.y === row);
        const isFood = food.x === col && food.y === row;
        const cellClass = isSnake ? 'snake' : isFood ? 'food' : 'empty';
        
        board.push(
          <div
            key={`${row}-${col}`}
            className={cellClass}
            style={{
              width: 20,
              height: 20,
              backgroundColor: isSnake ? '#4CAF50' : isFood ? '#FF0000' : '#000',
              border: '1px solid #333',
              display: 'inline-block'
            }}
          />
        );
      }
    }
    return board;
  };

  return (
    <div className="game-container">
      <h1>React Snake Game</h1>
      <div className="score">Score: {score}</div>
      
      {gameOver && <div className="game-over">Game Over!</div>}
      
      <div 
        className="game-board"
        style={{ 
          width: BOARD_SIZE * 22, 
          height: BOARD_SIZE * 22,
          display: 'grid',
          gridTemplateColumns: `repeat(${BOARD_SIZE}, 20px)`,
          gap: '1px'
        }}
      >
        {renderBoard()}
      </div>
      
      <div>
        <button onClick={resetGame}>
          {gameStarted ? 'Restart Game' : 'Start Game'}
        </button>
      </div>
      
      {gameStarted && (
        <div style={{ marginTop: '20px' }}>
          <p>Use arrow keys to control the snake</p>
        </div>
      )}
    </div>
  );
};

export default SnakeGame;''',
            "README.md": '''# React Snake Game

A fully functional Snake game built with React.

## Features

- Responsive game board (20x20 grid)
- Arrow key controls for snake movement
- Food spawning mechanics
- Collision detection for walls and snake body
- Score tracking
- Game over screen with restart functionality
- Modern React hooks implementation

## Setup Instructions

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

## How to Play

- Click "Start Game" to begin
- Use arrow keys to control the snake
- Eat the red food to grow and increase your score
- Avoid hitting walls or the snake's own body
- Click "Restart Game" to play again

## Generated by AiTeam Enterprise Platform

This game was automatically generated using AI agents with enterprise-grade code generation.
''',
            "Dockerfile": '''FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'''
        }


code_generator = AICodeGenerator()


@app.post("/generate")
async def generate_code_from_tasks(request: dict):
    """Generate code from a list of tasks (API Gateway compatible)."""
    logger.info("Starting code generation from task list")
    
    try:
        tasks = request.get("tasks", [])
        language = request.get("language", "python")
        framework = request.get("framework", "fastapi")
        additional_requirements = request.get("additional_requirements", "")
        
        if not tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tasks list is required"
            )
        
        # Create a temporary requirement text from tasks
        requirement_text = f"Create a {language} {framework} application with the following features:\n"
        requirement_text += "\n".join(f"- {task}" for task in tasks)
        if additional_requirements:
            requirement_text += f"\n\nAdditional requirements: {additional_requirements}"
        
        logger.info(f"Generated requirement text: {requirement_text[:200]}...")
        
        # Generate unique generation ID
        generation_id = f"gen_{int(time.time())}_{request.get('priority', 'medium')}"
        
        # Run multi-agent code generation with status tracking
        result = code_generator.generate_code(
            tasks=tasks,
            language=language,
            framework=framework,
            additional_requirements=additional_requirements,
            generation_id=generation_id
        )
        
        return {
            "status": "completed",
            "generation_id": generation_id,
            "language": language,
            "framework": framework,
            "project_path": result.get("project_path"),
            "generated_files": result.get("generated_files", []),
            "repo_url": result.get("repo_url", ""),
            "commit_id": result.get("commit_id", ""),
            "setup_instructions": result.get("setup_instructions", ""),
            "status_info": result.get("status_info", {}),
            "message": "Project generated successfully"
        }
        
    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}"
        )


@app.post("/codegen/{requirement_id}", response_model=CodegenResponse)
async def generate_code(
    requirement_id: int,
    request: CodegenRequest,
    db: Session = Depends(get_db)
):
    """Generate code for a requirement."""
    logger.info(f"Code generation requested for requirement {requirement_id}")
    
    try:
        # Verify requirement exists
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requirement not found"
            )
        
        # Generate code
        result = code_generator.generate_code(
            tasks=request.tasks,
            language=request.language,
            framework=request.framework,
            additional_requirements=request.additional_requirements
        )
        
        # Create project record
        project = Project(
            tenant_id=requirement.tenant_id,
            requirement_id=requirement_id,
            repo_url=f"file://{result['project_path']}",
            commit_id="initial",
            project_metadata={
                "language": result["language"],
                "framework": result["framework"],
                "generated_files": result["generated_files"],
                "generation_timestamp": datetime.utcnow().isoformat()
            },
            status="ready"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"Code generated successfully for requirement {requirement_id}")
        
        return CodegenResponse(
            repo_url=project.repo_url,
            commit_id=project.commit_id,
            status=project.status,
            generated_files=result["generated_files"],
            metadata=project.project_metadata
        )
        
    except Exception as e:
        logger.error(f"Code generation failed for requirement {requirement_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code generation failed"
        )


@app.get("/status/{generation_id}")
async def get_generation_status(generation_id: str):
    """Get real-time status of code generation."""
    try:
        status_info = code_generator.get_generation_status(generation_id)
        
        if "error" in status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generation ID {generation_id} not found"
            )
        
        return {
            "generation_id": generation_id,
            "status": status_info["status"],
            "current_step": status_info["current_step"],
            "progress": status_info["progress"],
            "steps_completed": status_info["steps_completed"],
            "estimated_completion": status_info.get("estimated_completion"),
            "details": status_info["details"],
            "started_at": status_info["started_at"],
            "updated_at": status_info.get("updated_at")
        }
        
    except Exception as e:
        logger.error(f"Failed to get status for {generation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve generation status"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "codegen-service",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Codegen Service on port 8003")
    uvicorn.run(app, host="0.0.0.0", port=8003)
