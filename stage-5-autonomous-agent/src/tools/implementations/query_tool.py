"""Database query tool implementation.

This tool provides database query capabilities.
"""

import os
import boto3
from typing import Dict, Any, List
from tools.base_tool import BaseTool, ToolResult, ToolParameter
from utils import get_env_var, get_aws_client, decimal_to_float


class DynamoDBQueryTool(BaseTool):
    """Tool for querying DynamoDB tables."""

    name = "dynamodb_query"
    description = "Query data from DynamoDB tables"
    category = "database"
    parameters = [
        ToolParameter(
            name="table_name",
            type="string",
            description="Name of the DynamoDB table",
            required=True
        ),
        ToolParameter(
            name="key_condition",
            type="string",
            description="Key condition expression (e.g., 'id = :id')",
            required=True
        ),
        ToolParameter(
            name="expression_values",
            type="string",
            description="Expression attribute values as JSON (e.g., '{\":id\": \"123\"}')",
            required=False
        ),
        ToolParameter(
            name="limit",
            type="number",
            description="Maximum number of items to return",
            required=False
        )
    ]

    def __init__(self):
        """Initialize the DynamoDB query tool."""
        self.dynamodb_client = get_aws_client('dynamodb')

    def execute(self, **kwargs) -> ToolResult:
        """Execute DynamoDB query.

        Args:
            table_name: Table name
            key_condition: Key condition
            expression_values: Expression values
            limit: Result limit

        Returns:
            Query results
        """
        table_name = kwargs.get('table_name')
        key_condition = kwargs.get('key_condition')
        expression_values = kwargs.get('expression_values', '{}')
        limit = kwargs.get('limit')

        if not table_name or not key_condition:
            return ToolResult(
                success=False,
                error="table_name and key_condition are required"
            )

        try:
            # Parse expression values
            values = {}
            if expression_values:
                import json
                values = json.loads(expression_values)
                # Convert to DynamoDB format
                values = {k: {"S": str(v)} for k, v in values.items()}

            # Build query parameters
            query_params = {
                'TableName': table_name,
                'KeyConditionExpression': key_condition
            }

            if values:
                query_params['ExpressionAttributeValues'] = values

            if limit:
                query_params['Limit'] = limit

            # Execute query
            response = self.dynamodb_client.query(**query_params)

            # Convert results
            items = [decimal_to_float(item) for item in response.get('Items', [])]

            return ToolResult(
                success=True,
                data={
                    "count": len(items),
                    "items": items,
                    "scanned_count": response.get('Count', 0)
                },
                metadata={
                    "table": table_name,
                    "consumed_capacity": response.get('ConsumedCapacity', {})
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"DynamoDB query failed: {str(e)}"
            )


class SQLQueryTool(BaseTool):
    """Tool for querying SQL databases (mock)."""

    name = "sql_query"
    description = "Execute SQL queries on a database"
    category = "database"
    parameters = [
        ToolParameter(
            name="query",
            type="string",
            description="SQL query to execute",
            required=True
        ),
        ToolParameter(
            name="database",
            type="string",
            description="Database name",
            required=False
        )
    ]

    def execute(self, **kwargs) -> ToolResult:
        """Execute SQL query.

        Args:
            query: SQL query
            database: Database name

        Returns:
            Query results
        """
        query = kwargs.get('query')
        database = kwargs.get('database', 'default')

        if not query:
            return ToolResult(
                success=False,
                error="Query parameter is required"
            )

        # Safety check
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        if any(keyword in query.upper() for keyword in dangerous_keywords):
            return ToolResult(
                success=False,
                error="Dangerous SQL operations are not allowed"
            )

        try:
            # Mock query execution
            # In production, connect to actual database
            if query.upper().startswith('SELECT'):
                results = [
                    {"id": 1, "name": "Sample Result 1"},
                    {"id": 2, "name": "Sample Result 2"}
                ]
            else:
                results = {"affected_rows": 1}

            return ToolResult(
                success=True,
                data={
                    "database": database,
                    "query": query,
                    "results": results
                },
                metadata={
                    "rows_affected": len(results) if isinstance(results, list) else 1
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"SQL query failed: {str(e)}"
            )
