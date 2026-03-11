"""Tool registry for managing agent tools.

This module provides a centralized registry for all agent tools,
handling registration, discovery, and execution.
"""

import os
import json
import boto3
from typing import Dict, Any, List, Optional, Type
from importlib import import_module
from pathlib import Path
from base_tool import BaseTool, ToolResult
from utils import get_env_var, get_aws_client


class ToolRegistry:
    """Centralized registry for agent tools.

    The tool registry:
    1. Discovers and registers tools
    2. Validates tool schemas
    3. Executes tools safely
    4. Handles tool errors
    """

    def __init__(
        self,
        s3_client: Optional[Any] = None,
        tool_bucket: Optional[str] = None
    ):
        """Initialize the tool registry.

        Args:
            s3_client: Optional boto3 S3 client
            tool_bucket: Optional S3 bucket for tool definitions
        """
        self.s3_client = s3_client or get_aws_client('s3')
        self.tool_bucket = tool_bucket or get_env_var('TOOL_BUCKET')

        self._tools: Dict[str, BaseTool] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance.

        Args:
            tool: Tool instance to register
        """
        if not tool.name:
            raise ValueError("Tool must have a name")

        self._tools[tool.name] = tool
        self._schemas[tool.name] = tool.get_schema()

        print(f"Registered tool: {tool.name}")

    def register_tools_from_directory(self, directory: str) -> None:
        """Discover and register tools from a directory.

        Args:
            directory: Directory containing tool modules
        """
        tool_dir = Path(directory)

        if not tool_dir.exists():
            print(f"Tool directory not found: {directory}")
            return

        for module_file in tool_dir.glob("*.py"):
            if module_file.name.startswith("_"):
                continue

            try:
                # Import module
                module_name = f"tools.implementations.{module_file.stem}"
                module = import_module(module_name)

                # Find tool classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type) and
                        issubclass(attr, BaseTool) and
                        attr is not BaseTool
                    ):
                        tool_instance = attr()
                        self.register_tool(tool_instance)

            except Exception as e:
                print(f"Error loading tool from {module_file}: {e}")

    def register_tools_from_s3(self) -> None:
        """Load tool definitions from S3.

        This loads JSON tool definitions from S3 and creates
        placeholder tool instances for them.
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.tool_bucket,
                Prefix='tools/'
            )

            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.json'):
                    try:
                        tool_def = json.loads(
                            self.s3_client.get_object(
                                Bucket=self.tool_bucket,
                                Key=obj['Key']
                            )['Body'].read().decode('utf-8')
                        )

                        # Create a dynamic tool class
                        class DynamicTool(BaseTool):
                            name = tool_def['name']
                            description = tool_def.get('description', '')
                            category = tool_def.get('category', 'general')

                            def execute(self, **kwargs):
                                # Placeholder execution
                                return ToolResult(
                                    success=False,
                                    error="Dynamic tool not implemented"
                                )

                        self.register_tool(DynamicTool())

                    except Exception as e:
                        print(f"Error loading tool definition from {obj['Key']}: {e}")

        except Exception as e:
            print(f"Error loading tools from S3: {e}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a registered tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """List registered tools.

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category:
            return [
                name for name, tool in self._tools.items()
                if tool.category == category
            ]
        return list(self._tools.keys())

    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool schema.

        Args:
            name: Tool name

        Returns:
            Tool schema or None
        """
        return self._schemas.get(name)

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool schemas.

        Returns:
            Dictionary of tool schemas
        """
        return self._schemas.copy()

    def execute_tool(
        self,
        name: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute a tool.

        Args:
            name: Tool name
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        tool = self.get_tool(name)

        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}"
            )

        # Validate parameters
        validation_errors = tool.validate_parameters(parameters)
        if validation_errors:
            return ToolResult(
                success=False,
                error=f"Parameter validation failed: {', '.join(validation_errors)}"
            )

        # Execute tool
        try:
            return tool.execute(**parameters)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )

    def save_to_s3(self) -> None:
        """Save all tool schemas to S3."""
        for tool_name, schema in self._schemas.items():
            try:
                self.s3_client.put_object(
                    Bucket=self.tool_bucket,
                    Key=f"tools/{tool_name}.json",
                    Body=json.dumps(schema, indent=2),
                    ContentType='application/json'
                )
                print(f"Saved tool schema: {tool_name}")
            except Exception as e:
                print(f"Error saving tool schema {tool_name}: {e}")


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance.

    Returns:
        ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(tool: BaseTool) -> None:
    """Register a tool with the global registry.

    Args:
        tool: Tool to register
    """
    get_registry().register_tool(tool)
