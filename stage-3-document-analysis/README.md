# Stage 3: Document Analysis System

## Learning Objectives

After completing this stage, you will be able to:
- [ ] Design asynchronous event-driven architectures
- [ ] Implement S3 event-driven processing
- [ ] Use AWS Textract for document analysis
- [ ] Design DynamoDB schemas for document metadata
- [ ] Implement SQS for reliable message processing
- [ ] Set up SNS for notifications

## Architecture Overview

```
┌────────┐      ┌─────┐      ┌──────┐      ┌──────────┐      ┌─────┐
│  User  │ ───> │ S3  │ ───> │ SQS  │ ───> │ Lambda   │ ───> │Textract
└────────┘      └─────┘      └──────┘      └──────────┘      └─────┘
                           │                                   │
                           ↓                                   ↓
                      ┌─────┐                           ┌──────────┐
                      │ DLQ │                           │ DynamoDB │
                      └─────┘                           └──────────┘
                                                                  │
                                                                  ↓
                                                           ┌─────────┐
                                                           │   SNS   │
                                                           └─────────┘
                                                                  │
                                                                  ↓
                                                           ┌─────────┐
                                                           │  Email  │
                                                           └─────────┘
```

## Features

- **Document Upload**: S3 bucket with presigned URLs
- **Async Processing**: SQS queue for reliable processing
- **Text Extraction**: Textract for PDF, images
- **Metadata Storage**: DynamoDB for document records
- **Notifications**: SNS for completion alerts
- **Error Handling**: Dead letter queue for failures

## Prerequisites

- AWS Account with Textract enabled
- Python 3.11+
- Terraform 1.0+
- AWS CLI configured

## Architecture Decisions

### Why Asynchronous Processing?

**Advantages:**
- **Decoupling**: Upload and processing are independent
- **Scalability**: Handle bursts of uploads
- **Reliability**: DLQ for failed messages
- **Cost**: Pay only for what you use

**Disadvantages:**
- **Complexity**: More moving parts
- **Latency**: Not real-time
- **Monitoring**: Need to track queue depth

**Mitigation Strategies:**
- Use CloudWatch alarms for queue monitoring
- Implement retry logic with exponential backoff
- Set appropriate visibility timeouts

### Why DynamoDB?

**Schema Design:**

```
Partition Key: document_id (String)
Sort Key: uploaded_at (String)

GSIs:
- status-index (status + uploaded_at)
- filename-index (filename + uploaded_at)
```

**Advantages:**
- Fast lookups by document_id
- Query by status or filename
- Automatic scaling
- Low latency

**Considerations:**
- Avoid hot partitions
- Use composite keys for sorting
- Plan query patterns upfront

## Deployment

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Review Variables

Create `terraform.tfvars`:

```hcl
aws_region      = "us-east-1"
environment     = "dev"
notification_email = "your-email@example.com"
```

### 3. Plan and Apply

```bash
terraform plan
terraform apply
```

### 4. Note Outputs

After deployment, note the output values:

```bash
terraform output
```

## Usage

### Upload Document

```python
import boto3

s3 = boto3.client('s3')
bucket = 'stage3-documents-dev'

# Generate presigned URL
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': bucket, 'Key': 'uploads/document.pdf'},
    ExpiresIn=3600
)

# Upload
import requests
with open('document.pdf', 'rb') as f:
    requests.put(url, f.read())
```

### Query Document Status

```bash
# Get document by ID
aws dynamodb get-item \
  --table-name stage3-document-metadata-dev \
  --key '{"document_id": {"S": "doc-123"}, "uploaded_at": {"S": "2024-03-10T12:00:00Z"}}'

# Query by status
aws dynamodb query \
  --table-name stage3-document-metadata-dev \
  --index-name status-index \
  --key-condition-expression 'status = :status' \
  --expression-attribute-values '{":status": {"S": "COMPLETED"}}'
```

### Monitor Queue Depth

```bash
# Get queue attributes
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/stage3-document-processing-dev \
  --attribute-names ApproximateNumberOfMessages
```

## API Reference

### Document Metadata

```json
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "s3_key": "uploads/doc-123.pdf",
  "s3_bucket": "stage3-documents-dev",
  "status": "PROCESSING|COMPLETED|FAILED",
  "uploaded_at": "2024-03-10T12:00:00Z",
  "completed_at": "2024-03-10T12:01:30Z",
  "textract_job_id": "job-123",
  "page_count": 10,
  "text_length": 5432,
  "tables_detected": 3,
  "forms_detected": 5,
  "error_message": null
}
```

## Cost Estimate

| Resource | Cost |
|----------|------|
| S3 Storage | ~$0.023 per GB |
| S3 Requests | ~$0.0004 per 1K requests |
| Lambda | ~$0.20 per 1M requests |
| SQS | ~$0.40 per million requests |
| DynamoDB | On-demand pricing |
| Textract | $1.50 per 1M pages for text |
| SNS | ~$0.50 per million notifications |

**Estimated monthly:** $10-30 for moderate usage (1000 documents)

## Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Monitoring

### CloudWatch Metrics

- **Lambda**: Invocations, Errors, Duration
- **SQS**: ApproximateNumberOfMessages, AgeOfOldestMessage
- **DynamoDB**: ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits
- **S3**: NumberOfObjects, BucketSizeBytes

### Alarms

The stack creates these alarms:
- SQS DLQ not empty
- DynamoDB throttle errors

## Troubleshooting

### Document Stuck in PENDING

Check SQS queue:
```bash
aws sqs receive-message --queue-url <queue-url>
```

Check Lambda logs:
```bash
aws logs tail /aws/lambda/stage3-upload-handler-dev --follow
```

### Textract Job Failed

Check job status in DynamoDB. Common issues:
- Invalid file format
- Corrupted PDF
- File too large (>500MB)

### SQS Messages Not Processing

Check Lambda concurrency limits:
```bash
aws lambda get-function --function-name stage3-analysis-handler-dev
```

## Cleanup

```bash
cd terraform
terraform destroy
```

## Next Steps

- [ ] Add document preview generation
- [ ] Implement document versioning
- [ ] Add batch processing support
- [ ] Integrate with Stage 4 (RAG)

## Resources

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [SQS Dead Letter Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
