"""Document analysis handler Lambda function"""

import json
import logging
import os
from typing import Dict, Any
import boto3
from datetime import datetime

from models.document import Document, DocumentStatus
from services.textract_service import TextractService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
TEXTRACT_FEATURES = os.environ.get("TEXTRACT_FEATURES", "TABLES,FORMS")

# AWS clients
dynamodb = boto3.client("dynamodb")
sns = boto3.client("sns")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SQS message handler for document analysis

    This function processes documents from the SQS queue by:
    1. Retrieving document metadata from DynamoDB
    2. Starting Textract analysis
    3. Updating DynamoDB with results
    4. Sending SNS notification on completion

    Args:
        event: SQS event data
        context: Lambda context

    Returns:
        Response dictionary
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Process SQS records
        for record in event.get("Records", []):
            try:
                # Parse message body
                message_body = json.loads(record.get("body", "{}"))
                document_id = message_body.get("document_id")

                if not document_id:
                    logger.error("Missing document_id in message")
                    continue

                logger.info(f"Processing document: {document_id}")

                # Load document from DynamoDB
                document = load_document_from_dynamodb(document_id)

                if not document:
                    logger.error(f"Document {document_id} not found")
                    continue

                # Update status to PROCESSING
                document.status = DocumentStatus.PROCESSING
                update_document_in_dynamodb(document)

                # Process with Textract
                features = TEXTRACT_FEATURES.split(",")
                textract_service = TextractService()

                try:
                    analysis = textract_service.process_document(
                        document.s3_bucket,
                        document.s3_key,
                        features,
                    )

                    # Update document with results
                    document.status = DocumentStatus.COMPLETED
                    document.completed_at = datetime.utcnow().isoformat()
                    document.textract_job_id = analysis.get("job_id")
                    document.page_count = analysis.get("page_count")
                    document.text_length = analysis.get("text_length")
                    document.tables_detected = analysis.get("tables_detected")
                    document.forms_detected = analysis.get("forms_detected")

                    logger.info(
                        f"Document {document_id} processed successfully: "
                        f"{document.page_count} pages, "
                        f"{document.tables_detected} tables, "
                        f"{document.forms_detected} forms"
                    )

                except Exception as e:
                    logger.error(f"Textract processing failed: {e}", exc_info=True)
                    document.status = DocumentStatus.FAILED
                    document.error_message = str(e)

                # Update DynamoDB with final status
                update_document_in_dynamodb(document)

                # Send notification
                send_completion_notification(document)

            except Exception as e:
                logger.error(f"Error processing record: {e}", exc_info=True)
                # Continue processing other records
                continue

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Document analysis completed",
            }),
        }

    except Exception as e:
        logger.error(f"Error in analysis handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
            }),
        }


def load_document_from_dynamodb(document_id: str) -> Document:
    """
    Load document from DynamoDB

    Args:
        document_id: Document ID

    Returns:
        Document object or None
    """
    try:
        response = dynamodb.get_item(
            TableName=DYNAMODB_TABLE,
            Key={
                "document_id": {"S": document_id},
            },
        )

        if "Item" not in response:
            logger.warning(f"Document {document_id} not found in DynamoDB")
            return None

        return Document.from_dynamodb_item(response["Item"])

    except Exception as e:
        logger.error(f"Error loading from DynamoDB: {e}", exc_info=True)
        raise


def update_document_in_dynamodb(document: Document) -> None:
    """
    Update document in DynamoDB

    Args:
        document: Document object
    """
    try:
        # Build update expression
        update_expressions = []
        expression_values = {}
        expression_names = {}

        # Always update status
        update_expressions.append("#status = :status")
        expression_names["#status"] = "status"
        expression_values[":status"] = {"S": document.status.value}

        # Update optional fields
        if document.completed_at:
            update_expressions.append("completed_at = :completed_at")
            expression_values[":completed_at"] = {"S": document.completed_at}

        if document.textract_job_id:
            update_expressions.append("textract_job_id = :job_id")
            expression_values[":job_id"] = {"S": document.textract_job_id}

        if document.page_count is not None:
            update_expressions.append("page_count = :page_count")
            expression_values[":page_count"] = {"N": str(document.page_count)}

        if document.text_length is not None:
            update_expressions.append("text_length = :text_length")
            expression_values[":text_length"] = {"N": str(document.text_length)}

        if document.tables_detected is not None:
            update_expressions.append("tables_detected = :tables")
            expression_values[":tables"] = {"N": str(document.tables_detected)}

        if document.forms_detected is not None:
            update_expressions.append("forms_detected = :forms")
            expression_values[":forms"] = {"N": str(document.forms_detected)}

        if document.error_message:
            update_expressions.append("error_message = :error")
            expression_values[":error"] = {"S": document.error_message}

        # Execute update
        dynamodb.update_item(
            TableName=DYNAMODB_TABLE,
            Key={
                "document_id": {"S": document.document_id},
                "uploaded_at": {"S": document.uploaded_at},
            },
            UpdateExpression="SET " + ", ".join(update_expressions),
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
        )

        logger.info(f"Updated document {document.document_id} in DynamoDB")

    except Exception as e:
        logger.error(f"Error updating DynamoDB: {e}", exc_info=True)
        raise


def send_completion_notification(document: Document) -> None:
    """
    Send SNS notification on document completion

    Args:
        document: Document object
    """
    if not SNS_TOPIC_ARN:
        logger.info("SNS_TOPIC_ARN not configured, skipping notification")
        return

    try:
        # Build notification message
        status_emoji = "✅" if document.status == DocumentStatus.COMPLETED else "❌"

        message = f"""
Document Processing {status_emoji}

Document ID: {document.document_id}
Filename: {document.filename}
Status: {document.status.value}
Uploaded: {document.uploaded_at}
Completed: {document.completed_at or 'N/A'}

"""

        if document.status == DocumentStatus.COMPLETED:
            message += f"""Results:
- Pages: {document.page_count}
- Text Length: {document.text_length}
- Tables Detected: {document.tables_detected}
- Forms Detected: {document.forms_detected}
"""
        elif document.status == DocumentStatus.FAILED:
            message += f"Error: {document.error_message}"

        # Publish to SNS
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Document {document.status.value}: {document.filename}",
            Message=message.strip(),
        )

        logger.info(f"Sent notification for document {document.document_id}")

    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        # Don't fail the workflow if notification fails
