"""
RAG Agent - Wraps Stage 4 Lambda function and OpenSearch.
"""
import logging
from typing import Dict, Any, List
import json
import boto3

logger = logging.getLogger(__name__)


class RAGAgent:
    """Agent for RAG knowledge base queries."""

    def __init__(
        self,
        lambda_client: boto3.client,
        lambda_arn: str = None,
        opensearch_endpoint: str = None
    ):
        """Initialize RAG agent."""
        self.lambda_client = lambda_client
        self.lambda_arn = lambda_arn
        self.opensearch_endpoint = opensearch_endpoint
        logger.info(f"RAG agent initialized with Lambda: {lambda_arn}")

    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute RAG query.

        Args:
            request_data: RAG query with top_k, min_score, etc.

        Returns:
            RAG search results with generated answer
        """
        try:
            query = request_data.get('query')
            top_k = request_data.get('top_k', 5)
            min_score = request_data.get('min_score', 0.5)
            include_sources = request_data.get('include_sources', True)

            if not query:
                raise ValueError("Query is required")

            # Invoke Lambda function
            payload = {
                'query': query,
                'top_k': top_k,
                'min_score': min_score,
                'include_sources': include_sources
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
                'answer': response_payload.get('answer'),
                'sources': response_payload.get('sources', []),
                'query': query,
                'num_results': len(response_payload.get('sources', []))
            }

        except Exception as e:
            logger.error(f"RAG agent error: {e}", exc_info=True)
            raise
