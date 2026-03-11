"""Tool executor for Lambda function.

This module handles tool execution in the Lambda environment.
"""

import os
import json
import traceback
from typing import Dict, Any
from utils import get_env_var, get_aws_client, format_error


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for tool executor.

    Args:
        event: Lambda event with tool execution request
        context: Lambda context

    Returns:
        Tool execution result
    """
    try:
        tool_name = event.get('tool_name')
        parameters = event.get('parameters', {})

        if not tool_name:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": "tool_name is required"
                })
            }

        # Execute the tool
        result = execute_tool(tool_name, parameters)

        return {
            "statusCode": 200,
            "body": result
        }

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        return {
            "statusCode": 500,
            "body": error_result
        }


def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name.

    Args:
        tool_name: Name of tool to execute
        parameters: Tool parameters

    Returns:
        Execution result
    """
    # Import tool implementations
    from tools.implementations.search_tool import WebSearchTool, NewsSearchTool
    from tools.implementations.query_tool import DynamoDBQueryTool, SQLQueryTool
    from tools.implementations.file_tool import (
        ReadFileTool,
        WriteFileTool,
        ListFilesTool,
        ParseJSONTool
    )

    # Tool registry
    tools = {
        "web_search": WebSearchTool(),
        "news_search": NewsSearchTool(),
        "dynamodb_query": DynamoDBQueryTool(),
        "sql_query": SQLQueryTool(),
        "read_file": ReadFileTool(),
        "write_file": WriteFileTool(),
        "list_files": ListFilesTool(),
        "parse_json": ParseJSONTool()
    }

    tool = tools.get(tool_name)

    if not tool:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(tools.keys())
        }

    # Validate parameters
    validation_errors = tool.validate_parameters(parameters)
    if validation_errors:
        return {
            "success": False,
            "error": f"Parameter validation failed: {', '.join(validation_errors)}"
        }

    # Execute tool
    try:
        result = tool.execute(**parameters)

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata,
            "tool_name": tool_name
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}",
            "tool_name": tool_name
        }
