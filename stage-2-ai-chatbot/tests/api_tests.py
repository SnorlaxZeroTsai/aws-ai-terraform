"""API tests for Stage 2 AI Chatbot."""

import pytest
import json
import os
from typing import Dict, Any


class TestChatAPI:
    """Test suite for the chat API."""

    @pytest.fixture
    def api_endpoint(self) -> str:
        """Get the API endpoint from environment or Terraform output."""
        endpoint = os.getenv("CHAT_API_ENDPOINT")
        if not endpoint:
            pytest.skip("CHAT_API_ENDPOINT environment variable not set")
        return endpoint

    @pytest.fixture
    def valid_request(self) -> Dict[str, Any]:
        """Valid chat request payload."""
        return {
            "message": "Hello! What can you do?"
        }

    @pytest.fixture
    def request_with_history(self) -> Dict[str, Any]:
        """Chat request with conversation history."""
        return {
            "message": "What did I just say?",
            "history": [
                {"role": "user", "content": "My name is Alice"},
                {"role": "assistant", "content": "Hello Alice!"}
            ]
        }

    @pytest.fixture
    def request_with_params(self) -> Dict[str, Any]:
        """Chat request with custom parameters."""
        return {
            "message": "Tell me a short joke.",
            "max_tokens": 100,
            "temperature": 0.9
        }

    def test_basic_request(self, api_endpoint: str, valid_request: Dict[str, Any]):
        """Test basic chat request."""
        import requests

        response = requests.post(
            api_endpoint,
            json=valid_request,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "model" in data
        assert len(data["message"]) > 0

    def test_request_with_history(self, api_endpoint: str, request_with_history: Dict[str, Any]):
        """Test chat request with conversation history."""
        import requests

        response = requests.post(
            api_endpoint,
            json=request_with_history,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Response should reference the conversation history

    def test_request_with_custom_params(self, api_endpoint: str, request_with_params: Dict[str, Any]):
        """Test chat request with custom parameters."""
        import requests

        response = requests.post(
            api_endpoint,
            json=request_with_params,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_missing_message_field(self, api_endpoint: str):
        """Test request with missing message field."""
        import requests

        response = requests.post(
            api_endpoint,
            json={},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_invalid_json(self, api_endpoint: str):
        """Test request with invalid JSON."""
        import requests

        response = requests.post(
            api_endpoint,
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422]

    def test_cors_headers(self, api_endpoint: str, valid_request: Dict[str, Any]):
        """Test CORS headers are present."""
        import requests

        response = requests.post(
            api_endpoint,
            json=valid_request,
            headers={"Content-Type": "application/json"}
        )

        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers

    def test_empty_message(self, api_endpoint: str):
        """Test request with empty message."""
        import requests

        response = requests.post(
            api_endpoint,
            json={"message": ""},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_very_long_message(self, api_endpoint: str):
        """Test request with very long message."""
        import requests

        long_message = "Tell me a story. " * 100
        response = requests.post(
            api_endpoint,
            json={"message": long_message},
            headers={"Content-Type": "application/json"}
        )

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 413]

    def test_special_characters(self, api_endpoint: str):
        """Test request with special characters."""
        import requests

        special_message = "Hello! 🎉 Test with emojis: 🚀 Also special chars: <>&\"'"
        response = requests.post(
            api_endpoint,
            json={"message": special_message},
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_concurrent_requests(self, api_endpoint: str, valid_request: Dict[str, Any]):
        """Test multiple concurrent requests."""
        import requests
        from concurrent.futures import ThreadPoolExecutor

        def make_request():
            response = requests.post(
                api_endpoint,
                json=valid_request,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(status == 200 for status in results)


class TestLambdaFunction:
    """Test Lambda function directly (local testing)."""

    @pytest.fixture
    def mock_event(self):
        """Mock API Gateway event."""
        return {
            "body": json.dumps({"message": "Hello!"}),
            "httpMethod": "POST",
            "headers": {
                "Content-Type": "application/json"
            }
        }

    @pytest.fixture
    def mock_context(self):
        """Mock Lambda context."""
        class MockContext:
            function_name = "test-chatbot"
            memory_limit_in_mb = 256
            invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
            aws_request_id = "test-request-id"

        return MockContext()

    def test_handler_import(self):
        """Test that handler can be imported."""
        try:
            from handlers.chat import handler
            assert callable(handler)
        except ImportError:
            pytest.skip("Handler module not available in test environment")

    def test_llm_service_import(self):
        """Test that LLM service can be imported."""
        try:
            from services.llm_service import LLMService
            assert LLMService is not None
        except ImportError:
            pytest.skip("LLM service module not available in test environment")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
