"""AWS Textract service wrapper"""

import boto3
import logging
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class TextractService:
    """Service for interacting with AWS Textract"""

    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client("textract", region_name=region_name)

    def start_document_analysis(
        self,
        bucket_name: str,
        document_key: str,
        features: Optional[List[str]] = None,
    ) -> str:
        """
        Start asynchronous document analysis

        Args:
            bucket_name: S3 bucket name
            document_key: S3 object key
            features: List of Textract features (TABLES, FORMS, LAYOUT)

        Returns:
            Job ID for the analysis

        Raises:
            ClientError: If Textract API call fails
        """
        document_location = {
            "S3Object": {
                "Bucket": bucket_name,
                "Name": document_key,
            }
        }

        # Build feature types
        feature_types = features or ["TABLES", "FORMS"]

        try:
            response = self.client.start_document_analysis(
                DocumentLocation=document_location,
                FeatureTypes=feature_types,
            )

            job_id = response["JobId"]
            logger.info(f"Started Textract job {job_id} for {document_key}")

            return job_id

        except ClientError as e:
            logger.error(f"Error starting document analysis: {e}")
            raise

    def get_document_analysis(
        self,
        job_id: str,
        max_results: int = 1000,
        next_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get results of document analysis

        Args:
            job_id: Textract job ID
            max_results: Maximum number of results to return
            next_token: Pagination token

        Returns:
            Dictionary containing analysis results

        Raises:
            ClientError: If Textract API call fails
        """
        try:
            kwargs = {
                "JobId": job_id,
                "MaxResults": max_results,
            }

            if next_token:
                kwargs["NextToken"] = next_token

            response = self.client.get_document_analysis(**kwargs)

            logger.info(
                f"Retrieved analysis for job {job_id}, "
                f"status: {response['JobStatus']}"
            )

            return response

        except ClientError as e:
            logger.error(f"Error getting document analysis: {e}")
            raise

    def is_job_complete(self, job_id: str) -> bool:
        """
        Check if Textract job is complete

        Args:
            job_id: Textract job ID

        Returns:
            True if job is complete, False otherwise
        """
        try:
            response = self.get_document_analysis(job_id, max_results=1)
            job_status = response["JobStatus"]

            if job_status == "SUCCEEDED":
                return True
            elif job_status == "FAILED":
                error_message = response.get("StatusMessage", "Unknown error")
                logger.error(f"Textract job {job_id} failed: {error_message}")
                raise Exception(f"Textract job failed: {error_message}")
            else:
                return False

        except ClientError as e:
            logger.error(f"Error checking job status: {e}")
            raise

    def extract_all_results(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Extract all pages of results from a Textract job

        Args:
            job_id: Textract job ID

        Returns:
            List of all blocks from the document
        """
        all_blocks = []
        next_token = None

        while True:
            response = self.get_document_analysis(job_id, next_token=next_token)

            blocks = response.get("Blocks", [])
            all_blocks.extend(blocks)

            next_token = response.get("NextToken")
            if not next_token:
                break

        logger.info(f"Extracted {len(all_blocks)} blocks from job {job_id}")
        return all_blocks

    def analyze_document_content(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze document content from Textract blocks

        Args:
            blocks: List of Textract blocks

        Returns:
            Dictionary with document statistics
        """
        text_blocks = [b for b in blocks if b["BlockType"] == "LINE"]
        text = " ".join([b.get("Text", "") for b in text_blocks])

        table_blocks = [b for b in blocks if b["BlockType"] == "TABLE"]
        form_blocks = [b for b in blocks if b["BlockType"] == "KEY_VALUE_SET"]

        # Count pages
        page_blocks = [b for b in blocks if b["BlockType"] == "PAGE"]
        page_count = len(page_blocks)

        return {
            "text": text,
            "text_length": len(text),
            "page_count": page_count,
            "tables_detected": len(table_blocks),
            "forms_detected": len(form_blocks),
            "blocks_count": len(blocks),
        }

    def process_document(
        self,
        bucket_name: str,
        document_key: str,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Complete document processing workflow

        Args:
            bucket_name: S3 bucket name
            document_key: S3 object key
            features: List of Textract features

        Returns:
            Dictionary with analysis results
        """
        # Start analysis
        job_id = self.start_document_analysis(bucket_name, document_key, features)

        # Wait for completion (in production, use async workflow)
        import time

        max_wait_time = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            if self.is_job_complete(job_id):
                break
            time.sleep(5)

        # Extract results
        blocks = self.extract_all_results(job_id)

        # Analyze content
        analysis = self.analyze_document_content(blocks)
        analysis["job_id"] = job_id

        return analysis
