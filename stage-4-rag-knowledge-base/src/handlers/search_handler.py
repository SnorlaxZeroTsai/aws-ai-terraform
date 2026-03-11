"""
Lambda Handler for RAG Search
Processes search queries via API Gateway
"""

import os
import logging
import json
from typing import Dict, Any

# Setup logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Import services (these should be in the Lambda deployment package)
import sys
sys.path.append('/opt/python')

from services.rag_service import RAGService

# Initialize RAG service (reused across invocations)
_rag_service = None


def get_rag_service() -> RAGService:
    """
    Get or initialize RAG service

    Returns:
        RAGService instance
    """
    global _rag_service

    if _rag_service is None:
        opensearch_endpoint = os.getenv('OPENSEARCH_DOMAIN_ENDPOINT')
        embedding_model_id = os.getenv('BEDROCK_EMBEDDING_MODEL')
        llm_model_id = os.getenv('BEDROCK_LLM_MODEL')

        _rag_service = RAGService(
            opensearch_endpoint=opensearch_endpoint,
            embedding_model_id=embedding_model_id,
            llm_model_id=llm_model_id
        )

    return _rag_service


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for RAG search

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        Response dictionary
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Parse request body
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)

        query = body.get('query')
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required field: query'
                })
            }

        # Get parameters
        max_results = body.get('max_results', int(os.getenv('MAX_RESULTS', 5)))
        search_type = body.get('search_type', 'vector')
        template_type = body.get('template_type', 'qa')
        conversation_history = body.get('conversation_history', None)
        include_chunks = body.get('include_chunks', True)

        logger.info(f"Processing query: {query}")

        # Perform RAG query
        rag_service = get_rag_service()

        if body.get('retrieval_only', False):
            # Retrieval only (no generation)
            chunks = rag_service.query_without_generation(
                user_query=query,
                max_results=max_results,
                search_type=search_type
            )

            response_body = {
                'query': query,
                'chunks': chunks if include_chunks else [],
                'chunk_count': len(chunks)
            }
        else:
            # Full RAG pipeline
            result = rag_service.query(
                user_query=query,
                max_results=max_results,
                search_type=search_type,
                template_type=template_type,
                conversation_history=conversation_history
            )

            response_body = {
                'query': query,
                'answer': result.get('answer'),
                'chunks': result.get('chunks') if include_chunks else [],
                'chunk_count': result.get('chunk_count', 0),
                'search_type': result.get('search_type')
            }

        logger.info("Query processed successfully")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }

    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
