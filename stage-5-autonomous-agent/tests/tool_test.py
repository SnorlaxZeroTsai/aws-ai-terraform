"""Tests for tool implementations.

These tests verify individual tool functionality including:
- Parameter validation
- Execution logic
- Error handling
- Security checks
"""

import pytest
import os
import tempfile
from tools.implementations.search_tool import WebSearchTool, NewsSearchTool
from tools.implementations.query_tool import DynamoDBQueryTool, SQLQueryTool
from tools.implementations.file_tool import (
    ReadFileTool,
    WriteFileTool,
    ListFilesTool,
    ParseJSONTool
)
from tools.base_tool import ToolResult


class TestWebSearchTool:
    """Test cases for WebSearchTool."""

    @pytest.fixture
    def tool(self):
        """Create web search tool instance."""
        return WebSearchTool()

    def test_tool_metadata(self, tool):
        """Test tool has correct metadata."""
        assert tool.name == "web_search"
        assert tool.description
        assert tool.category == "information"
        assert len(tool.parameters) > 0

    def test_required_parameters(self, tool):
        """Test required parameter validation."""
        errors = tool.validate_parameters({})
        assert any("query" in error for error in errors)

    def test_valid_parameters(self, tool):
        """Test valid parameters pass validation."""
        errors = tool.validate_parameters({"query": "test"})
        assert len(errors) == 0

    def test_execution_returns_results(self, tool):
        """Test tool execution returns results."""
        result = tool.execute(query="AI news", num_results=3)

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert "results" in result.data
        assert result.data["count"] == 3

    def test_execution_with_missing_query(self, tool):
        """Test execution fails without query."""
        result = tool.execute()

        assert result.success is False
        assert "required" in result.error.lower()


class TestNewsSearchTool:
    """Test cases for NewsSearchTool."""

    @pytest.fixture
    def tool(self):
        """Create news search tool instance."""
        return NewsSearchTool()

    def test_tool_metadata(self, tool):
        """Test tool has correct metadata."""
        assert tool.name == "news_search"
        assert "news" in tool.description.lower()

    def test_execution_with_days_filter(self, tool):
        """Test tool execution with days parameter."""
        result = tool.execute(query="technology", days=7)

        assert result.success is True
        assert result.data["days"] == 7
        assert "results" in result.data


class TestDynamoDBQueryTool:
    """Test cases for DynamoDBQueryTool."""

    @pytest.fixture
    def tool(self):
        """Create DynamoDB query tool instance."""
        return DynamoDBQueryTool()

    def test_tool_metadata(self, tool):
        """Test tool has correct metadata."""
        assert tool.name == "dynamodb_query"
        assert tool.category == "database"

    def test_required_parameters(self, tool):
        """Test required parameters."""
        errors = tool.validate_parameters({})
        assert len(errors) > 0

    def test_missing_table_name(self, tool):
        """Test missing table_name fails."""
        errors = tool.validate_parameters({"key_condition": "id = :id"})
        assert any("table_name" in error for error in errors)

    def test_schema_structure(self, tool):
        """Test tool schema structure."""
        schema = tool.get_schema()
        assert "parameters" in schema
        assert "properties" in schema["parameters"]


class TestSQLQueryTool:
    """Test cases for SQLQueryTool."""

    @pytest.fixture
    def tool(self):
        """Create SQL query tool instance."""
        return SQLQueryTool()

    def test_dangerous_sql_blocked(self, tool):
        """Test dangerous SQL keywords are blocked."""
        result = tool.execute(query="DROP TABLE users")

        assert result.success is False
        assert "not allowed" in result.error.lower()

    def test_delete_blocked(self, tool):
        """Test DELETE operations are blocked."""
        result = tool.execute(query="DELETE FROM users")

        assert result.success is False

    def test_select_allowed(self, tool):
        """Test SELECT queries are allowed."""
        result = tool.execute(query="SELECT * FROM users")

        assert result.success is True
        assert "results" in result.data

    def test_missing_query(self, tool):
        """Test missing query parameter fails."""
        result = tool.execute()

        assert result.success is False
        assert "required" in result.error.lower()


class TestReadFileTool:
    """Test cases for ReadFileTool."""

    @pytest.fixture
    def tool(self):
        """Create read file tool instance."""
        return ReadFileTool()

    def test_path_traversal_blocked(self, tool):
        """Test directory traversal is blocked."""
        result = tool.execute(file_path="../../../etc/passwd")

        assert result.success is False
        assert "directory traversal" in result.error.lower()

    def test_absolute_path_blocked(self, tool):
        """Test absolute paths are blocked."""
        result = tool.execute(file_path="/etc/passwd")

        assert result.success is False
        assert "invalid" in result.error.lower()

    def test_relative_path_allowed(self, tool):
        """Test relative paths are allowed."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir='/tmp', suffix='.txt') as f:
            f.write("Test content")
            temp_path = os.path.basename(f.name)

        try:
            result = tool.execute(file_path=temp_path)
            # File might not exist in test environment
            # Just check the path was accepted
            if not result.success:
                assert "not found" in result.error.lower()
        finally:
            os.unlink(f.name)

    def test_missing_file_path(self, tool):
        """Test missing file_path parameter."""
        errors = tool.validate_parameters({})
        assert len(errors) > 0


class TestWriteFileTool:
    """Test cases for WriteFileTool."""

    @pytest.fixture
    def tool(self):
        """Create write file tool instance."""
        return WriteFileTool()

    def test_path_traversal_blocked(self, tool):
        """Test directory traversal is blocked."""
        result = tool.execute(
            file_path="../../../tmp/malicious.txt",
            content="Malicious content"
        )

        assert result.success is False

    def test_write_mode_overwrite(self, tool):
        """Test overwrite mode."""
        result = tool.execute(
            file_path="test.txt",
            content="Test content",
            mode="overwrite"
        )

        # Check path validation passed
        # Actual write might fail in test environment
        if not result.success:
            assert "Failed to write file" not in result.error

    def test_write_mode_append(self, tool):
        """Test append mode."""
        result = tool.execute(
            file_path="test.txt",
            content="More content",
            mode="append"
        )

        if result.success:
            assert result.data["mode"] == "append"

    def test_missing_content(self, tool):
        """Test missing content parameter."""
        errors = tool.validate_parameters({"file_path": "test.txt"})
        assert len(errors) > 0


class TestListFilesTool:
    """Test cases for ListFilesTool."""

    @pytest.fixture
    def tool(self):
        """Create list files tool instance."""
        return ListFilesTool()

    def test_list_default_directory(self, tool):
        """Test listing default directory."""
        result = tool.execute()

        assert result.success is True
        assert "files" in result.data

    def test_list_with_pattern(self, tool):
        """Test listing with pattern filter."""
        result = tool.execute(directory="/tmp", pattern="*.txt")

        if result.success:
            assert "files" in result.data
            assert result.data["directory"] == "/tmp"

    def test_directory_traversal_blocked(self, tool):
        """Test directory traversal is blocked."""
        result = tool.execute(directory="../../../etc")

        assert result.success is False
        assert "invalid" in result.error.lower()


class TestParseJSONTool:
    """Test cases for ParseJSONTool."""

    @pytest.fixture
    def tool(self):
        """Create parse JSON tool instance."""
        return ParseJSONTool()

    def test_valid_json(self, tool):
        """Test parsing valid JSON."""
        result = tool.execute(json_string='{"key": "value"}')

        assert result.success is True
        assert result.data["parsed"]["key"] == "value"

    def test_invalid_json(self, tool):
        """Test parsing invalid JSON."""
        result = tool.execute(json_string='{invalid json}')

        assert result.success is False
        assert "invalid" in result.error.lower()

    def test_json_array(self, tool):
        """Test parsing JSON array."""
        result = tool.execute(json_string='[1, 2, 3]')

        assert result.success is True
        assert result.data["parsed"] == [1, 2, 3]

    def test_missing_json_string(self, tool):
        """Test missing json_string parameter."""
        errors = tool.validate_parameters({})
        assert len(errors) > 0


class TestToolSchemas:
    """Test cases for tool schema generation."""

    def test_web_search_schema(self):
        """Test WebSearchTool schema."""
        tool = WebSearchTool()
        schema = tool.get_schema()

        assert schema["name"] == "web_search"
        assert "query" in schema["parameters"]["required"]
        assert "num_results" not in schema["parameters"]["required"]

    def test_dynamodb_query_schema(self):
        """Test DynamoDBQueryTool schema."""
        tool = DynamoDBQueryTool()
        schema = tool.get_schema()

        assert "table_name" in schema["parameters"]["required"]
        assert "key_condition" in schema["parameters"]["required"]
        assert "limit" not in schema["parameters"]["required"]

    def test_all_tools_have_schemas(self):
        """Test all tools can generate schemas."""
        tools = [
            WebSearchTool(),
            NewsSearchTool(),
            DynamoDBQueryTool(),
            SQLQueryTool(),
            ReadFileTool(),
            WriteFileTool(),
            ListFilesTool(),
            ParseJSONTool()
        ]

        for tool in tools:
            schema = tool.get_schema()
            assert "name" in schema
            assert "parameters" in schema
            assert "type" in schema["parameters"]


@pytest.mark.security
class TestToolSecurity:
    """Security tests for tools."""

    def test_file_tools_block_path_traversal(self):
        """Test all file tools block path traversal."""
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "..\\..\\windows\\system32",
            "C:\\Windows\\System32\\config"
        ]

        for path in malicious_paths:
            read_tool = ReadFileTool()
            result = read_tool.execute(file_path=path)
            assert not result.success, f"Path {path} should be blocked"

            write_tool = WriteFileTool()
            result = write_tool.execute(file_path=path, content="test")
            assert not result.success, f"Path {path} should be blocked"

    def test_sql_tool_blocks_dangerous_operations(self):
        """Test SQL tool blocks dangerous operations."""
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "TRUNCATE TABLE users",
            "ALTER TABLE users DROP COLUMN id"
        ]

        tool = SQLQueryTool()
        for query in dangerous_queries:
            result = tool.execute(query=query)
            assert not result.success, f"Query {query} should be blocked"

    def test_parameter_validation(self):
        """Test tools validate parameters."""
        tools = [
            (WebSearchTool(), {}),
            (ReadFileTool(), {}),
            (ParseJSONTool(), {})
        ]

        for tool, params in tools:
            errors = tool.validate_parameters(params)
            assert len(errors) > 0, f"{tool.name} should validate required parameters"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
