"""Document data model"""

from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import uuid4


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADING = "UPLOADING"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document:
    """Document metadata model"""

    def __init__(
        self,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        status: DocumentStatus = DocumentStatus.PENDING,
        uploaded_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        textract_job_id: Optional[str] = None,
        page_count: Optional[int] = None,
        text_length: Optional[int] = None,
        tables_detected: Optional[int] = None,
        forms_detected: Optional[int] = None,
        error_message: Optional[str] = None,
    ):
        self.document_id = document_id or str(uuid4())
        self.filename = filename
        self.s3_key = s3_key
        self.s3_bucket = s3_bucket
        self.status = status
        self.uploaded_at = uploaded_at or datetime.utcnow().isoformat()
        self.completed_at = completed_at
        self.textract_job_id = textract_job_id
        self.page_count = page_count
        self.text_length = text_length
        self.tables_detected = tables_detected
        self.forms_detected = forms_detected
        self.error_message = error_message

    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        item = {
            "document_id": {"S": self.document_id},
            "uploaded_at": {"S": self.uploaded_at},
            "status": {"S": self.status.value},
        }

        # Add optional fields
        if self.filename:
            item["filename"] = {"S": self.filename}
        if self.s3_key:
            item["s3_key"] = {"S": self.s3_key}
        if self.s3_bucket:
            item["s3_bucket"] = {"S": self.s3_bucket}
        if self.completed_at:
            item["completed_at"] = {"S": self.completed_at}
        if self.textract_job_id:
            item["textract_job_id"] = {"S": self.textract_job_id}
        if self.page_count is not None:
            item["page_count"] = {"N": str(self.page_count)}
        if self.text_length is not None:
            item["text_length"] = {"N": str(self.text_length)}
        if self.tables_detected is not None:
            item["tables_detected"] = {"N": str(self.tables_detected)}
        if self.forms_detected is not None:
            item["forms_detected"] = {"N": str(self.forms_detected)}
        if self.error_message:
            item["error_message"] = {"S": self.error_message}

        return item

    @classmethod
    def from_dynamodb_item(cls, item: dict) -> "Document":
        """Create Document from DynamoDB item"""
        def get_str(key: str) -> Optional[str]:
            return item.get(key, {}).get("S")

        def get_int(key: str) -> Optional[int]:
            val = item.get(key, {}).get("N")
            return int(val) if val else None

        return cls(
            document_id=get_str("document_id"),
            filename=get_str("filename"),
            s3_key=get_str("s3_key"),
            s3_bucket=get_str("s3_bucket"),
            status=DocumentStatus(get_str("status") or DocumentStatus.PENDING),
            uploaded_at=get_str("uploaded_at"),
            completed_at=get_str("completed_at"),
            textract_job_id=get_str("textract_job_id"),
            page_count=get_int("page_count"),
            text_length=get_int("text_length"),
            tables_detected=get_int("tables_detected"),
            forms_detected=get_int("forms_detected"),
            error_message=get_str("error_message"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "s3_key": self.s3_key,
            "s3_bucket": self.s3_bucket,
            "status": self.status.value,
            "uploaded_at": self.uploaded_at,
            "completed_at": self.completed_at,
            "textract_job_id": self.textract_job_id,
            "page_count": self.page_count,
            "text_length": self.text_length,
            "tables_detected": self.tables_detected,
            "forms_detected": self.forms_detected,
            "error_message": self.error_message,
        }
