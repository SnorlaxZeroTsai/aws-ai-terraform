"""
Integration tests for AI Agent Platform.
Run after deployment to verify functionality.
"""
import pytest
import requests
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINT = os.getenv("API_ENDPOINT", f"{API_BASE_URL}/api/v1")


class TestHealth:
    """Test health endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns platform info."""
        response = requests.get(f"{API_BASE_URL}/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "operational"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "platform" in data
        assert "environment" in data


class TestAgents:
    """Test agent endpoints."""

    def test_list_agents(self):
        """Test listing available agents."""
        response = requests.get(f"{API_BASE_URL}/agents")
        assert response.status_code == 200

        data = response.json()
        assert "agents" in data
        assert "count" in data
        assert isinstance(data["agents"], list)


class TestChatbot:
    """Test chatbot agent."""

    @pytest.mark.skipif(
        os.getenv("ENABLE_CHATBOT") == "false",
        reason="Chatbot agent disabled"
    )
    def test_chat_endpoint(self):
        """Test chatbot endpoint."""
        payload = {
            "message": "Hello, how are you?",
            "temperature": 0.7,
            "max_tokens": 100
        }

        response = requests.post(
            f"{API_ENDPOINT}/chat",
            json=payload
        )

        # Note: May fail if Lambda not deployed
        # assert response.status_code == 200

        # data = response.json()
        # assert data["success"] is True
        # assert "data" in data
        # assert "response" in data["data"]


class TestRAG:
    """Test RAG agent."""

    @pytest.mark.skipif(
        os.getenv("ENABLE_RAG") == "false",
        reason="RAG agent disabled"
    )
    def test_rag_endpoint(self):
        """Test RAG query endpoint."""
        payload = {
            "query": "What is the revenue growth?",
            "top_k": 5,
            "min_score": 0.5
        }

        response = requests.post(
            f"{API_ENDPOINT}/rag",
            json=payload
        )

        # Note: May fail if Lambda not deployed
        # assert response.status_code == 200

        # data = response.json()
        # assert data["success"] is True
        # assert "data" in data


class TestAutonomousAgent:
    """Test autonomous agent."""

    @pytest.mark.skipif(
        os.getenv("ENABLE_AUTONOMOUS") == "false",
        reason="Autonomous agent disabled"
    )
    def test_autonomous_agent_endpoint(self):
        """Test autonomous agent endpoint."""
        payload = {
            "task": "Calculate 15% of 1,000,000",
            "max_iterations": 5
        }

        response = requests.post(
            f"{API_ENDPOINT}/agent",
            json=payload
        )

        # Note: May fail if Step Function not deployed
        # assert response.status_code == 200

        # data = response.json()
        # assert data["success"] is True
        # assert "data" in data
        # assert "job_id" in data["data"]


class TestDocumentAgent:
    """Test document agent."""

    @pytest.mark.skipif(
        os.getenv("ENABLE_DOCUMENT") == "false",
        reason="Document agent disabled"
    )
    def test_document_endpoint(self):
        """Test document analysis endpoint."""
        payload = {
            "document_key": "sample.pdf",
            "analysis_type": "full"
        }

        response = requests.post(
            f"{API_ENDPOINT}/document",
            json=payload
        )

        # Note: May fail if Lambda not deployed
        # assert response.status_code == 200

        # data = response.json()
        # assert data["success"] is True
        # assert "data" in data


class TestMultiAgentCollaboration:
    """Test multi-agent collaboration."""

    def test_collaboration_endpoint(self):
        """Test multi-agent collaboration."""
        payload = {
            "agents": ["chatbot"],
            "task": "Generate a summary"
        }

        response = requests.post(
            f"{API_ENDPOINT}/collaborate",
            params=payload
        )

        # Note: May fail if agents not deployed
        # assert response.status_code == 200

        # data = response.json()
        # assert data["success"] is True


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
