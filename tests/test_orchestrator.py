"""Unit and integration tests for Orchestrator Service."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add the saas-devgen directory to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saas-devgen'))

from orchestrator.main import app, AIPromptManager
from shared.models import Requirement, Task


class TestAIPromptManager:
    """Test cases for AI-powered requirement breakdown."""

    def setup_method(self):
        """Setup test fixtures."""
        self.ai_pm = AIPromptManager()

    @patch.dict(os.environ, {
        "AI_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key"
    })
    @patch('orchestrator.main.openai.OpenAI')
    def test_openai_breakdown(self, mock_openai_class):
        """Test OpenAI-powered requirement breakdown."""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '["Task 1", "Task 2", "Task 3"]'
        mock_client.chat.completions.create.return_value = mock_response

        # Test the breakdown
        tasks = self.ai_pm.break_down_requirement("Build a web app")

        assert len(tasks) == 3
        assert "Task 1" in tasks
        assert "Task 2" in tasks
        assert "Task 3" in tasks

    @patch.dict(os.environ, {
        "AI_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "test-key"
    })
    @patch('orchestrator.main.anthropic.Anthropic')
    def test_anthropic_breakdown(self, mock_anthropic_class):
        """Test Anthropic-powered requirement breakdown."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock the response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '["Task A", "Task B"]'
        mock_client.messages.create.return_value = mock_response

        # Test the breakdown
        tasks = self.ai_pm.break_down_requirement("Create an API")

        assert len(tasks) == 2
        assert "Task A" in tasks
        assert "Task B" in tasks

    def test_rule_based_fallback(self):
        """Test rule-based breakdown when AI is not available."""
        # Test with no AI provider configured
        with patch.dict(os.environ, {}, clear=True):
            tasks = self.ai_pm.break_down_requirement("Build API with database")

            assert len(tasks) > 0
            assert any("API" in task.lower() for task in tasks)
            assert any("database" in task.lower() for task in tasks)


class TestOrchestratorAPI:
    """Test cases for Orchestrator API endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "orchestrator"

    @patch('orchestrator.main.get_db')
    @patch('orchestrator.main.get_current_user_from_token')
    def test_create_requirement_success(self, mock_get_user, mock_get_db):
        """Test successful requirement creation."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user
        mock_get_user.return_value = {
            "user_id": 1,
            "tenant_id": 1,
            "username": "test_user",
            "roles": ["developer"]
        }

        # Mock database operations
        mock_requirement = Mock()
        mock_requirement.id = 1
        mock_requirement.text = "Test requirement"
        mock_requirement.status = "processing"
        mock_requirement.created_at = "2024-01-01T00:00:00"

        mock_task = Mock()
        mock_task.id = 1
        mock_task.description = "Test task"
        mock_task.status = "pending"
        mock_task.order_index = 0

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_requirement
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_task]

        # Test the endpoint
        response = self.client.post(
            "/requirements",
            json={"requirement": "Build a test app"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requirement_id"] == 1
        assert data["text"] == "Test requirement"
        assert len(data["tasks"]) == 1

    def test_create_requirement_invalid_data(self):
        """Test requirement creation with invalid data."""
        response = self.client.post(
            "/requirements",
            json={},  # Missing requirement field
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 422  # Validation error

    @patch('orchestrator.main.get_db')
    def test_get_requirement_not_found(self, mock_get_db):
        """Test getting a non-existent requirement."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get("/requirements/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestIntegrationWorkflow:
    """Integration tests for the complete orchestrator workflow."""

    def setup_method(self):
        """Setup integration test fixtures."""
        self.client = TestClient(app)

    @patch('orchestrator.main.get_db')
    @patch('orchestrator.main.get_current_user_from_token')
    @patch('orchestrator.main.AIPromptManager.break_down_requirement')
    def test_full_requirement_workflow(self, mock_breakdown, mock_get_user, mock_get_db):
        """Test the complete requirement creation and task breakdown workflow."""
        # Mock AI breakdown
        mock_breakdown.return_value = [
            "Design system architecture",
            "Set up project structure",
            "Implement core functionality",
            "Add testing framework",
            "Deploy to production"
        ]

        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user
        mock_get_user.return_value = {
            "user_id": 1,
            "tenant_id": 1,
            "username": "test_user",
            "roles": ["developer"]
        }

        # Mock database objects
        mock_requirement = Mock()
        mock_requirement.id = 1
        mock_requirement.text = "Build a web application"
        mock_requirement.status = "completed"
        mock_requirement.created_at = "2024-01-01T00:00:00"

        mock_tasks = []
        for i, desc in enumerate(mock_breakdown.return_value):
            mock_task = Mock()
            mock_task.id = i + 1
            mock_task.description = desc
            mock_task.status = "pending"
            mock_task.order_index = i
            mock_tasks.append(mock_task)

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_requirement
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_tasks

        # Test the workflow
        response = self.client.post(
            "/requirements",
            json={"requirement": "Build a web application"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify the response structure
        assert "requirement_id" in data
        assert "text" in data
        assert "status" in data
        assert "tasks" in data
        assert "created_at" in data

        # Verify tasks were created
        assert len(data["tasks"]) == 5
        for task in data["tasks"]:
            assert "id" in task
            assert "description" in task
            assert "status" in task
            assert "order_index" in task

        # Verify AI breakdown was called
        mock_breakdown.assert_called_once_with("Build a web application")


if __name__ == "__main__":
    pytest.main([__file__])
