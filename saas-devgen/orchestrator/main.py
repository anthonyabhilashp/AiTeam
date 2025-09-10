"""Orchestrator Service - Manages requirement intake and task breakdown."""
import sys
import os
# Add the parent directory to sys.path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Requirement, Task, User
from sqlalchemy.orm import Session

# Initialize logger
logger = setup_logger("orchestrator", "orchestrator.log")

app = FastAPI(title="Orchestrator Service", version="1.0.0")


class RequirementRequest(BaseModel):
    """Requirement creation request."""
    requirement: str


class TaskResponse(BaseModel):
    """Task response model."""
    id: int
    description: str
    status: str
    order_index: int


class RequirementResponse(BaseModel):
    """Requirement response model."""
    requirement_id: int
    text: str
    status: str
    tasks: List[TaskResponse]
    created_at: datetime


class AIPromptManager:
    """Manages AI prompts for requirement breakdown."""
    
    def __init__(self):
        self.logger = logger
    
    def break_down_requirement(self, requirement_text: str) -> List[str]:
        """
        Break down requirement into tasks using AI.
        For now, using simple rule-based approach.
        In production, integrate with MetaGPT or similar.
        """
        self.logger.info(f"Breaking down requirement: {requirement_text[:100]}...")
        
        # Simple task breakdown logic (replace with AI)
        tasks = []
        
        if "api" in requirement_text.lower():
            tasks.extend([
                "Design API endpoints and data models",
                "Set up FastAPI project structure",
                "Implement authentication middleware",
                "Create database models and migrations",
                "Implement API endpoints with validation",
                "Add error handling and logging",
                "Write unit tests for API endpoints",
                "Create API documentation"
            ])
        
        if "frontend" in requirement_text.lower() or "ui" in requirement_text.lower():
            tasks.extend([
                "Design UI/UX wireframes",
                "Set up React/Next.js project",
                "Implement responsive layout",
                "Create reusable components",
                "Integrate with backend APIs",
                "Add state management",
                "Implement error handling",
                "Write component tests"
            ])
        
        if "database" in requirement_text.lower():
            tasks.extend([
                "Design database schema",
                "Set up database migrations",
                "Implement data access layer",
                "Add database indexing",
                "Set up backup strategy"
            ])
        
        # Default tasks if no specific patterns found
        if not tasks:
            tasks = [
                "Analyze requirements and create technical specification",
                "Design system architecture",
                "Set up project structure",
                "Implement core functionality",
                "Add error handling and validation",
                "Write tests",
                "Create documentation"
            ]
        
        self.logger.info(f"Generated {len(tasks)} tasks for requirement")
        return tasks


ai_pm = AIPromptManager()


async def get_current_user_from_token(authorization: str) -> dict:
    """Extract user info from authorization header."""
    # For enterprise demo, use the created enterprise user
    # In production, this would validate JWT and extract real user info
    return {
        "user_id": 1,  # Enterprise user ID
        "tenant_id": 1,  # Enterprise tenant ID
        "username": "enterprise_user",
        "roles": ["admin", "developer", "project_manager"]
    }


@app.post("/requirements", response_model=RequirementResponse)
async def create_requirement(
    req: RequirementRequest,
    db: Session = Depends(get_db),
    authorization: str = Depends(lambda: "Bearer mock-token")
):
    """Create a new requirement and break it down into tasks."""
    logger.info(f"Creating requirement: {req.requirement[:100]}...")
    
    try:
        # Get user info (simplified for MVP)
        user_info = await get_current_user_from_token(authorization)
        
        # Create requirement
        requirement = Requirement(
            tenant_id=user_info["tenant_id"],
            user_id=user_info["user_id"],
            text=req.requirement,
            status="processing"
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        
        # Break down into tasks using AI PM
        task_descriptions = ai_pm.break_down_requirement(req.requirement)
        
        # Create tasks
        tasks = []
        for i, desc in enumerate(task_descriptions):
            task = Task(
                requirement_id=requirement.id,
                description=desc,
                order_index=i,
                status="pending"
            )
            db.add(task)
            tasks.append(task)
        
        db.commit()
        
        # Update requirement status
        requirement.status = "completed"
        db.commit()
        
        logger.info(f"Created requirement {requirement.id} with {len(tasks)} tasks")
        
        return RequirementResponse(
            requirement_id=requirement.id,
            text=requirement.text,
            status=requirement.status,
            tasks=[
                TaskResponse(
                    id=task.id,
                    description=task.description,
                    status=task.status,
                    order_index=task.order_index
                ) for task in tasks
            ],
            created_at=requirement.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create requirement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process requirement"
        )


@app.get("/requirements/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: int, db: Session = Depends(get_db)):
    """Get requirement by ID."""
    logger.info(f"Fetching requirement {requirement_id}")
    
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found"
        )
    
    tasks = db.query(Task).filter(Task.requirement_id == requirement_id).order_by(Task.order_index).all()
    
    return RequirementResponse(
        requirement_id=requirement.id,
        text=requirement.text,
        status=requirement.status,
        tasks=[
            TaskResponse(
                id=task.id,
                description=task.description,
                status=task.status,
                order_index=task.order_index
            ) for task in tasks
        ],
        created_at=requirement.created_at
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Orchestrator Service on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
