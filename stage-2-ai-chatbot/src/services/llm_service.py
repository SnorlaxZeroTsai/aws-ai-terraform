"""LLM service for interacting with AWS Bedrock."""

import json
import logging
import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with AWS Bedrock Claude API."""

    def __init__(self, model_id: str, secret_arn: str):
        """
        Initialize the LLM service.

        Args:
            model_id: Bedrock model ID
            secret_arn: ARN of the secret in Secrets Manager
        """
        self.model_id = model_id
        self.secret_arn = secret_arn

        # Initialize Bedrock client
        self.bedrock = boto3.client("bedrock-runtime")
        self.secrets = boto3.client("secretsmanager")

    def generate_response(
        self,
        message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a response from Claude.

        Args:
            message: User message
            system_prompt: System prompt for the AI
            conversation_history: Optional conversation history
            max_tokens: Maximum tokens in response
            temperature: Response temperature (0.0-1.0)

        Returns:
            Generated response text

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If Bedrock API call fails
        """
        # Validate parameters
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        if not system_prompt:
            raise ValueError("System prompt cannot be empty")

        # Build conversation
        conversation = self._build_conversation(
            message=message,
            system_prompt=system_prompt,
            conversation_history=conversation_history
        )

        # Prepare request payload
        payload = self._prepare_payload(
            conversation=conversation,
            max_tokens=max_tokens,
            temperature=temperature
        )

        try:
            # Invoke Bedrock
            response = self._invoke_bedrock(payload)

            # Extract response text
            response_text = self._extract_response(response)

            logger.info("Successfully generated response from Claude")

            return response_text

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate response: {e}")

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise RuntimeError(f"Unexpected error: {e}")

    def _build_conversation(
        self,
        message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Build the full conversation including system prompt.

        Args:
            message: Current user message
            system_prompt: System prompt
            conversation_history: Previous conversation turns

        Returns:
            Complete conversation list
        """
        conversation = []

        # Add conversation history if provided
        if conversation_history:
            conversation.extend(conversation_history)

        # Add current message
        conversation.append({
            "role": "user",
            "content": message
        })

        return conversation

    def _prepare_payload(
        self,
        conversation: List[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Prepare the request payload for Bedrock.

        Args:
            conversation: Conversation history
            max_tokens: Maximum tokens
            temperature: Temperature parameter

        Returns:
            JSON payload string
        """
        # Claude 3 uses a specific message format
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": conversation
        }

        return json.dumps(payload)

    def _invoke_bedrock(self, payload: str) -> Dict[str, Any]:
        """
        Invoke the Bedrock API.

        Args:
            payload: Request payload

        Returns:
            Bedrock response

        Raises:
            ClientError: If API call fails
        """
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=payload
        )

        response_body = response["body"].read()
        return json.loads(response_body)

    def _extract_response(self, response: Dict[str, Any]) -> str:
        """
        Extract the response text from Bedrock response.

        Args:
            response: Bedrock API response

        Returns:
            Response text

        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Claude 3 response format
            return response["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Invalid response format: {response}")
            raise ValueError(f"Invalid response format from Bedrock: {e}")

    def get_secret(self, key: str) -> Optional[str]:
        """
        Get a secret value from Secrets Manager.

        Args:
            key: Secret key

        Returns:
            Secret value or None if not found
        """
        try:
            secret = self.secrets.get_secret_value(SecretId=self.secret_arn)
            secret_dict = json.loads(secret["SecretString"])
            return secret_dict.get(key)

        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {e}")
            return None
