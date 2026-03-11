"""Lambda handler for AI chatbot."""

import json
import os
import logging
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from services.llm_service import LLMService
from prompts.chat_templates import get_system_prompt
from utils.response import create_response, create_error_response

# Initialize logger and tracer
logger = Logger(level=os.getenv("LOG_LEVEL", "INFO"))
tracer = Tracer()

# Initialize LLM service
llm_service = LLMService(
    model_id=os.getenv("BEDROCK_MODEL_ID"),
    secret_arn=os.getenv("SECRET_ARN")
)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for chat requests.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response dict
    """
    try:
        logger.info("Processing chat request", extra={"event": event})

        # Parse request body
        body = parse_event_body(event)
        if not body:
            return create_error_response(400, "Invalid request body")

        # Extract message
        message = body.get("message")
        if not message:
            return create_error_response(400, "Missing 'message' field in request")

        # Optional: Extract conversation history
        conversation_history = body.get("history", [])

        # Optional: Extract max_tokens and temperature overrides
        max_tokens = body.get("max_tokens", 1000)
        temperature = body.get("temperature", 0.7)

        # Log the request
        logger.info(
            "Chat request received",
            extra={
                "message_length": len(message),
                "history_length": len(conversation_history)
            }
        )

        # Get system prompt
        system_prompt = get_system_prompt()

        # Call LLM service
        response = llm_service.generate_response(
            message=message,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            max_tokens=max_tokens,
            temperature=temperature
        )

        logger.info("Chat response generated successfully")

        # Return success response
        return create_response(200, {
            "message": response,
            "model": os.getenv("BEDROCK_MODEL_ID")
        })

    except ValueError as e:
        logger.error("Validation error", exc_info=True)
        return create_error_response(400, str(e))

    except Exception as e:
        logger.error("Unexpected error processing request", exc_info=True)
        return create_error_response(500, "Internal server error")


def parse_event_body(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse the request body from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Parsed body as dict, or None if parsing fails
    """
    try:
        if "body" not in event:
            return None

        body = event["body"]
        if isinstance(body, str):
            return json.loads(body)
        return body

    except (json.JSONDecodeError, TypeError) as e:
        logger.error("Failed to parse request body", exc_info=True)
        return None
