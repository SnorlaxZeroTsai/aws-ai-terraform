"""Utility functions for API responses."""

from typing import Dict, Any


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an API Gateway response.

    Args:
        status_code: HTTP status code
        body: Response body as dict

    Returns:
        API Gateway response dict
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "POST,OPTIONS"
        },
        "body": json.dumps(body)
    }


def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create an error response.

    Args:
        status_code: HTTP status code
        message: Error message

    Returns:
        API Gateway error response dict
    """
    return create_response(status_code, {
        "error": message,
        "success": False
    })
