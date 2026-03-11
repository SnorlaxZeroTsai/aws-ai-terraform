# Stage 3: Architecture Documentation

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Presigned URL Upload)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                        S3 Bucket                                │
│                   (Document Storage)                            │
│  - Versioning enabled                                           │
│  - Server-side encryption                                       │
│  - Event notifications to Lambda                                │
└────────────────────────┬────────────────────────────────────────┘
                         │ s3:ObjectCreated
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Lambda: Upload Handler                        │
│  - Creates DynamoDB record                                      │
│  - Sends message to SQS                                         │
│  - Returns success                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      SQS Queue                                  │
│              (Async Processing Queue)                           │
│  - 3 retries with backoff                                       │
│  - DLQ for failures                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Lambda: Analysis Handler                       │
│  - Loads document from DynamoDB                                 │
│  - Starts Textract job                                          │
│  - Polls for completion                                         │
│  - Updates DynamoDB                                             │
│  - Sends SNS notification                                       │
└────────────────────┬──────────────────────────┬─────────────────┘
                     │                          │
                     ↓                          ↓
        ┌────────────────────────┐  ┌─────────────────────┐
        │   AWS Textract         │  │   DynamoDB          │
        │   (Document Analysis)  │  │   (Metadata Store)  │
        │  - Text extraction     │  │  - Document records │
        │  - Table detection     │  │  - Status tracking  │
        │  - Form extraction     │  │  - GSIs for queries │
        └────────────────────────┘  └─────────┬───────────┘
                                               │
                                               ↓
                                    ┌─────────────────────┐
                                    │   SNS Topic         │
                                    │   (Notifications)   │
                                    │  - Email alerts     │
                                    │  - Status updates   │
                                    └─────────────────────┘
```

## Component Details

### 1. S3 Bucket (stage3-documents-{env})

**Purpose:** Store uploaded documents

**Configuration:**
- **Bucket Name:** `stage3-documents-{env}`
- **Versioning:** Enabled
- **Encryption:** AES256
- **Public Access:** Blocked
- **Lifecycle:** Delete non-current versions after 30 days

**Event Notifications:**
- **Event:** s3:ObjectCreated:*
- **Prefix:** uploads/
- **Suffix:** .pdf
- **Target:** Upload Handler Lambda

**IAM Policies:**
- Lambda: GetObject, HeadObject
- No public access

---

### 2. Lambda: Upload Handler

**Purpose:** Handle S3 upload events and initiate processing

**Configuration:**
- **Function Name:** `stage3-upload-handler-{env}`
- **Runtime:** Python 3.11
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **Handler:** upload_handler.lambda_handler

**Environment Variables:**
- `DYNAMODB_TABLE`: DynamoDB table name
- `SQS_QUEUE_URL`: SQS queue URL

**IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:HeadObject"
      ],
      "Resource": "arn:aws:s3:::stage3-documents-{env}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/stage3-document-metadata-{env}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:*:*:stage3-document-processing-{env}"
    }
  ]
}
```

**Workflow:**
1. Receive S3 event
2. Extract bucket and key
3. Create Document object
4. Save to DynamoDB (status: PENDING)
5. Send message to SQS
6. Return success

**Error Handling:**
- Log errors to CloudWatch
- Return 500 on failure
- Don't retry (event-driven)

---

### 3. SQS Queue (stage3-document-processing-{env})

**Purpose:** Async message queue for document processing

**Configuration:**
- **Queue Name:** `stage3-document-processing-{env}`
- **Type:** Standard Queue
- **Message Retention:** 14 days
- **Visibility Timeout:** 300 seconds
- **Receive Wait Time:** 20 seconds (long polling)
- **Max Receive Count:** 3

**Dead Letter Queue:**
- **Queue Name:** `stage3-document-processing-{env}-dlq`
- **Retention:** 14 days

**IAM Policies:**
- Lambda: SendMessage, ReceiveMessage, DeleteMessage

**Message Format:**
```json
{
  "document_id": "uuid",
  "s3_bucket": "stage3-documents-dev",
  "s3_key": "uploads/document.pdf",
  "status": "PENDING"
}
```

**Monitoring:**
- CloudWatch metric: ApproximateNumberOfMessages
- Alarm: DLQ not empty

---

### 4. Lambda: Analysis Handler

**Purpose:** Process documents with Textract

**Configuration:**
- **Function Name:** `stage3-analysis-handler-{env}`
- **Runtime:** Python 3.11
- **Timeout:** 300 seconds (5 minutes)
- **Memory:** 512 MB
- **Handler:** analysis_handler.lambda_handler

**Environment Variables:**
- `DYNAMODB_TABLE`: DynamoDB table name
- `SNS_TOPIC_ARN`: SNS topic ARN
- `TEXTRACT_FEATURES`: "TABLES,FORMS"

**IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/stage3-document-metadata-{env}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:*:*:stage3-document-processing-{env}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:*:*:stage3-document-notifications-{env}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentAnalysis",
        "textract:GetDocumentAnalysis"
      ],
      "Resource": "*"
    }
  ]
}
```

**Workflow:**
1. Receive SQS message
2. Load document from DynamoDB
3. Update status to PROCESSING
4. Start Textract job
5. Poll for completion (max 5 min)
6. Update DynamoDB with results
7. Send SNS notification
8. Delete SQS message

**Error Handling:**
- Log errors to CloudWatch
- Update status to FAILED
- SQS retries 3 times
- Move to DLQ on final failure

---

### 5. AWS Textract

**Purpose:** Extract text and data from documents

**API Calls:**
- `start_document_analysis()`: Start async analysis
- `get_document_analysis()`: Get results

**Features:**
- **TABLES**: Detect and extract tables
- **FORMS**: Detect and extract key-value pairs
- **LAYOUT**: Document layout (optional)

**Workflow:**
1. Call start_document_analysis() with S3 location
2. Get JobId
3. Poll get_document_analysis() every 5 seconds
4. Status: IN_PROGRESS → SUCCEEDED/FAILED
5. Retrieve all pages of results
6. Extract text, tables, forms

**Pricing:**
- $1.50 per 1M pages for text detection
- $15.00 per 1M pages for tables/forms

---

### 6. DynamoDB Table (stage3-document-metadata-{env})

**Purpose:** Store document metadata

**Schema:**

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| document_id | String | HASH | UUID |
| uploaded_at | String | RANGE | ISO timestamp |
| filename | String | - | Original filename |
| s3_key | String | - | S3 object key |
| s3_bucket | String | - | S3 bucket name |
| status | String | - | PENDING/PROCESSING/COMPLETED/FAILED |
| completed_at | String | - | ISO timestamp |
| textract_job_id | String | - | Textract job ID |
| page_count | Number | - | Number of pages |
| text_length | Number | - | Extracted text length |
| tables_detected | Number | - | Number of tables |
| forms_detected | Number | - | Number of forms |
| error_message | String | - | Error details |

**Global Secondary Indexes:**

**status-index:**
- Partition Key: status
- Sort Key: uploaded_at
- Use: Query all documents by status

**filename-index:**
- Partition Key: filename
- Sort Key: uploaded_at
- Use: Check if file already uploaded

**Configuration:**
- **Billing Mode:** PAY_PER_REQUEST
- **Point-in-Time Recovery:** Enabled
- **Encryption:** AWS managed key

---

### 7. SNS Topic (stage3-document-notifications-{env})

**Purpose:** Send completion notifications

**Configuration:**
- **Topic Name:** `stage3-document-notifications-{env}`
- **Type:** Standard
- **Subscriptions:** Email (optional)

**Message Format:**
```
Document Processing ✅

Document ID: doc-123
Filename: document.pdf
Status: COMPLETED
Uploaded: 2024-03-10T12:00:00Z
Completed: 2024-03-10T12:01:30Z

Results:
- Pages: 10
- Text Length: 5432
- Tables Detected: 3
- Forms Detected: 5
```

**IAM Permissions:**
- Lambda: Publish

---

## Data Flow

### Complete Flow Diagram

```
User Upload
    │
    ├──> Generate Presigned URL (S3)
    │
    └──> Upload Document (S3)
            │
            └──> s3:ObjectCreated Event
                    │
                    └──> Upload Handler Lambda
                            │
                            ├──> Create Document Record (DynamoDB)
                            │     - status: PENDING
                            │
                            ├──> Send Message (SQS)
                            │     - document_id
                            │     - s3_bucket
                            │     - s3_key
                            │
                            └──> Return Success
                                    │
                                    ↓
                            SQS Queue
                                    │
                                    └──> Analysis Handler Lambda
                                            │
                                            ├──> Load Document (DynamoDB)
                                            │
                                            ├──> Update Status: PROCESSING
                                            │
                                            ├──> Start Textract Job
                                            │     - s3_location
                                            │     - features: TABLES,FORMS
                                            │
                                            ├──> Poll for Completion
                                            │     - 5s intervals
                                            │     - max 5 min
                                            │
                                            ├──> Get Results
                                            │     - Extract all pages
                                            │     - text, tables, forms
                                            │
                                            ├──> Update DynamoDB
                                            │     - status: COMPLETED
                                            │     - results
                                            │
                                            ├──> Send Notification (SNS)
                                            │     - email alert
                                            │
                                            └──> Delete SQS Message
```

### Error Flow

```
Any Failure
    │
    ├──> Log Error (CloudWatch)
    │
    ├──> Update DynamoDB
    │     - status: FAILED
    │     - error_message
    │
    ├──> SQS Retry (max 3)
    │
    └──> Move to DLQ
            │
            └──> CloudWatch Alarm
                    │
                    └──> SNS Alert (Admin)
```

---

## API Reference

### Document Metadata Object

```typescript
interface Document {
  document_id: string;        // UUID
  filename: string;           // Original filename
  s3_key: string;             // S3 object key
  s3_bucket: string;          // S3 bucket name
  status: string;             // PENDING|PROCESSING|COMPLETED|FAILED
  uploaded_at: string;        // ISO 8601 timestamp
  completed_at?: string;      // ISO 8601 timestamp
  textract_job_id?: string;   // Textract job ID
  page_count?: number;        // Number of pages
  text_length?: number;       // Extracted text length
  tables_detected?: number;   // Number of tables
  forms_detected?: number;    // Number of forms
  error_message?: string;     // Error details
}
```

### SQS Message Format

```typescript
interface SQSMessage {
  document_id: string;
  s3_bucket: string;
  s3_key: string;
  status: string;
}
```

### SNS Notification Format

```
Subject: Document {STATUS}: {filename}

Body:
Document Processing {emoji}

Document ID: {document_id}
Filename: {filename}
Status: {status}
Uploaded: {uploaded_at}
Completed: {completed_at}

{if COMPLETED}
Results:
- Pages: {page_count}
- Text Length: {text_length}
- Tables Detected: {tables_detected}
- Forms Detected: {forms_detected}
{end if}

{if FAILED}
Error: {error_message}
{end if}
```

---

## Testing

### Unit Tests

```bash
# Test document model
pytest tests/test_document_model.py -v

# Test Textract service
pytest tests/test_textract_service.py -v
```

### Integration Tests

```bash
# Test upload handler
pytest tests/test_upload_handler.py -v

# Test analysis handler
pytest tests/test_analysis_handler.py -v
```

### End-to-End Test

```bash
# Upload test document
aws s3 cp test.pdf s3://stage3-documents-dev/uploads/test.pdf

# Check DynamoDB
aws dynamodb query \
  --table-name stage3-document-metadata-dev \
  --index-name status-index \
  --key-condition-expression 'status = :status' \
  --expression-attribute-values '{":status": {"S": "COMPLETED"}}'
```

---

## Monitoring

### CloudWatch Dashboards

**Lambda Metrics:**
- Invocations
- Errors
- Duration
- Throttles
- Concurrent Executions

**SQS Metrics:**
- ApproximateNumberOfMessages
- AgeOfOldestMessage
- NumberOfMessagesReceived
- NumberOfMessagesDeleted

**DynamoDB Metrics:**
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- SystemErrors

### Alarms

1. **SQS DLQ Not Empty**
   - Metric: ApproximateNumberOfMessages > 0
   - Action: SNS notification

2. **Lambda Error Rate**
   - Metric: Errors > 5% of invocations
   - Action: SNS notification

3. **Queue Age**
   - Metric: AgeOfOldestMessage > 3600 seconds
   - Action: SNS notification

---

## Troubleshooting

### Document Stuck in PENDING

**Symptoms:**
- Document status not changing
- No Lambda invocations

**Diagnosis:**
```bash
# Check SQS queue
aws sqs get-queue-attributes \
  --queue-url <queue-url> \
  --attribute-names ApproximateNumberOfMessages

# Check Lambda logs
aws logs tail /aws/lambda/stage3-upload-handler-dev --follow
```

**Solutions:**
- Verify S3 event notification
- Check Lambda IAM permissions
- Review CloudWatch logs

### Textract Job Failed

**Symptoms:**
- Document status: FAILED
- Error message in DynamoDB

**Diagnosis:**
```bash
# Get document from DynamoDB
aws dynamodb get-item \
  --table-name stage3-document-metadata-dev \
  --key '{"document_id": {"S": "doc-id"}, "uploaded_at": {"S": "timestamp"}}'

# Check error_message field
```

**Common Causes:**
- Invalid file format
- Corrupted PDF
- File too large (>500MB)
- Unsupported features

### SQS Messages Not Processing

**Symptoms:**
- Queue depth increasing
- No Lambda invocations

**Diagnosis:**
```bash
# Check Lambda concurrency
aws lambda get-function-configuration \
  --function-name stage3-analysis-handler-dev

# Check for throttles
aws logs filter-log-events \
  --log-group-name /aws/lambda/stage3-analysis-handler-dev \
  --filter-pattern "Throttle"
```

**Solutions:**
- Increase Lambda concurrency
- Check Lambda timeout
- Review IAM permissions

---

## Cost Management

### Monthly Cost Estimate (1000 documents)

| Service | Usage | Cost |
|---------|-------|------|
| S3 Storage | 1 GB | $0.023 |
| S3 Requests | 2000 requests | $0.001 |
| Lambda (Upload) | 1000 invocations | $0.0002 |
| Lambda (Analysis) | 1000 invocations × 60s | $0.20 |
| SQS | 2000 messages | $0.001 |
| DynamoDB | 1000 writes, 2000 reads | $0.01 |
| Textract | 1000 pages | $0.002 |
| SNS | 1000 notifications | $0.001 |
| CloudWatch Logs | 5 GB | $0.50 |
| **Total** | | **~$0.74** |

### Cost Optimization

1. **Right-size Lambda memory**
   - Test with 256 MB, 512 MB, 1024 MB
   - Choose best price/performance

2. **Optimize Textract**
   - Only enable needed features
   - Filter unwanted file types

3. **Lifecycle policies**
   - Delete old S3 versions
   - Expire CloudWatch logs

---

## Security

### IAM Roles

**Lambda Execution Role:**
- Least privilege access
- No credentials in code
- Rotate access keys

### Data Protection

- **Encryption at rest:** S3 SSE-S3, DynamoDB default
- **Encryption in transit:** TLS/SSL
- **No public access:** S3 bucket policy blocks public

### Compliance

- **Data retention:** 30 days for non-current versions
- **Audit logging:** CloudWatch Trail (if enabled)
- **PII handling:** Consider GDPR requirements

---

## Future Enhancements

1. **Document Preview**
   - Generate thumbnails
   - First page preview

2. **Batch Processing**
   - Process multiple documents
   - Bulk status updates

3. **Webhook Notifications**
   - HTTP callbacks
   - Real-time updates

4. **Document Versioning**
   - Track versions
   - Compare changes

5. **Integration with Stage 4**
   - Index extracted text
   - Enable semantic search

---

**Document Version:** 1.0
**Last Updated:** 2026-03-11
**Maintainer:** AI Learning Roadmap
