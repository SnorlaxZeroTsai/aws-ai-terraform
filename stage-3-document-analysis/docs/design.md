# Stage 3: Design Document - Document Analysis System

**Date:** 2026-03-11
**Status:** Implementation Complete
**Author:** AI Learning Roadmap

---

## 1. Overview

### 1.1 Purpose

Build an asynchronous document processing pipeline that demonstrates:
- Event-driven architecture
- AWS AI/ML service integration (Textract)
- NoSQL database design (DynamoDB)
- Message queue patterns (SQS)
- Notification systems (SNS)

### 1.2 Scope

**In Scope:**
- PDF and image document upload
- Text extraction using AWS Textract
- Async processing with SQS
- Metadata storage in DynamoDB
- Completion notifications via SNS

**Out of Scope:**
- Document preview generation
- Batch processing
- Document versioning
- Search functionality (Stage 4)

---

## 2. Architecture Decisions

### 2.1 Synchronous vs Asynchronous Processing

**Decision:** Asynchronous processing with SQS

**Options Considered:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Synchronous** | Simple, real-time | Poor UX for long docs, timeouts | ❌ Rejected |
| **Async (SQS)** | Reliable, scalable | More complex, eventual consistency | ✅ **Selected** |
| **Async (Step Functions)** | Visual workflow | Higher cost, overkill | ❌ Rejected |

**Rationale:**

**Advantages:**
1. **Scalability**: Handle burst traffic without dropping requests
2. **Reliability**: DLQ captures failures for analysis
3. **Cost**: Pay only for messages processed
4. **Decoupling**: Upload and processing scale independently

**Disadvantages:**
1. **Complexity**: Need to monitor queue depth
2. **Latency**: Not real-time (30s - 5min)
3. **State Management**: Need to track document status

**Mitigation Strategies:**
- CloudWatch alarms for queue depth > 100
- Exponential backoff for retries
- Status polling endpoint for clients
- TTL on messages to prevent indefinite processing

**Technical Limitations:**
- SQS max message size: 256 KB
- Lambda max timeout: 15 minutes
- Textract max file size: 500 MB

**Cost Considerations:**
- SQS: $0.40 per million requests
- Lambda: $0.20 per 1M requests
- Textract: $1.50 per 1M pages

**Scalability Considerations:**
- SQS: Virtually unlimited throughput
- Lambda: 1000 concurrent executions (default)
- DynamoDB: Unlimited with on-demand

---

### 2.2 DynamoDB Schema Design

**Decision:** Composite key with GSIs

**Schema:**

```
Table: stage3-document-metadata-{env}

Primary Key:
- Partition Key: document_id (String) - UUID
- Sort Key: uploaded_at (String) - ISO timestamp

Attributes:
- filename (String)
- s3_key (String)
- s3_bucket (String)
- status (String) - PENDING|PROCESSING|COMPLETED|FAILED
- completed_at (String) - ISO timestamp
- textract_job_id (String)
- page_count (Number)
- text_length (Number)
- tables_detected (Number)
- forms_detected (Number)
- error_message (String)

Global Secondary Indexes:
1. status-index
   - Partition Key: status
   - Sort Key: uploaded_at
   - Use case: Query all completed documents

2. filename-index
   - Partition Key: filename
   - Sort Key: uploaded_at
   - Use case: Check if file already uploaded
```

**Rationale:**

**Advantages:**
1. **Fast lookups**: Primary key access is O(1)
2. **Query flexibility**: GSIs support multiple access patterns
3. **Automatic scaling**: On-demand pricing
4. **Low latency**: Single-digit millisecond reads

**Disadvantages:**
1. **No joins**: Must denormalize data
2. **GSIs cost**: Extra read/write units
3. **Schema migrations**: Need to plan carefully

**Alternatives Considered:**

| Database | Pros | Cons | Decision |
|----------|------|------|----------|
| **DynamoDB** | Fast, scalable | No joins, learning curve | ✅ **Selected** |
| **RDS** | Familiar SQL | Scaling complexity, higher cost | ❌ Rejected |
| **S3 Select** | Simple | No query flexibility | ❌ Rejected |

**Access Patterns:**

1. Get document by ID: Primary key query
2. List by status: GSI query on status-index
3. Search by filename: GSI query on filename-index
4. Recent uploads: Query with sort on uploaded_at

**Data Modeling Considerations:**
- **Partition key**: UUID prevents hot partitioning
- **Sort key**: ISO timestamp enables time-based queries
- **GSIs**: Support most common queries without scans
- **Item size**: Keep < 400 KB (DynamoDB limit)

---

### 2.3 Error Handling Strategy

**Decision:** Multi-layer error handling with DLQ

**Layers:**

1. **S3 Event Trigger**
   - No retry (event-driven)
   - Lambda DLQ for handler failures

2. **SQS Queue**
   - 3 retries with exponential backoff
   - Move to DLQ after max retries

3. **Lambda Handler**
   - Try/catch blocks with logging
   - Update DynamoDB status to FAILED

4. **Textract API**
   - Poll with timeout (5 minutes)
   - Mark document FAILED on error

**Error States:**

```
PENDING → PROCESSING → COMPLETED
         ↓            ↓
       FAILED ←───────┘
```

**DLQ Monitoring:**
- CloudWatch alarm when DLQ > 0
- SNS notification for alerts
- Manual inspection and replay

**Recovery Strategy:**
1. Inspect DLQ messages
2. Identify failure cause
3. Fix underlying issue
4. Replay message or reprocess document

---

## 3. Component Design

### 3.1 S3 Module

**Features:**
- Versioning enabled (recover from mistakes)
- Server-side encryption (AES256)
- Block public access (security)
- Lifecycle rules (cost management)
- Event notifications (trigger Lambda)

**Naming:**
- Bucket: `stage3-documents-{env}`
- Prefix: `uploads/`

**Security:**
- No public access
- IAM-based access only
- Encryption at rest
- HTTPS only

**Lifecycle:**
- Delete old versions after 30 days
- Minimize storage costs

---

### 3.2 Lambda Functions

**Upload Handler:**
- **Trigger**: S3 ObjectCreated event
- **Timeout**: 30 seconds
- **Memory**: 256 MB
- **Responsibilities**:
  - Create document record in DynamoDB
  - Send message to SQS

**Analysis Handler:**
- **Trigger**: SQS message
- **Timeout**: 300 seconds (5 minutes)
- **Memory**: 512 MB
- **Responsibilities**:
  - Start Textract job
  - Poll for completion
  - Update DynamoDB
  - Send SNS notification

**IAM Permissions:**
- S3: Read document
- DynamoDB: CRUD operations
- SQS: Send/receive/delete messages
- SNS: Publish notifications
- Textract: Start/Get analysis

**Logging:**
- CloudWatch Logs (7-day retention)
- Structured JSON logging
- Error stack traces

---

### 3.3 Textract Integration

**Features:**
- TABLES extraction
- FORMS extraction
- LAYOUT (optional)

**Workflow:**
1. Call `start_document_analysis()`
2. Get job ID
3. Poll `get_document_analysis()`
4. Process results when SUCCEEDED

**Pagination:**
- Extract all pages of results
- Handle NextToken
- Store in DynamoDB

**Error Handling:**
- Check job status
- Capture error messages
- Mark document as FAILED

---

## 4. Data Flow

### 4.1 Upload Flow

```
1. User uploads document to S3 (presigned URL)
2. S3 triggers upload_handler Lambda
3. Lambda creates document record (status: PENDING)
4. Lambda sends message to SQS
5. upload_handler returns success
```

**Timing:** < 1 second

### 4.2 Processing Flow

```
1. SQS triggers analysis_handler Lambda
2. Lambda loads document from DynamoDB
3. Lambda starts Textract job
4. Lambda polls for completion (30s - 5min)
5. Lambda updates DynamoDB with results
6. Lambda sends SNS notification
7. Lambda deletes SQS message
```

**Timing:** 30 seconds - 5 minutes

### 4.3 Error Flow

```
1. Processing fails at any point
2. Error logged to CloudWatch
3. Document status updated to FAILED
4. SQS message moved to DLQ after 3 retries
5. SNS alert sent (if configured)
```

---

## 5. Monitoring & Observability

### 5.1 Metrics

**Lambda:**
- Invocations (count)
- Errors (count)
- Duration (ms)
- Throttles (count)
- Concurrent executions (count)

**SQS:**
- ApproximateNumberOfMessages (count)
- AgeOfOldestMessage (seconds)
- NumberOfMessagesReceived (count)
- NumberOfMessagesDeleted (count)

**DynamoDB:**
- ConsumedReadCapacityUnits (count)
- ConsumedWriteCapacityUnits (count)
- SystemErrors (count)

**Textract:**
- Jobs completed (count)
- Jobs failed (count)

### 5.2 Alarms

- SQS DLQ not empty
- Lambda error rate > 5%
- DynamoDB throttle errors
- Queue age > 1 hour

### 5.3 Logging

**Structured Logging Format:**
```json
{
  "timestamp": "2024-03-10T12:00:00Z",
  "level": "INFO",
  "document_id": "doc-123",
  "message": "Document processing started",
  "function": "analysis_handler",
  "request_id": "123-456-789"
}
```

---

## 6. Security Considerations

### 6.1 Data Security

- **Encryption at rest**: S3 SSE-S3, DynamoDB default
- **Encryption in transit**: TLS/SSL
- **Access control**: IAM roles, least privilege
- **No credentials in code**: Use IAM roles

### 6.2 Network Security

- VPC endpoints (if using VPC)
- No public access to S3
- Private API (if adding later)

### 6.3 Compliance

- Data retention policies
- GDPR considerations (if processing PII)
- Audit logging

---

## 7. Cost Optimization

### 7.1 Cost Drivers

1. **Lambda**: Request count, duration
2. **SQS**: Message count
3. **DynamoDB**: Read/write units
4. **Textract**: Pages processed
5. **S3**: Storage, requests

### 7.2 Optimization Strategies

- **Lambda**: Right-size memory, use Graviton2
- **SQS**: Batch processing
- **DynamoDB**: On-demand for spiky workloads
- **S3**: Lifecycle policies, intelligent tiering
- **Textract**: Filter unwanted file types

### 7.3 Cost Monitoring

- AWS Budgets
- Cost Explorer
- Anomaly detection

---

## 8. Testing Strategy

### 8.1 Unit Tests

- Document model tests
- Textract service tests
- Handler logic tests

### 8.2 Integration Tests

- S3 → Lambda → DynamoDB
- SQS → Lambda → Textract
- End-to-end pipeline

### 8.3 Tools

- pytest
- moto (AWS mocking)
- localstack (local AWS)

---

## 9. Deployment Strategy

### 9.1 Environments

- **dev**: Development/testing
- **prod**: Production

### 9.2 CI/CD

1. Run tests
2. Terraform validate
3. Terraform plan (dry-run)
4. Manual approval
5. Terraform apply

### 9.3 Rollback

- Terraform destroy previous version
- Restore DynamoDB from backup (if needed)

---

## 10. Future Enhancements

### 10.1 Short-term

- Document preview thumbnails
- Batch processing
- Document versioning

### 10.2 Long-term

- Multi-language support
- Custom Textract queries
- Integration with Stage 4 (RAG)
- Webhook notifications

---

## 11. Lessons Learned

### 11.1 What Works Well

- Async processing for long-running tasks
- DLQ for debugging failures
- DynamoDB for fast lookups

### 11.2 Challenges

- Textract polling complexity
- Lambda timeout management
- SQS message ordering

### 11.3 Recommendations

- Start with synchronous processing for simplicity
- Add async only if needed
- Monitor queue depth closely
- Set appropriate timeouts

---

**Document Status:** Complete
**Next Stage:** Stage 4 - RAG Knowledge Base
