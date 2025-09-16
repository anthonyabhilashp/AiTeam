"""
Enterprise GitHub Integration Service
Production-ready GitHub repository management with enterprise features.
Handles repository creation, commits, pull requests, and collaboration workflows.
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import tempfile
import zipfile
from pathlib import Path

# Enterprise FastAPI (MIT License)
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Enterprise GitHub SDK (MIT License)
import httpx
from github import Github, GithubException
import git
from git import Repo, GitCommandError

# Enterprise configuration
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import Project, GitRepository

# Initialize enterprise logging
logger = setup_logger("github-integration", "github-integration.log")

app = FastAPI(title="Enterprise GitHub Integration", version="1.0.0")

# CORS middleware for enterprise integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitHub integration models
class RepositoryRequest(BaseModel):
    """Repository creation request."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    private: bool = True
    organization: Optional[str] = None
    template_repo: Optional[str] = None
    auto_init: bool = True
    gitignore_template: Optional[str] = None
    license_template: Optional[str] = None

class CommitRequest(BaseModel):
    """Commit request."""
    repo_name: str
    branch: str = "main"
    message: str
    files: Dict[str, str]  # filename -> content
    author_name: Optional[str] = None
    author_email: Optional[str] = None

class PullRequestRequest(BaseModel):
    """Pull request creation request."""
    repo_name: str
    title: str
    body: str
    head_branch: str
    base_branch: str = "main"
    draft: bool = False

class RepositoryInfo(BaseModel):
    """Repository information."""
    id: int
    name: str
    full_name: str
    description: str
    private: bool
    clone_url: str
    ssh_url: str
    html_url: str
    default_branch: str
    created_at: datetime
    updated_at: datetime

class CommitInfo(BaseModel):
    """Commit information."""
    sha: str
    message: str
    author: str
    author_email: str
    committed_at: datetime
    url: str

# Enterprise GitHub Manager
class EnterpriseGitHubManager:
    """Production-ready GitHub integration with enterprise features."""
    
    def __init__(self):
        self.logger = logger
        self.github_client: Optional[Github] = None
        self.personal_access_token = None
        self.organization = None
        
    def initialize(self, token: str, organization: Optional[str] = None):
        """Initialize GitHub client with credentials."""
        try:
            self.personal_access_token = token
            self.organization = organization
            self.github_client = Github(token)
            
            # Test connection
            user = self.github_client.get_user()
            self.logger.info(f"GitHub client initialized for user: {user.login}")
            
            return True
            
        except GithubException as e:
            self.logger.error(f"Failed to initialize GitHub client: {e}")
            return False
    
    async def create_repository(self, request: RepositoryRequest) -> Dict[str, Any]:
        """Create GitHub repository with enterprise configuration."""
        try:
            if not self.github_client:
                raise ValueError("GitHub client not initialized")
            
            # Determine where to create repository
            if request.organization and self.organization:
                # Create in organization
                org = self.github_client.get_organization(self.organization)
                repo = org.create_repo(
                    name=request.name,
                    description=request.description,
                    private=request.private,
                    auto_init=request.auto_init,
                    gitignore_template=request.gitignore_template,
                    license_template=request.license_template
                )
            else:
                # Create in personal account
                user = self.github_client.get_user()
                repo = user.create_repo(
                    name=request.name,
                    description=request.description,
                    private=request.private,
                    auto_init=request.auto_init,
                    gitignore_template=request.gitignore_template,
                    license_template=request.license_template
                )
            
            # Configure repository settings
            await self._configure_repository_settings(repo)
            
            repo_info = {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "html_url": repo.html_url,
                "default_branch": repo.default_branch,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at
            }
            
            self.logger.info(f"Repository created: {repo.full_name}")
            return repo_info
            
        except GithubException as e:
            self.logger.error(f"Failed to create repository: {e}")
            raise
    
    async def _configure_repository_settings(self, repo):
        """Configure enterprise repository settings."""
        try:
            # Enable security features
            repo.edit(
                has_issues=True,
                has_projects=True,
                has_wiki=False,  # Disable wiki for security
                allow_squash_merge=True,
                allow_merge_commit=False,
                allow_rebase_merge=True,
                delete_branch_on_merge=True
            )
            
            # Set up branch protection for main branch
            try:
                main_branch = repo.get_branch(repo.default_branch)
                main_branch.edit_protection(
                    strict=True,
                    contexts=[],
                    enforce_admins=True,
                    dismiss_stale_reviews=True,
                    require_code_owner_reviews=False,
                    required_approving_review_count=1
                )
                self.logger.info(f"Branch protection enabled for {repo.full_name}")
            except GithubException as e:
                self.logger.warning(f"Could not set branch protection: {e}")
            
        except Exception as e:
            self.logger.warning(f"Could not configure all repository settings: {e}")
    
    async def commit_files(self, request: CommitRequest) -> Dict[str, Any]:
        """Commit files to repository."""
        try:
            if not self.github_client:
                raise ValueError("GitHub client not initialized")
            
            # Get repository
            if self.organization:
                repo_full_name = f"{self.organization}/{request.repo_name}"
            else:
                user = self.github_client.get_user()
                repo_full_name = f"{user.login}/{request.repo_name}"
            
            repo = self.github_client.get_repo(repo_full_name)
            
            # Get current commit SHA for branch
            try:
                branch_ref = repo.get_git_ref(f"heads/{request.branch}")
                base_sha = branch_ref.object.sha
            except GithubException:
                # Branch doesn't exist, create it from default branch
                default_branch = repo.get_branch(repo.default_branch)
                base_sha = default_branch.commit.sha
                repo.create_git_ref(f"refs/heads/{request.branch}", base_sha)
            
            # Create blobs for all files
            blobs = []
            for file_path, content in request.files.items():
                blob = repo.create_git_blob(content, "utf-8")
                blobs.append({
                    "path": file_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob.sha
                })
            
            # Create tree
            base_tree = repo.get_git_tree(base_sha)
            tree = repo.create_git_tree(blobs, base_tree)
            
            # Create commit
            author_name = request.author_name or "AI Generator"
            author_email = request.author_email or "ai@enterprise.com"
            
            commit = repo.create_git_commit(
                message=request.message,
                tree=tree,
                parents=[repo.get_git_commit(base_sha)],
                author={"name": author_name, "email": author_email},
                committer={"name": author_name, "email": author_email}
            )
            
            # Update branch reference
            branch_ref = repo.get_git_ref(f"heads/{request.branch}")
            branch_ref.edit(commit.sha)
            
            commit_info = {
                "sha": commit.sha,
                "message": commit.message,
                "author": author_name,
                "author_email": author_email,
                "committed_at": datetime.utcnow(),
                "url": f"{repo.html_url}/commit/{commit.sha}"
            }
            
            self.logger.info(f"Files committed to {repo_full_name}:{request.branch}")
            return commit_info
            
        except GithubException as e:
            self.logger.error(f"Failed to commit files: {e}")
            raise
    
    async def create_pull_request(self, request: PullRequestRequest) -> Dict[str, Any]:
        """Create pull request."""
        try:
            if not self.github_client:
                raise ValueError("GitHub client not initialized")
            
            # Get repository
            if self.organization:
                repo_full_name = f"{self.organization}/{request.repo_name}"
            else:
                user = self.github_client.get_user()
                repo_full_name = f"{user.login}/{request.repo_name}"
            
            repo = self.github_client.get_repo(repo_full_name)
            
            # Create pull request
            pr = repo.create_pull(
                title=request.title,
                body=request.body,
                head=request.head_branch,
                base=request.base_branch,
                draft=request.draft
            )
            
            # Add labels for AI-generated content
            try:
                repo.get_label("ai-generated")
            except GithubException:
                # Create label if it doesn't exist
                repo.create_label("ai-generated", "00ff00", "Code generated by AI")
            
            pr.add_to_labels("ai-generated")
            
            pr_info = {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "html_url": pr.html_url,
                "head_branch": pr.head.ref,
                "base_branch": pr.base.ref,
                "created_at": pr.created_at,
                "updated_at": pr.updated_at
            }
            
            self.logger.info(f"Pull request created: {repo_full_name}#{pr.number}")
            return pr_info
            
        except GithubException as e:
            self.logger.error(f"Failed to create pull request: {e}")
            raise
    
    async def clone_repository(self, repo_name: str, local_path: str, branch: str = None) -> str:
        """Clone repository to local path."""
        try:
            if self.organization:
                repo_full_name = f"{self.organization}/{repo_name}"
            else:
                user = self.github_client.get_user()
                repo_full_name = f"{user.login}/{repo_name}"
            
            repo = self.github_client.get_repo(repo_full_name)
            clone_url = repo.clone_url
            
            # Add authentication to clone URL
            if self.personal_access_token:
                clone_url = clone_url.replace(
                    "https://github.com/",
                    f"https://{self.personal_access_token}@github.com/"
                )
            
            # Clone repository
            cloned_repo = Repo.clone_from(clone_url, local_path)
            
            # Checkout specific branch if specified
            if branch and branch != repo.default_branch:
                cloned_repo.git.checkout(branch)
            
            self.logger.info(f"Repository cloned to {local_path}")
            return local_path
            
        except (GithubException, GitCommandError) as e:
            self.logger.error(f"Failed to clone repository: {e}")
            raise
    
    async def upload_project_to_github(self, project_path: str, repo_name: str, 
                                     description: str = "") -> Dict[str, Any]:
        """Upload entire project to GitHub repository."""
        try:
            # Create repository
            repo_request = RepositoryRequest(
                name=repo_name,
                description=description,
                private=True,
                auto_init=False
            )
            repo_info = await self.create_repository(repo_request)
            
            # Prepare files from project directory
            files = {}
            project_root = Path(project_path)
            
            for file_path in project_root.rglob("*"):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    relative_path = file_path.relative_to(project_root)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            files[str(relative_path)] = f.read()
                    except UnicodeDecodeError:
                        # Skip binary files
                        continue
            
            # Commit files
            commit_request = CommitRequest(
                repo_name=repo_name,
                branch="main",
                message="Initial commit: AI-generated project",
                files=files,
                author_name="AI Generator",
                author_email="ai@enterprise.com"
            )
            
            commit_info = await self.commit_files(commit_request)
            
            # Add project README if not exists
            if "README.md" not in files:
                readme_content = self._generate_readme(repo_name, description)
                readme_commit = CommitRequest(
                    repo_name=repo_name,
                    branch="main",
                    message="Add AI-generated README",
                    files={"README.md": readme_content}
                )
                await self.commit_files(readme_commit)
            
            result = {
                **repo_info,
                "initial_commit": commit_info,
                "files_uploaded": len(files)
            }
            
            self.logger.info(f"Project uploaded to GitHub: {repo_info['html_url']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to upload project to GitHub: {e}")
            raise
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored during upload."""
        ignore_patterns = [
            ".git", "__pycache__", "node_modules", ".env", ".venv",
            ".DS_Store", "*.pyc", "*.pyo", "*.pyd", ".pytest_cache",
            "*.log", ".idea", ".vscode", "dist", "build"
        ]
        
        for pattern in ignore_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    def _generate_readme(self, repo_name: str, description: str) -> str:
        """Generate AI project README."""
        return f"""# {repo_name}

{description}

## 🤖 AI-Generated Project

This project was automatically generated using an enterprise AI software generator.

## Features

- Production-ready code structure
- Comprehensive testing
- Security best practices
- Enterprise compliance
- Automated documentation

## Getting Started

### Prerequisites

- [List prerequisites based on project type]

### Installation

```bash
# Clone the repository
git clone https://github.com/{self.organization or 'user'}/{repo_name}.git
cd {repo_name}

# Install dependencies
# [Add installation commands]
```

### Usage

```bash
# [Add usage examples]
```

## Testing

```bash
# [Add testing commands]
```

## Deployment

```bash
# [Add deployment instructions]
```

## Contributing

This project follows enterprise development standards. Please ensure all contributions:

- Include comprehensive tests
- Follow security guidelines
- Maintain code quality standards
- Include proper documentation

## License

[Add appropriate license]

---

*Generated by Enterprise AI Software Generator on {datetime.utcnow().strftime('%Y-%m-%d')}*
"""

# Global GitHub manager
github_manager = EnterpriseGitHubManager()

# API Endpoints
@app.post("/github/initialize")
async def initialize_github(token: str = Form(...), organization: str = Form(None)):
    """Initialize GitHub integration with credentials."""
    try:
        success = github_manager.initialize(token, organization)
        if success:
            return {"message": "GitHub integration initialized successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to initialize GitHub client")
        
    except Exception as e:
        logger.error(f"Failed to initialize GitHub: {e}")
        raise HTTPException(status_code=500, detail=f"Initialization failed: {e}")

@app.post("/github/repositories", response_model=RepositoryInfo)
async def create_repository(request: RepositoryRequest, db: Session = Depends(get_db)):
    """Create GitHub repository."""
    try:
        repo_info = await github_manager.create_repository(request)
        
        # Store repository record
        git_repo = GitRepository(
            github_id=repo_info["id"],
            name=repo_info["name"],
            full_name=repo_info["full_name"],
            clone_url=repo_info["clone_url"],
            html_url=repo_info["html_url"],
            private=repo_info["private"],
            created_at=datetime.utcnow()
        )
        db.add(git_repo)
        db.commit()
        
        return RepositoryInfo(**repo_info)
        
    except Exception as e:
        logger.error(f"Failed to create repository: {e}")
        raise HTTPException(status_code=500, detail=f"Repository creation failed: {e}")

@app.post("/github/repositories/{repo_name}/commits", response_model=CommitInfo)
async def commit_files(repo_name: str, request: CommitRequest):
    """Commit files to repository."""
    try:
        request.repo_name = repo_name
        commit_info = await github_manager.commit_files(request)
        return CommitInfo(**commit_info)
        
    except Exception as e:
        logger.error(f"Failed to commit files: {e}")
        raise HTTPException(status_code=500, detail=f"Commit failed: {e}")

@app.post("/github/repositories/{repo_name}/pull-requests")
async def create_pull_request(repo_name: str, request: PullRequestRequest):
    """Create pull request."""
    try:
        request.repo_name = repo_name
        pr_info = await github_manager.create_pull_request(request)
        return pr_info
        
    except Exception as e:
        logger.error(f"Failed to create pull request: {e}")
        raise HTTPException(status_code=500, detail=f"Pull request creation failed: {e}")

@app.post("/github/upload-project")
async def upload_project(
    project_path: str = Form(...),
    repo_name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    """Upload entire project to GitHub."""
    try:
        result = await github_manager.upload_project_to_github(
            project_path, repo_name, description
        )
        
        # Store repository record
        git_repo = GitRepository(
            github_id=result["id"],
            name=result["name"],
            full_name=result["full_name"],
            clone_url=result["clone_url"],
            html_url=result["html_url"],
            private=result["private"],
            created_at=datetime.utcnow()
        )
        db.add(git_repo)
        db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to upload project: {e}")
        raise HTTPException(status_code=500, detail=f"Project upload failed: {e}")

@app.get("/github/repositories")
async def list_repositories():
    """List GitHub repositories."""
    try:
        if not github_manager.github_client:
            raise HTTPException(status_code=400, detail="GitHub client not initialized")
        
        user = github_manager.github_client.get_user()
        repos = []
        
        for repo in user.get_repos():
            repos.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "html_url": repo.html_url,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at
            })
        
        return {"repositories": repos}
        
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "github-integration",
        "timestamp": datetime.utcnow().isoformat(),
        "github_initialized": github_manager.github_client is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
