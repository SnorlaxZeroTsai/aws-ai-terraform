"""
Embedding Service for AWS Bedrock
Handles generating embeddings using AWS Bedrock Titan Embeddings model
"""

import boto3
import json
import logging
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using AWS Bedrock"""

    def __init__(self, model_id: str = None, region: str = None):
        """
        Initialize the embedding service

        Args:
            model_id: Bedrock model ID for embeddings
            region: AWS region
        """
        self.model_id = model_id or os.getenv('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')

        # Initialize Bedrock client
        self.client = boto3.client('bedrock-runtime', region_name=self.region)

        logger.info(f"Initialized EmbeddingService with model: {self.model_id}")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of embedding values

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Prepare the request
            request_body = {
                "inputText": text
            }

            # Invoke Bedrock model
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding', [])

            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process in each batch

        Returns:
            List of embeddings

        Raises:
            Exception: If embedding generation fails
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            for text in batch:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text {i}: {str(e)}")
                    # Add zero embedding as fallback
                    embeddings.append([0.0] * self.get_embedding_dimension())

        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors

        Returns:
            Dimension of embeddings
        """
        # Titan Embeddings v1 has 1536 dimensions
        # Claude embeddings have 1024 dimensions
        if 'titan-embed-text-v1' in self.model_id:
            return 1536
        elif 'titan-embed-text-v2' in self.model_id:
            return 1024
        else:
            # Default to 1536
            return 1536

    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate that an embedding has the correct dimension

        Args:
            embedding: Embedding vector to validate

        Returns:
            True if valid, False otherwise
        """
        expected_dim = self.get_embedding_dimension()
        actual_dim = len(embedding)

        if actual_dim != expected_dim:
            logger.warning(f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}")
            return False

        return True


def create_embedding_service() -> EmbeddingService:
    """
    Factory function to create an embedding service instance

    Returns:
        EmbeddingService instance
    """
    return EmbeddingService()
