"""
Chatbot Agent - Wraps Stage 2 Lambda function.
"""
import logging
from typing import Dict, Any
import json
import boto3

logger = logging.getLogger(__name__)


class ChatbotAgent:
    """Agent for conversational AI interactions."""

    def __init__(
        self,
        lambda_client: boto3.client,
        lambda_arn: str = None
    ):
        """Initialize chatbot agent."""
        self.lambda_client = lambda_client
        self.lambda_arn = lambda_arn
        logger.info(f"Chatbot agent initialized with Lambda: {lambda_arn}")

    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute chatbot request.

        Args:
            request_data: Chat request with message and optional parameters

        Returns:
            Chatbot response
        """
        try:
            message = request_data.get('message')
            session_id = request_data.get('session_id')
            temperature = request_data.get('temperature', 0.7)
            max_tokens = request_data.get('max_tokens', 1000)

            if not message:
                raise ValueError("Message is required")

            # Invoke Lambda function
            payload = {
                'message': message,
                'session_id': session_id,
                'temperature': temperature,
                'max_tokens': max_tokens
            }

            response = self.lambda_client.invoke(
                FunctionName=self.lambda_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            # Parse response
            response_payload = json.loads(response['Payload'].read().decode())

            if response['StatusCode'] != 200:
                raise Exception(f"Lambda error: {response_payload}")

            return {
                'response': response_payload.get('response'),
                'session_id': response_payload.get('session_id', session_id),
                'model': response_payload.get('model'),
                'tokens_used': response_payload.get('tokens_used')
            }

        except Exception as e:
            logger.error(f"Chatbot agent error: {e}", exc_info=True)
            raise
