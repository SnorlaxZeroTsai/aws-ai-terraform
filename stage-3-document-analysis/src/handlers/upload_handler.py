"""S3 upload handler Lambda function"""

import json
import logging
import os
from typing import Dict, Any
import boto3

from models.document import Document, DocumentStatus
from services.textract_service import TextractService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "")
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL", "")

# AWS clients
dynamodb = boto3.client("dynamodb")
sqs = boto3.client("sqs")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    S3 event handler for document uploads

    This function is triggered when a document is uploaded to S3.
    It creates a document record in DynamoDB and sends a message to SQS
    for async processing.

    Args:
        event: S3 event data
        context: Lambda context

    Returns:
        Response dictionary
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Process S3 event records
        for record in event.get("Records", []):
            s3_info = record.get("s3", {})
            bucket_name = s3_info.get("bucket", {}).get("name", "")
            object_key = s3_info.get("object", {}).get("key", "")

            if not bucket_name or not object_key:
                logger.error("Invalid S3 event: missing bucket or key")
                continue

            # URL decode the key if needed
            import urllib.parse
            object_key = urllib.parse.unquote_plus(object_key)

            logger.info(f"Processing document: {bucket_name}/{object_key}")

            # Create document record
            document = Document(
                filename=object_key.split("/")[-1],
                s3_key=object_key,
                s3_bucket=bucket_name,
                status=DocumentStatus.PENDING,
            )

            # Save to DynamoDB
            save_document_to_dynamodb(document)

            # Send to SQS for processing
            send_to_sqs(document)

            logger.info(f"Document {document.document_id} queued for processing")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Document upload processed successfully",
            }),
        }

    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
            }),
        }


def save_document_to_dynamodb(document: Document) -> None:
    """
    Save document metadata to DynamoDB

    Args:
        document: Document object
    """
    try:
        item = document.to_dynamodb_item()

        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item=item,
        )

        logger.info(f"Saved document {document.document_id} to DynamoDB")

    except Exception as e:
        logger.error(f"Error saving to DynamoDB: {e}", exc_info=True)
        raise


def send_to_sqs(document: Document) -> None:
    """
    Send document processing message to SQS

    Args:
        document: Document object
    """
    try:
        message = {
            "document_id": document.document_id,
            "s3_bucket": document.s3_bucket,
            "s3_key": document.s3_key,
            "status": document.status.value,
        }

        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
            MessageAttributes={
                "DocumentId": {
                    "StringValue": document.document_id,
                    "DataType": "String",
                },
            },
        )

        logger.info(f"Sent document {document.document_id} to SQS")

    except Exception as e:
        logger.error(f"Error sending to SQS: {e}", exc_info=True)
        raise
