"""
Lambda Handler for Document Indexing
Processes S3 events to index documents into OpenSearch
"""

import os
import logging
import boto3
import json
from typing import Dict, Any

# Setup logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Import services (these should be in the Lambda deployment package)
import sys
sys.path.append('/opt/python')

from services.rag_service import RAGService
from chunking.strategies import create_chunking_strategy

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

        # Initialize index
        vector_dimension = int(os.getenv('VECTOR_DIMENSION', 1536))
        _rag_service.initialize_index(vector_dimension)

    return _rag_service


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for document indexing

    Args:
        event: S3 event
        context: Lambda context

    Returns:
        Response dictionary
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Process S3 records
        records = event.get('Records', [])
        processed_count = 0
        failed_count = 0

        rag_service = get_rag_service()

        for record in records:
            try:
                # Get S3 bucket and key
                s3 = record.get('s3')
                bucket_name = s3.get('bucket', {}).get('name')
                object_key = s3.get('object', {}).get('key')

                logger.info(f"Processing document: {bucket_name}/{object_key}")

                # Download document from S3
                s3_client = boto3.client('s3')
                response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                content = response['Body'].read().decode('utf-8')

                # Chunk document
                chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
                chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))
                chunking_strategy = create_chunking_strategy('hybrid', chunk_size, chunk_overlap)
                chunks = chunking_strategy.chunk(content)

                logger.info(f"Created {len(chunks)} chunks")

                # Index chunks
                for chunk in chunks:
                    doc_id = f"{object_key}#{chunk['id']}"

                    metadata = {
                        'source': object_key,
                        'chunk_id': chunk['id'],
                        'doc_id': object_key,
                        'timestamp': context.aws_request_id if context else 'unknown'
                    }

                    success = rag_service.index_document(
                        doc_id=doc_id,
                        content=chunk['content'],
                        metadata=metadata
                    )

                    if success:
                        processed_count += 1
                    else:
                        failed_count += 1

                logger.info(f"Successfully indexed document: {object_key}")

            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                failed_count += 1

        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing complete',
                'processed': processed_count,
                'failed': failed_count
            })
        }

        logger.info(f"Handler completed: {processed_count} processed, {failed_count} failed")
        return response

    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
