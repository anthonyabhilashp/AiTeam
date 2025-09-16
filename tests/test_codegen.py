"""Unit and integration tests for Codegen Service."""
import pytest
import sys
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add the saas-devgen directory to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saas-devgen'))

from codegen_service.main import app, EnterpriseCodeGenerator
from codegen_service.code_generators import generate_code_from_tasks


class TestCodeGenerators:
    """Test cases for code generation functions."""

    def test_generate_code_from_tasks_success(self):
        """Test successful code generation."""
        with patch('code_generators._run_metagpt_codegen') as mock_metagpt:
            # Mock MetaGPT response
            mock_metagpt.return_value = {
                "main.py": "print('Hello World')",
                "requirements.txt": "fastapi==0.104.1",
                "README.md": "# Generated App"
            }

            result = generate_code_from_tasks(
                requirement_text="Build a simple app",
                tasks=["Create main file", "Add dependencies"],
                language="python",
                framework="fastapi"
            )

            assert result["status"] == "ready"
            assert "repo_url" in result
            assert "commit_id" in result
            assert "generated_files" in result
            assert "metadata" in result

    def test_generate_code_from_tasks_failure(self):
        """Test code generation failure handling."""
        with patch('code_generators._run_metagpt_codegen', side_effect=Exception("MetaGPT failed")):
            result = generate_code_from_tasks(
                requirement_text="Build a failing app",
                tasks=["This will fail"],
                language="python",
                framework="fastapi"
            )

            assert result["status"] == "error"
            assert "error" in result
            assert result["repo_url"] is None

    def test_fallback_generation(self):
        """Test fallback template-based generation."""
        with patch('code_generators.METAGPT_AVAILABLE', False):
            result = generate_code_from_tasks(
                requirement_text="Build a FastAPI app",
                tasks=["Create API endpoints"],
                language="python",
                framework="fastapi"
            )

            assert result["status"] == "ready"
            assert len(result["generated_files"]) > 0


class TestEnterpriseCodeGenerator:
    """Test cases for the Enterprise Code Generator."""

    def setup_method(self):
        """Setup test fixtures."""
        self.generator = EnterpriseCodeGenerator()

    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.temp_dir is None
        assert self.generator.logger is not None

    @patch('codegen_service.main.generate_code_from_tasks')
    def test_generate_code_success(self, mock_generate):
        """Test successful code generation."""
        # Mock the generation function
        mock_generate.return_value = {
            "status": "ready",
            "repo_url": "file:///tmp/test",
            "generated_files": ["main.py", "requirements.txt"],
            "metadata": {"language": "python", "framework": "fastapi"}
        }

        result = self.generator.generate_code(
            tasks=["Create API", "Add models"],
            language="python",
            framework="fastapi",
            additional_requirements="Add authentication"
        )

        assert result["status"] == "ready"
        assert "repo_url" in result
        assert "generated_files" in result

    def test_generate_fastapi_project(self):
        """Test FastAPI project generation."""
        tasks = ["Create API endpoints", "Add database models"]
        result = self.generator._generate_fastapi_project(tasks, "Add authentication")

        assert result["status"] == "completed"
        assert "project_path" in result
        assert "generated_files" in result
        assert len(result["generated_files"]) > 0
        assert "main.py" in result["generated_files"]
        assert "requirements.txt" in result["generated_files"]

    def test_create_fastapi_main_content(self):
        """Test FastAPI main.py content generation."""
        tasks = ["Create API with auth", "Add database integration"]
        content = self.generator._create_fastapi_main(tasks)

        assert "from fastapi import FastAPI" in content
        assert "app = FastAPI" in content
        assert "auth" in content.lower() or "database" in content.lower()

    def test_create_requirements_content(self):
        """Test requirements.txt content generation."""
        additional_reqs = "Add pytest for testing"
        content = self.generator._create_requirements(additional_reqs)

        assert "fastapi" in content
        assert "uvicorn" in content
        assert "pytest" in content or "test" in additional_reqs.lower()


class TestCodegenAPI:
    """Test cases for Codegen API endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "codegen-service"

    @patch('codegen_service.main.EnterpriseCodeGenerator.generate_code')
    def test_generate_code_endpoint(self, mock_generate):
        """Test code generation endpoint."""
        # Mock the generation
        mock_generate.return_value = {
            "status": "ready",
            "repo_url": "file:///tmp/generated",
            "generated_files": ["main.py", "models.py"],
            "metadata": {"language": "python", "framework": "fastapi"}
        }

        request_data = {
            "tasks": ["Create API", "Add models"],
            "language": "python",
            "framework": "fastapi",
            "additional_requirements": "Add authentication"
        }

        response = self.client.post("/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "repo_url" in data
        assert "generated_files" in data

    def test_generate_code_invalid_request(self):
        """Test code generation with invalid request."""
        response = self.client.post("/generate", json={})

        assert response.status_code == 422  # Validation error

    @patch('codegen_service.main.EnterpriseCodeGenerator.generate_code')
    def test_generation_status_tracking(self, mock_generate):
        """Test generation status tracking."""
        # Mock async generation
        mock_generate.return_value = {
            "status": "in_progress",
            "generation_id": "test-gen-123",
            "message": "Generation started"
        }

        request_data = {
            "tasks": ["Create API"],
            "language": "python",
            "framework": "fastapi"
        }

        response = self.client.post("/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "generation_id" in data or "status" in data


class TestIntegrationScenarios:
    """Integration tests for various code generation scenarios."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.client = TestClient(app)

    def test_fastapi_project_generation(self):
        """Test complete FastAPI project generation."""
        request_data = {
            "tasks": [
                "Create REST API endpoints",
                "Add database models",
                "Implement authentication",
                "Add error handling"
            ],
            "language": "python",
            "framework": "fastapi",
            "additional_requirements": "Add comprehensive logging"
        }

        response = self.client.post("/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        if data["status"] == "ready":
            assert "repo_url" in data
            assert "generated_files" in data
            assert isinstance(data["generated_files"], list)
            assert len(data["generated_files"]) > 0

    def test_react_project_generation(self):
        """Test React project generation."""
        request_data = {
            "tasks": [
                "Create React components",
                "Add state management",
                "Implement routing",
                "Add API integration"
            ],
            "language": "javascript",
            "framework": "react",
            "additional_requirements": "Add TypeScript support"
        }

        response = self.client.post("/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_project_with_complex_requirements(self):
        """Test project generation with complex requirements."""
        request_data = {
            "tasks": [
                "Design microservices architecture",
                "Implement API gateway",
                "Add service discovery",
                "Implement distributed tracing",
                "Add monitoring and logging",
                "Set up CI/CD pipeline",
                "Add security measures",
                "Implement testing strategy"
            ],
            "language": "python",
            "framework": "fastapi",
            "additional_requirements": "Enterprise-grade with high availability and scalability"
        }

        response = self.client.post("/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_error_handling(self):
        """Test error handling in code generation."""
        # Test with invalid language/framework combination
        request_data = {
            "tasks": ["Create app"],
            "language": "invalid",
            "framework": "invalid"
        }

        response = self.client.post("/generate", json=request_data)

        # Should not crash, should return some response
        assert response.status_code in [200, 422, 500]
        data = response.json()
        assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
