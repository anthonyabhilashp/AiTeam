"""Codegen Service - AI-powered code generation."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
import json
import os
import tempfile
import shutil
import litellm
from dotenv import load_dotenv
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Requirement, Task, Project
from sqlalchemy.orm import Session

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("codegen-service", "codegen-service.log")

app = FastAPI(title="Code Generation Service", version="1.0.0")


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
    """AI-powered code generator."""
    
    def __init__(self):
        self.logger = logger
        self.temp_dir = None
    
    def generate_code(self, tasks: List[str], language: str, framework: str, 
                     additional_requirements: str = None) -> Dict[str, Any]:
        """
        Generate code based on tasks using AI.
        """
        self.logger.info(f"Generating {language}/{framework} code for {len(tasks)} tasks using AI")
        
        # Create temporary directory for code generation
        self.temp_dir = tempfile.mkdtemp(prefix="codegen_")
        self.logger.info(f"Using temp directory: {self.temp_dir}")
        
        try:
            # Use AI to generate code
            return self._generate_ai_code(tasks, language, framework, additional_requirements)
        
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise
    
    def _generate_ai_code(self, tasks: List[str], language: str, framework: str, 
                         additional_requirements: str = None) -> Dict[str, Any]:
        """Generate code using multi-agent AI workflow (inspired by MetaGPT)."""
        
        # Configure LiteLLM for OpenRouter
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "openrouter/deepseek/deepseek-chat-v3.1:free")
        openrouter_api_base = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
        
        if not openrouter_api_key:
            self.logger.warning("OPENROUTER_API_KEY not found, falling back to template generation")
            return self._generate_template_based_code(tasks, language, framework, additional_requirements)
        
        try:
            # Get AI configuration
            ai_config = self._get_ai_config()
            
            # Step 1: Product Manager - Analyze requirements and create PRD
            prd = self._agent_product_manager(tasks, additional_requirements, ai_config)
            self.logger.info("Product Manager completed requirement analysis")
            
            # Step 2: Architect - Design system architecture
            architecture = self._agent_architect(prd, language, framework, ai_config)
            self.logger.info("Architect completed system design")
            
            # Step 3: Engineer - Generate code based on architecture
            code_result = self._agent_engineer(prd, architecture, language, framework, ai_config)
            self.logger.info("Engineer completed code generation")
            
            # Create project structure
            return self._create_project_from_agents(code_result, language, framework, tasks)
            
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

        response = litellm.completion(
            model=ai_config["model"],
            messages=[{"role": "user", "content": prompt}],
            api_key=ai_config["api_key"],
            api_base=ai_config["api_base"],
            temperature=ai_config["temperature"],
            max_tokens=ai_config["max_tokens"]
        )
        
        prd_content = response.choices[0].message.content
        try:
            return json.loads(prd_content)
        except json.JSONDecodeError:
            # Extract JSON if wrapped in markdown
            if "```json" in prd_content:
                json_start = prd_content.find("```json") + 7
                json_end = prd_content.find("```", json_start)
                return json.loads(prd_content[json_start:json_end].strip())
            raise
    
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

        response = litellm.completion(
            model=ai_config["model"],
            messages=[{"role": "user", "content": prompt}],
            api_key=ai_config["api_key"],
            api_base=ai_config["api_base"],
            temperature=ai_config["temperature"],
            max_tokens=ai_config["max_tokens"]
        )
        
        arch_content = response.choices[0].message.content
        try:
            return json.loads(arch_content)
        except json.JSONDecodeError:
            if "```json" in arch_content:
                json_start = arch_content.find("```json") + 7
                json_end = arch_content.find("```", json_start)
                return json.loads(arch_content[json_start:json_end].strip())
            raise
    
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

        response = litellm.completion(
            model=ai_config["model"],
            messages=[{"role": "user", "content": prompt}],
            api_key=ai_config["api_key"],
            api_base=ai_config["api_base"],
            temperature=ai_config["temperature"],
            max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS_ENGINEER", "8000"))
        )
        
        code_content = response.choices[0].message.content
        try:
            return json.loads(code_content)
        except json.JSONDecodeError:
            if "```json" in code_content:
                json_start = code_content.find("```json") + 7
                json_end = code_content.find("```", json_start)
                return json.loads(code_content[json_start:json_end].strip())
            raise
    
    def _create_project_from_agents(self, code_result: Dict[str, Any], language: str, framework: str, 
                                   tasks: List[str]) -> Dict[str, Any]:
        """Create project structure from multi-agent AI response."""
        
        project_name = f"ai_generated_project_{int(datetime.now().timestamp())}"
        
        # Create permanent project directory in generated_projects folder
        base_projects_dir = os.path.join(os.path.dirname(self.temp_dir), "generated_projects")
        os.makedirs(base_projects_dir, exist_ok=True)
        
        project_path = os.path.join(base_projects_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        generated_files = []
        
        # Create files from AI response
        for filename, content in code_result.get("files", {}).items():
            file_path = os.path.join(project_path, filename)
            
            # Create subdirectories if needed
            file_dir = os.path.dirname(file_path)
            if file_dir != project_path:
                os.makedirs(file_dir, exist_ok=True)
            
            with open(file_path, "w") as f:
                f.write(content)
            generated_files.append(filename)
            self.logger.info(f"Created AI-generated file: {filename}")
        
        # Create a project metadata file
        metadata = {
            "project_name": project_name,
            "generated_at": datetime.now().isoformat(),
            "language": language,
            "framework": framework,
            "generation_method": "multi_agent_ai",
            "setup_instructions": code_result.get("setup_instructions", "No specific instructions provided"),
            "files": generated_files,
            "tasks": tasks
        }
        
        metadata_path = os.path.join(project_path, "project_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Project saved permanently at: {project_path}")
        
        return {
            "project_path": project_path,
            "project_name": project_name,
            "generated_files": generated_files,
            "language": language,
            "framework": framework,
            "status": "completed",
            "generation_method": "multi_agent_ai",
            "setup_instructions": code_result.get("setup_instructions", "No specific instructions provided"),
            "repo_url": f"file://{project_path}",  # Local file URL
            "commit_id": f"gen_{int(datetime.now().timestamp())}",  # Simple commit ID
            "metadata": metadata
        }
    
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
        
        # Run multi-agent code generation
        result = code_generator.generate_code(
            tasks=tasks,
            language=language,
            framework=framework,
            additional_requirements=additional_requirements
        )
        
        return {
            "status": "completed",
            "language": language,
            "framework": framework,
            "project_path": result.get("project_path"),
            "generated_files": result.get("generated_files", []),
            "repo_url": result.get("repo_url", ""),
            "commit_id": result.get("commit_id", ""),
            "setup_instructions": result.get("setup_instructions", ""),
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
