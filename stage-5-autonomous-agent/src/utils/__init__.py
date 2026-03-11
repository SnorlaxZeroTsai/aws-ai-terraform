"""Utilities package for Stage 5 Autonomous Agent."""

from typing import Dict, Any, Optional
import os
import boto3
import json
from decimal import Decimal

def decimal_to_float(obj: Any) -> Any:
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

def get_env_var(key: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default."""
    value = os.environ.get(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} not set")
    return value

def get_aws_client(service_name: str, region: Optional[str] = None) -> Any:
    """Get AWS client with proper configuration."""
    return boto3.client(
        service_name,
        region_name=region or os.environ.get('AWS_REGION', 'us-east-1')
    )

def format_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format error for consistent error responses."""
    return {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {}
        }
    }
