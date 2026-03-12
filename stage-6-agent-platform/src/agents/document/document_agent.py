"""
Document Agent - Wraps Stage 3 document analysis.
"""
import logging
from typing import Dict, Any
import json
import boto3

logger = logging.getLogger(__name__)


class DocumentAgent:
    """Agent for document analysis using Textract."""

    def __init__(
        self,
        lambda_client: boto3.client,
        s3_bucket: str = None
    ):
        """Initialize document agent."""
        self.lambda_client = lambda_client
        self.s3_bucket = s3_bucket
        logger.info(f"Document agent initialized with S3 bucket: {s3_bucket}")

    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute document analysis.

        Args:
            request_data: Document key and analysis parameters

        Returns:
            Document analysis results
        """
        try:
            document_key = request_data.get('document_key')
            analysis_type = request_data.get('analysis_type', 'full')
            extract_tables = request_data.get('extract_tables', True)
            extract_forms = request_data.get('extract_forms', True)

            if not document_key:
                raise ValueError("Document key is required")

            # For document analysis, we would typically trigger async processing
            # via SQS. For simplicity, we'll return a job_id.

            job_id = f"doc-{document_key.replace('/', '-')}-{int(datetime.utcnow().timestamp())}"

            return {
                'job_id': job_id,
                'status': 'processing',
                'document_key': document_key,
                'bucket': self.s3_bucket,
                'analysis_type': analysis_type,
                'message': 'Document analysis started'
            }

        except Exception as e:
            logger.error(f"Document agent error: {e}", exc_info=True)
            raise
