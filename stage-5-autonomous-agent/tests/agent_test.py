"""Tests for the autonomous agent.

These tests verify the agent's core functionality including:
- ReAct loop execution
- Tool calling
- Memory management
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent.core import Agent
from agent.memory import MemorySystem
from agent.reasoning import ReasoningEngine
from tools.registry import ToolRegistry
from tools.implementations.search_tool import WebSearchTool
from tools.implementations.file_tool import ReadFileTool


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock client."""
    client = Mock()
    response = Mock()
    response['body'].read.return_value = b'{"content": [{"text": "Test response"}]}'
    client.invoke_model.return_value = response
    return client


@pytest.fixture
def mock_dynamodb_client():
    """Mock DynamoDB client."""
    client = Mock()
    client.query.return_value = {'Items': []}
    client.put_item.return_value = {}
    return client


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    client = Mock()
    client.list_objects_v2.return_value = {'Contents': []}
    return client


@pytest.fixture
def agent(mock_bedrock_client, mock_dynamodb_client, mock_s3_client):
    """Create an agent instance with mocked clients."""
    with patch.dict('os.environ', {
        'CONVERSATION_TABLE': 'test-conversation',
        'EPISODIC_TABLE': 'test-episodic',
        'SEMANTIC_TABLE': 'test-semantic',
        'TOOL_BUCKET': 'test-tools',
        'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'MAX_ITERATIONS': '3'
    }):
        return Agent(
            bedrock_client=mock_bedrock_client,
            dynamodb_client=mock_dynamodb_client,
            s3_client=mock_s3_client
        )


class TestAgentCore:
    """Test cases for Agent core functionality."""

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.conversation_table == 'test-conversation'
        assert agent.episodic_table == 'test-episodic'
        assert agent.semantic_table == 'test-semantic'
        assert agent.tool_bucket == 'test-tools'
        assert agent.max_iterations == 3

    def test_run_with_session_id(self, agent, mock_bedrock_client):
        """Test agent run with provided session ID."""
        # Mock reasoning response
        mock_bedrock_client.invoke_model.return_value = Mock(
            body=Mock(
                read=Mock(
                    return_value=b'{"content": [{"text": "Thought: Test\\nAction: {\\"type\\": \\"respond\\"}"}]}'
                )
            )
        )

        result = agent.run("Test query", session_id="test-session")

        assert result['status'] == 'success'
        assert result['session_id'] == 'test-session'
        assert 'response' in result

    def test_run_generates_session_id(self, agent, mock_bedrock_client):
        """Test agent run generates session ID if not provided."""
        mock_bedrock_client.invoke_model.return_value = Mock(
            body=Mock(
                read=Mock(
                    return_value=b'{"content": [{"text": "Action: {\\"type\\": \\"respond\\"}"}]}'
                )
            )
        )

        result = agent.run("Test query")

        assert result['status'] == 'success'
        assert result['session_id'].startswith('session_')

    def test_max_iterations(self, agent, mock_bedrock_client):
        """Test agent respects max iterations."""
        # Always return tool action to trigger iteration limit
        mock_bedrock_client.invoke_model.return_value = Mock(
            body=Mock(
                read=Mock(
                    return_value=b'{"content": [{"text": "Action: {\\"type\\": \\"tool\\", \\"tool\\": \\"search\\"}"}]}'
                )
            )
        )

        result = agent.run("Test query")

        assert result['status'] == 'max_iterations'
        assert result['iterations'] == 3

    def test_tool_execution(self, agent):
        """Test tool execution."""
        result = agent._execute_tool('web_search', {'query': 'test'})

        assert result['tool'] == 'web_search'
        assert 'parameters' in result
        assert 'timestamp' in result

    def test_memory_retrieval(self, agent, mock_dynamodb_client):
        """Test memory retrieval."""
        mock_dynamodb_client.query.return_value = {
            'Items': [
                {'role': {'S': 'user'}, 'content': {'S': 'Hello'}}
            ]
        }

        memory = agent._retrieve_memory('test-session')

        assert 'conversation' in memory
        assert 'tool_results' in memory
        assert 'learned_patterns' in memory

    def test_memory_storage(self, agent, mock_dynamodb_client):
        """Test memory storage."""
        context = {
            'query': 'Test query',
            'response': 'Test response',
            'iteration': 1
        }

        agent._store_memory('test-session', context)

        mock_dynamodb_client.put_item.assert_called_once()


class TestMemorySystem:
    """Test cases for Memory system."""

    @pytest.fixture
    def memory_system(self, mock_dynamodb_client):
        """Create a memory system instance."""
        with patch.dict('os.environ', {
            'CONVERSATION_TABLE': 'test-conversation',
            'EPISODIC_TABLE': 'test-episodic',
            'SEMANTIC_TABLE': 'test-semantic'
        }):
            return MemorySystem(dynamodb_client=mock_dynamodb_client)

    def test_store_conversation(self, memory_system, mock_dynamodb_client):
        """Test storing conversation."""
        memory_system.store_conversation(
            'test-session',
            'user',
            'Hello'
        )

        mock_dynamodb_client.put_item.assert_called_once()

    def test_get_conversation_history(self, memory_system, mock_dynamodb_client):
        """Test retrieving conversation history."""
        mock_dynamodb_client.query.return_value = {
            'Items': [
                {'role': {'S': 'user'}, 'content': {'S': 'Hello'}}
            ]
        }

        history = memory_system.get_conversation_history('test-session')

        assert len(history) == 1
        assert history[0]['role'] == 'user'

    def test_store_episode(self, memory_system, mock_dynamodb_client):
        """Test storing episodic memory."""
        memory_system.store_episode(
            'episode-1',
            'test-session',
            'tool_result',
            {'result': 'data'}
        )

        mock_dynamodb_client.put_item.assert_called_once()

    def test_store_semantic_memory(self, memory_system, mock_dynamodb_client):
        """Test storing semantic memory."""
        memory_system.store_semantic_memory(
            'memory-1',
            'concept',
            {'knowledge': 'data'},
            0.9
        )

        mock_dynamodb_client.put_item.assert_called_once()


class TestReasoningEngine:
    """Test cases for Reasoning Engine."""

    @pytest.fixture
    def reasoning_engine(self, mock_bedrock_client):
        """Create a reasoning engine instance."""
        with patch.dict('os.environ', {
            'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0'
        }):
            return ReasoningEngine(bedrock_client=mock_bedrock_client)

    def test_reason_returns_action(self, reasoning_engine, mock_bedrock_client):
        """Test reasoning returns an action."""
        mock_bedrock_client.invoke_model.return_value = Mock(
            body=Mock(
                read=Mock(
                    return_value=b'{"content": [{"text": "Thought: Test\\nAction: {\\"type\\": \\"respond\\"}\\nConfidence: 0.8"}]}'
                )
            )
        )

        result = reasoning_engine.reason(
            'Test query',
            {},
            []
        )

        assert 'reasoning_chain' in result
        assert 'action' in result
        assert 'confidence' in result

    def test_reason_with_tools(self, reasoning_engine, mock_bedrock_client):
        """Test reasoning considers available tools."""
        mock_bedrock_client.invoke_model.return_value = Mock(
            body=Mock(
                read=Mock(
                    return_value=b'{"content": [{"text": "Action: {\\"type\\": \\"tool\\", \\"tool\\": \\"web_search\\"}"}]}'
                )
            )
        )

        tools = [
            {
                'name': 'web_search',
                'description': 'Search the web'
            }
        ]

        result = reasoning_engine.reason('Search for news', {}, tools)

        assert result['action']['type'] == 'tool'
        assert result['action']['tool'] == 'web_search'


class TestToolRegistry:
    """Test cases for Tool Registry."""

    @pytest.fixture
    def registry(self, mock_s3_client):
        """Create a tool registry instance."""
        with patch.dict('os.environ', {
            'TOOL_BUCKET': 'test-tools'
        }):
            return ToolRegistry(s3_client=mock_s3_client)

    def test_register_tool(self, registry):
        """Test registering a tool."""
        tool = WebSearchTool()
        registry.register_tool(tool)

        assert 'web_search' in registry._tools
        assert registry.get_tool('web_search') == tool

    def test_list_tools(self, registry):
        """Test listing tools."""
        tool1 = WebSearchTool()
        tool2 = ReadFileTool()
        registry.register_tool(tool1)
        registry.register_tool(tool2)

        tools = registry.list_tools()

        assert 'web_search' in tools
        assert 'read_file' in tools

    def test_execute_tool_success(self, registry):
        """Test successful tool execution."""
        tool = WebSearchTool()
        registry.register_tool(tool)

        result = registry.execute_tool('web_search', {'query': 'test'})

        assert result.success is True
        assert result.data is not None

    def test_execute_tool_not_found(self, registry):
        """Test executing non-existent tool."""
        result = registry.execute_tool('unknown_tool', {})

        assert result.success is False
        assert 'not found' in result.error.lower()

    def test_get_tool_schema(self, registry):
        """Test getting tool schema."""
        tool = WebSearchTool()
        registry.register_tool(tool)

        schema = registry.get_tool_schema('web_search')

        assert schema['name'] == 'web_search'
        assert 'parameters' in schema


class TestTools:
    """Test cases for individual tools."""

    def test_web_search_tool(self):
        """Test web search tool."""
        tool = WebSearchTool()
        result = tool.execute(query='test')

        assert result.success is True
        assert 'results' in result.data

    def test_read_file_tool_validation(self):
        """Test read file tool parameter validation."""
        tool = ReadFileTool()
        errors = tool.validate_parameters({})

        assert len(errors) > 0
        assert 'file_path' in errors[0]

    def test_read_file_tool_execution(self):
        """Test read file tool execution with security check."""
        tool = ReadFileTool()
        result = tool.execute(file_path='../../../etc/passwd')

        assert result.success is False
        assert 'directory traversal' in result.error.lower()

    def test_tool_get_schema(self):
        """Test getting tool schema."""
        tool = WebSearchTool()
        schema = tool.get_schema()

        assert schema['name'] == 'web_search'
        assert 'parameters' in schema
        assert 'properties' in schema['parameters']


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the complete agent system."""

    def test_end_to_end_query(self, agent, mock_bedrock_client):
        """Test complete query flow."""
        # Mock responses
        mock_bedrock_client.invoke_model.side_effect = [
            # First call: reasoning - use tool
            Mock(body=Mock(read=Mock(
                return_value=b'{"content": [{"text": "Thought: Need to search\\nAction: {\\"type\\": \\"tool\\", \\"tool\\": \\"web_search\\", \\"parameters\\": {\\"query\\": \\"test\\"}}"}]}'
            ))),
            # Second call: generate response
            Mock(body=Mock(read=Mock(
                return_value=b'{"content": [{"text": "Here is the information you requested"}]}'
            )))
        ]

        result = agent.run("What's the latest news?")

        assert result['status'] == 'success'
        assert 'response' in result
        assert result['iterations'] == 2

    def test_multi_tool_execution(self, agent, mock_bedrock_client):
        """Test agent using multiple tools."""
        mock_bedrock_client.invoke_model.side_effect = [
            # Tool 1
            Mock(body=Mock(read=Mock(
                return_value=b'{"content": [{"text": "Action: {\\"type\\": \\"tool\\", \\"tool\\": \\"web_search\\"}"}]}'
            ))),
            # Tool 2
            Mock(body=Mock(read=Mock(
                return_value=b'{"content": [{"text": "Action: {\\"type\\": \\"tool\\", \\"tool\\": \\"read_file\\"}"}]}'
            ))),
            # Respond
            Mock(body=Mock(read=Mock(
                return_value=b'{"content": [{"text": "Done"}]}'
            )))
        ]

        result = agent.run("Search and read file")

        assert result['iterations'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
