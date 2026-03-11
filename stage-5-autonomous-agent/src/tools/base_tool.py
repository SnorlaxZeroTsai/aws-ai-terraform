"""Base tool interface for the autonomous agent.

This module defines the abstract interface that all tools must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, number, boolean, etc.)")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value")


class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = Field(..., description="Whether execution was successful")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class BaseTool(ABC):
    """Abstract base class for all agent tools.

    All tools must inherit from this class and implement the required methods.
    """

    # Tool metadata (must be overridden by subclasses)
    name: str = ""
    description: str = ""
    parameters: List[ToolParameter] = []
    category: str = "general"

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate tool parameters.

        Args:
            params: Parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for param in self.parameters:
            if param.required and param.name not in params:
                errors.append(f"Missing required parameter: {param.name}")

            # Type validation
            if param.name in params:
                value = params[param.name]
                if param.type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {param.name} must be a string")
                elif param.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Parameter {param.name} must be a number")
                elif param.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Parameter {param.name} must be a boolean")

        return errors

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM consumption.

        Returns:
            Tool schema dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description
                    }
                    for param in self.parameters
                },
                "required": [
                    param.name for param in self.parameters if param.required
                ]
            }
        }

    def __repr__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name={self.name}, category={self.category})"
