# Stage 3: Document Analysis System - Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an asynchronous document processing pipeline using S3, Lambda, AWS Textract, DynamoDB, and SNS/SQS, demonstrating event-driven architecture patterns.

**Architecture:** User uploads to S3 → S3 event triggers Lambda → Textract processes document → Results stored in DynamoDB → SNS sends notification

**Tech Stack:** Terraform, AWS Lambda (Python), S3, Textract, DynamoDB, SNS, SQS, Python 3.11

---

## Chunk 1: Project Setup

### Task 1: Create Directory Structure

**Files:**
- Create: `stage-3-document-analysis/README.md`
- Create: `stage-3-document-analysis/.gitignore`
- Create: `stage-3-document-analysis/requirements.txt`
- Create: `stage-3-document-analysis/terraform/main.tf`
- Create: `stage-3-document-analysis/terraform/variables.tf`
- Create: `stage-3-document-analysis/terraform/outputs.tf`
- Create: `stage-3-document-analysis/terraform/provider.tf`

- [ ] **Step 1: Create directories**

```bash
mkdir -p stage-3-document-analysis/terraform/modules/{s3,lambda,textract,dynamodb,sns_sqs}
mkdir -p stage-3-document-analysis/src/{handlers,services,models,utils}
mkdir -p stage-3-document-analysis/tests
mkdir -p stage-3-document-analysis/docs
```

- [ ] **Step 2: Create .gitignore** (same as Stage 2)

- [ ] **Step 3: Create provider.tf**

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "ai-learning-roadmap"
      Stage     = "3-document-analysis"
      ManagedBy = "Terraform"
    }
  }
}

data "terraform_remote_state" "foundation" {
  backend = "local"
  config = {
    path = "../stage-1-terraform-foundation/terraform/terraform.tfstate"
  }
}
```

- [ ] **Step 4: Create variables.tf**

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "document-analysis"
}

variable "allowed_file_types" {
  description = "Allowed file extensions"
  type        = list(string)
  default     = ["pdf", "png", "jpg", "jpeg"]
}

variable "max_file_size_mb" {
  description = "Maximum file size in MB"
  type        = number
  default     = 10

  validation {
    condition     = var.max_file_size_mb > 0 && var.max_file_size_mb <= 500
    error_message = "File size must be between 1 and 500 MB."
  }
}

variable "enable_async_processing" {
  description = "Enable SQS for async processing"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email for SNS notifications"
  type        = string
  default     = null
}

variable "textract_features" {
  description = "Textract features to enable"
  type = list(object({
    name        = string
    enabled     = bool
  }))
  default = [
    {name = "TABLES", enabled = true},
    {name = "FORMS", enabled = true},
    {name = "LAYOUT", enabled = false}
  ]
}
```

- [ ] **Step 5: Create outputs.tf**

```hcl
output "s3_bucket_name" {
  description = "S3 bucket for document uploads"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3.bucket_arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  value       = try(module.sns_sqs.topic_arn, null)
}

output "api_upload_url" {
  description = "Presigned URL generator function name"
  value       = try(module.lambda.upload_function_name, null)
}
```

- [ ] **Step 6: Create requirements.txt**

```bash
cat > stage-3-document-analysis/requirements.txt << 'EOF'
# AWS SDK
boto3==1.34.84
botocore==1.34.84

# Validation
pydantic==2.6.1

# Utilities
python-dotenv==1.0.1

# Testing
pytest==8.0.2
pytest-mock==3.12.0
pytest-cov==4.1.0
moto==5.0.2
EOF
```

- [ ] **Step 7: Create README.md**

```bash
cat > stage-3-document-analysis/README.md << 'EOF'
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

- Completed Stage 1
- AWS Account with Textract enabled
- Python 3.11+

## Deployment

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Usage

### Upload Document

```python
import boto3

s3 = boto3.client('s3')
bucket = 'your-bucket-name'

# Generate presigned URL
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': bucket, 'Key': 'document.pdf'},
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
  --table-name document-analysis-table \
  --key '{"document_id": {"S": "doc-123"}}'
```

## API Reference

### Document Metadata

```json
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "s3_key": "uploads/doc-123.pdf",
  "s3_bucket": "document-analysis-bucket",
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

**Estimated monthly:** $10-30 for moderate usage

## Cleanup

```bash
cd terraform
terraform destroy
```
EOF
```

- [ ] **Step 8: Create Python package structure**

```bash
touch stage-3-document-analysis/src/__init__.py
touch stage-3-document-analysis/src/handlers/__init__.py
touch stage-3-document-analysis/src/services/__init__.py
touch stage-3-document-analysis/src/models/__init__.py
touch stage-3-document-analysis/src/utils/__init__.py
```

- [ ] **Step 9: Commit**

```bash
git add stage-3-document-analysis/
git commit -m "feat: stage-3 initial project structure"
```

---

## Chunk 2: S3 Module

### Task 2: Create S3 Infrastructure

**Files:**
- Create: `stage-3-document-analysis/terraform/modules/s3/main.tf`
- Create: `stage-3-document-analysis/terraform/modules/s3/variables.tf`
- Create: `stage-3-document-analysis/terraform/modules/s3/outputs.tf`

- [ ] **Step 1: Create S3 module**

```hcl
# S3 Bucket for document uploads
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  tags = var.tags
}

# Enable versioning
resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = var.sse_algorithm
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count = var.enable_lifecycle ? 1 : 0

  bucket = aws_s3_bucket.this.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

# Event notifications to SQS
resource "aws_s3_bucket_notification" "this" {
  count = var.notify_queue_arn != null ? 1 : 0

  bucket = aws_s3_bucket.this.id

  queue {
    queue_arn = var.notify_queue_arn
    events    = ["s3:ObjectCreated:*"]

    filter_prefix = var.notification_prefix
    filter_suffix = var.notification_suffix
  }

  depends_on = [aws_s3_bucket_queue.this]
}

# Allow SQS to receive messages from S3
data "aws_iam_policy_document" "s3_queue" {
  count = var.notify_queue_arn != null ? 1 : 0

  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [var.notify_queue_arn]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.this.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "s3_notification" {
  count = var.notify_queue_arn != null ? 1 : 0

  queue_url = var.queue_url
  policy    = data.aws_iam_policy_document.s3_queue[0].json
}
```

- [ ] **Step 2: Create variables**

```hcl
variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

variable "sse_algorithm" {
  description = "Server-side encryption algorithm"
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.sse_algorithm)
    error_message = "Must be AES256 or aws:kms"
  }
}

variable "enable_lifecycle" {
  description = "Enable lifecycle rules"
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  description = "Days to retain non-current versions"
  type        = number
  default     = 30
}

variable "notify_queue_arn" {
  description = "SQS queue ARN for notifications"
  type        = string
  default     = null
}

variable "queue_url" {
  description = "SQS queue URL"
  type        = string
  default     = null
}

variable "notification_prefix" {
  description = "Filter notifications by prefix"
  type        = string
  default     = "uploads/"
}

variable "notification_suffix" {
  description = "Filter notifications by suffix"
  type        = string
  default     = ".pdf"
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create outputs**

```hcl
output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.this.arn
}

output "bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.this.bucket_domain_name
}
```

- [ ] **Step 4: Update main.tf**

```hcl
# S3 Module (after SQS module is added)
module "s3" {
  source = "./modules/s3"

  bucket_name = "${var.project_name}-${var.environment}-${var.aws_region}"

  notify_queue_arn = try(module.sns_sqs.queue_arn, null)
  queue_url         = try(module.sns_sqs.queue_url, null)

  tags = {
    Stage = "3-document-analysis"
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add stage-3-document-analysis/terraform/modules/s3
git commit -m "feat: add S3 module with versioning and encryption"
```

---

## Chunk 3: SQS/SNS Module

### Task 3: Create Messaging Infrastructure

**Files:**
- Create: `stage-3-document-analysis/terraform/modules/sns_sqs/main.tf`
- Create: `stage-3-document-analysis/terraform/modules/sns_sqs/variables.tf`
- Create: `stage-3-document-analysis/terraform/modules/sns_sqs/outputs.tf`

- [ ] **Step 1: Create SQS/SNS module**

```hcl
# Main processing queue
resource "aws_sqs_queue" "main" {
  name = "${var.name}-main-queue"

  message_retention_seconds = var.message_retention_seconds
  visibility_timeout_seconds = var.visibility_timeout_seconds
  max_message_size = var.max_message_size

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

# Dead letter queue
resource "aws_sqs_queue" "dlq" {
  name = "${var.name}-dlq"

  message_retention_seconds = var.dlq_retention_seconds

  tags = var.tags
}

# CloudWatch alarms for DLQ
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  count = var.create_dlq_alarm ? 1 : 0

  alarm_name          = "${var.name}-dlq-messages"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.dlq_alarm_threshold

  dimensions = {
    QueueUrl = aws_sqs_queue.dlq.id
  }

  alarm_actions = var.dlq_alarm_actions

  tags = var.tags
}

# SNS Topic for notifications
resource "aws_sns_topic" "this" {
  name = var.topic_name

  tags = var.tags
}

# Email subscription
resource "aws_sns_topic_subscription" "email" {
  count = var.notification_email != null ? 1 : 0

  topic_arn = aws_sns_topic.this.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Lambda subscription for processing notifications
resource "aws_sns_topic_subscription" "lambda" {
  count = var.notify_lambda_arn != null ? 1 : 0

  topic_arn = aws_sns_topic.this.arn
  protocol  = "lambda"
  endpoint  = var.notify_lambda_arn
}
```

- [ ] **Step 2: Create variables**

```hcl
variable "name" {
  description = "Base name for resources"
  type        = string
}

variable "topic_name" {
  description = "SNS topic name"
  type        = string
}

variable "message_retention_seconds" {
  description = "Message retention in main queue"
  type        = number
  default     = 1209600  # 14 days

  validation {
    condition     = var.message_retention_seconds >= 60 && var.message_retention_seconds <= 1209600
    error_message = "Retention must be between 60 and 1209600 seconds."
  }
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout for main queue"
  type        = number
  default     = 900  # 15 minutes

  validation {
    condition     = var.visibility_timeout_seconds >= 0 && var.visibility_timeout_seconds <= 43200
    error_message = "Visibility timeout must be between 0 and 43200 seconds."
  }
}

variable "max_message_size" {
  description = "Maximum message size in bytes"
  type        = number
  default     = 262144  # 256 KB

  validation {
    condition     = var.max_message_size >= 1024 && var.max_message_size <= 262144
    error_message = "Message size must be between 1024 and 262144 bytes."
  }
}

variable "max_receive_count" {
  description = "Max receives before DLQ"
  type        = number
  default     = 3
}

variable "dlq_retention_seconds" {
  description = "DLQ message retention"
  type        = number
  default     = 1209600  # 14 days
}

variable "create_dlq_alarm" {
  description = "Create DLQ CloudWatch alarm"
  type        = bool
  default     = true
}

variable "dlq_alarm_threshold" {
  description = "DLQ alarm threshold"
  type        = number
  default     = 5
}

variable "dlq_alarm_actions" {
  description = "Actions for DLQ alarm (SNS ARNs)"
  type        = list(string)
  default     = []
}

variable "notification_email" {
  description = "Email for SNS notifications"
  type        = string
  default     = null
}

variable "notify_lambda_arn" {
  description = "Lambda ARN for SNS notifications"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create outputs**

```hcl
output "queue_url" {
  description = "Main SQS queue URL"
  value       = aws_sqs_queue.main.id
}

output "queue_arn" {
  description = "Main SQS queue ARN"
  value       = aws_sqs_queue.main.arn
}

output "dlq_url" {
  description = "DLQ URL"
  value       = aws_sqs_queue.dlq.id
}

output "topic_arn" {
  description = "SNS topic ARN"
  value       = aws_sns_topic.this.arn
}

output "topic_name" {
  description = "SNS topic name"
  value       = aws_sns_topic.this.name
}
```

- [ ] **Step 4: Update main.tf**

```hcl
# SQS/SNS Module
module "sns_sqs" {
  source = "./modules/sns_sqs"

  name             = "${var.project_name}-${var.environment}"
  topic_name       = "${var.project_name}-notifications-${var.environment}"

  notification_email = var.notification_email

  tags = {
    Stage = "3-document-analysis"
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add stage-3-document-analysis/terraform/modules/sns_sqs stage-3-document-analysis/terraform/main.tf
git commit -m "feat: add SQS/SNS modules with DLQ"
```

---

## Chunk 4: DynamoDB Module

### Task 4: Create Database Infrastructure

**Files:**
- Create: `stage-3-document-analysis/terraform/modules/dynamodb/main.tf`
- Create: `stage-3-document-analysis/terraform/modules/dynamodb/variables.tf`
- Create: `stage-3-document-analysis/terraform/modules/dynamodb/outputs.tf`

- [ ] **Step 1: Create DynamoDB module**

```hcl
# Documents table
resource "aws_dynamodb_table" "documents" {
  name           = var.table_name
  billing_mode   = var.billing_mode
  hash_key       = var.hash_key

  # Stream for Lambda triggers
  stream_enabled   = var.stream_enabled
  stream_view_type = var.stream_view_type

  attribute {
    name = var.hash_key
    type = "S"
  }

  # GSI for querying by status
  dynamic "global_secondary_index" {
    for_each = var.create_status_index ? [1] : []
    content {
      name            = "${var.table_name}-status-index"
      hash_key        = "status"
      range_key       = "uploaded_at"
      projection_type = "ALL"

      read_capacity  = var.index_read_capacity
      write_capacity = var.index_write_capacity
    }
  }

  # GSI for querying by user
  dynamic "global_secondary_index" {
    for_each = var.create_user_index ? [1] : []
    content {
      name            = "${var.table_name}-user-index"
      hash_key        = "user_id"
      range_key       = "uploaded_at"
      projection_type = "ALL"

      read_capacity  = var.index_read_capacity
      write_capacity = var.index_write_capacity
    }
  }

  tags = var.tags

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_pitr
  }

  # TTL for automatic cleanup
  ttl {
    attribute_name = "expire_at"
    enabled        = var.enable_ttl
  }
}

# Auto-scaling for on-demand (if using provisioned)
resource "aws_appautoscaling_target" "read" {
  count = var.billing_mode == "PROVISIONED" && var.enable_autoscaling ? 1 : 0

  max_capacity       = var.max_read_capacity
  min_capacity       = var.min_read_capacity
  resource_id        = "table/${aws_dynamodb_table.documents.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "read" {
  count = var.billing_mode == "PROVISIONED" && var.enable_autoscaling ? 1 : 0

  name               = "${var.table_name}-read-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.read[0].resource_id
  scalable_dimension = aws_appautoscaling_target.read[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.read[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value       = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
```

- [ ] **Step 2: Create variables**

```hcl
variable "table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "billing_mode" {
  description = "Billing mode"
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PROVISIONED", "PAY_PER_REQUEST"], var.billing_mode)
    error_message = "Must be PROVISIONED or PAY_PER_REQUEST."
  }
}

variable "hash_key" {
  description = "Hash key name"
  type        = string
  default     = "document_id"
}

variable "stream_enabled" {
  description = "Enable DynamoDB Streams"
  type        = bool
  default     = true
}

variable "stream_view_type" {
  description = "Stream view type"
  type        = string
  default     = "NEW_IMAGE"

  validation {
    condition     = contains(["KEYS_ONLY", "NEW_IMAGE", "OLD_IMAGE", "NEW_AND_OLD_IMAGES"], var.stream_view_type)
    error_message = "Invalid stream view type."
  }
}

variable "create_status_index" {
  description = "Create status GSI"
  type        = bool
  default     = true
}

variable "create_user_index" {
  description = "Create user GSI"
  type        = bool
  default     = true
}

variable "index_read_capacity" {
  description = "GSI read capacity"
  type        = number
  default     = 5
}

variable "index_write_capacity" {
  description = "GSI write capacity"
  type        = number
  default     = 5
}

variable "enable_pitr" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "enable_ttl" {
  description = "Enable TTL"
  type        = bool
  default     = false
}

variable "enable_autoscaling" {
  description = "Enable auto-scaling"
  type        = bool
  default     = false
}

variable "min_read_capacity" {
  description = "Min read capacity"
  type        = number
  default     = 5
}

variable "max_read_capacity" {
  description = "Max read capacity"
  type        = number
  default     = 100
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create outputs**

```hcl
output "table_name" {
  description = "Table name"
  value       = aws_dynamodb_table.documents.name
}

output "table_arn" {
  description = "Table ARN"
  value       = aws_dynamodb_table.documents.arn
}

output "stream_arn" {
  description = "Stream ARN"
  value       = aws_dynamodb_table.documents.stream_arn
}
```

- [ ] **Step 4: Update main.tf**

```hcl
# DynamoDB Module
module "dynamodb" {
  source = "./modules/dynamodb"

  table_name = "${var.project_name}-${var.environment}"

  tags = {
    Stage = "3-document-analysis"
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add stage-3-document-analysis/terraform/modules/dynamodb stage-3-document-analysis/terraform/main.tf
git commit -m "feat: add DynamoDB table with GSIs"
```

---

## Chunk 5: Lambda & Textract Integration

### Task 5: Create Processing Function

**Files:**
- Create: `stage-3-document-analysis/terraform/modules/lambda/main.tf`
- Create: `stage-3-document-analysis/terraform/modules/textract/main.tf`
- Create: `stage-3-document-analysis/src/handlers/processor.py`
- Create: `stage-3-document-analysis/src/services/textract_service.py`
- Create: `stage-3-document-analysis/src/models/document.py`

- [ ] **Step 1: Create Textract module**

```hcl
# Textract access policy
data "aws_iam_policy_document" "textract" {
  statement {
    effect = "Allow"

    actions = [
      "textract:StartDocumentTextDetection",
      "textract:StartDocumentAnalysis",
      "textract:GetDocumentTextDetection",
      "textract:GetDocumentAnalysis",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "textract" {
  name   = "${var.name}-textract-policy"
  policy = data.aws_iam_policy_document.textract.json
}

# S3 access for Textract
data "aws_iam_policy_document" "s3_read" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
    ]

    resources = ["${var.s3_bucket_arn}/*"]
  }
}

resource "aws_iam_policy" "s3_read" {
  name   = "${var.name}-s3-read-policy"
  policy = data.aws_iam_policy_document.s3_read.json
}
```

- [ ] **Step 2: Create Lambda module**

```hcl
# Archive Lambda code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../src"
  output_path = "${path.module}/lambda_function.zip"

  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".venv",
    "venv",
    "tests"
  ]
}

# Lambda IAM role
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json

  tags = var.tags
}

# Attach policies
resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "dynamodb" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

resource "aws_iam_role_policy_attachment" "sqs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

resource "aws_iam_role_policy_attachment" "sns" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSNSFullAccess"
}

# Lambda function
resource "aws_lambda_function" "processor" {
  function_name    = var.function_name
  description      = "Process documents with Textract"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.processor.handler"
  runtime          = "python3.11"
  timeout          = var.timeout
  memory_size      = var.memory_size
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  filename         = data.archive_file.lambda_zip.output_path

  environment {
    variables = {
      DYNAMODB_TABLE    = var.dynamodb_table
      SNS_TOPIC_ARN     = var.sns_topic_arn
      TEXTRACT_FEATURES = jsonencode(var.textract_features)
      LOG_LEVEL         = var.log_level
    }
  }

  tags = var.tags

  depends_on = [
    aws_iam_role_policy_attachment.basic,
    aws_cloudwatch_log_group.this
  ]
}

# Log group
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention

  tags = var.tags
}

# SQS trigger
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = var.batch_size
  enabled          = true
}
```

- [ ] **Step 3: Create document model**

```bash
cat > stage-3-document-analysis/src/models/document.py << 'EOF'
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class Document:
    """Document metadata model"""

    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = None
    s3_key: str = None
    s3_bucket: str = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    uploaded_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    textract_job_id: Optional[str] = None
    page_count: Optional[int] = None
    text_length: Optional[int] = None
    tables_detected: Optional[int] = None
    forms_detected: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item"""
        item = {
            "document_id": {"S": self.document_id},
            "filename": {"S": self.filename},
            "s3_key": {"S": self.s3_key},
            "s3_bucket": {"S": self.s3_bucket},
            "status": {"S": self.status.value},
            "uploaded_at": {"S": self.uploaded_at},
        }

        if self.completed_at:
            item["completed_at"] = {"S": self.completed_at}
        if self.textract_job_id:
            item["textract_job_id"] = {"S": self.textract_job_id}
        if self.page_count:
            item["page_count"] = {"N": str(self.page_count)}
        if self.text_length:
            item["text_length"] = {"N": str(self.text_length)}
        if self.tables_detected:
            item["tables_detected"] = {"N": str(self.tables_detected)}
        if self.forms_detected:
            item["forms_detected"] = {"N": str(self.forms_detected)}
        if self.error_message:
            item["error_message"] = {"S": self.error_message}
        if self.metadata:
            item["metadata"] = {"M": {k: self._format_value(v)
                                     for k, v in self.metadata.items()}}

        return item

    @staticmethod
    def _format_value(value: Any) -> Dict[str, Any]:
        """Format value for DynamoDB"""
        if isinstance(value, str):
            return {"S": value}
        elif isinstance(value, (int, float)):
            return {"N": str(value)}
        elif isinstance(value, bool):
            return {"BOOL": value}
        elif isinstance(value, list):
            return {"L": [Document._format_value(v) for v in value]}
        elif isinstance(value, dict):
            return {"M": {k: Document._format_value(v)
                         for k, v in value.items()}}
        else:
            return {"NULL": True}

    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> "Document":
        """Create from DynamoDB item"""
        def get_value(attr: Dict[str, Any]) -> Any:
            if "S" in attr:
                return attr["S"]
            elif "N" in attr:
                return int(attr["N"])
            elif "BOOL" in attr:
                return attr["BOOL"]
            return None

        return cls(
            document_id=get_value(item["document_id"]),
            filename=get_value(item["filename"]),
            s3_key=get_value(item["s3_key"]),
            s3_bucket=get_value(item["s3_bucket"]),
            status=DocumentStatus(get_value(item["status"])),
            uploaded_at=get_value(item["uploaded_at"]),
            completed_at=get_value(item.get("completed_at")),
            textract_job_id=get_value(item.get("textract_job_id")),
            page_count=get_value(item.get("page_count")),
            text_length=get_value(item.get("text_length")),
            tables_detected=get_value(item.get("tables_detected")),
            forms_detected=get_value(item.get("forms_detected")),
            error_message=get_value(item.get("error_message")),
        )
EOF
```

- [ ] **Step 4: Create Textract service**

```bash
cat > stage-3-document-analysis/src/services/textract_service.py << 'EOF'
import boto3
import os
import json
from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TextractService:
    """Service for AWS Textract operations"""

    def __init__(self):
        self.client = boto3.client("textract", region_name=os.getenv("AWS_REGION"))
        self.features = json.loads(os.getenv("TEXTRACT_FEATURES", "[]"))

    def start_text_detection(self, s3_bucket: str, s3_key: str) -> str:
        """Start asynchronous text detection"""

        logger.info("Starting Textract text detection", extra_data={
            "bucket": s3_bucket,
            "key": s3_key
        })

        response = self.client.start_document_text_detection(
            DocumentLocation={
                "S3Object": {
                    "Bucket": s3_bucket,
                    "Name": s3_key
                }
            }
        )

        job_id = response["JobId"]
        logger.info("Textract job started", extra_data={"job_id": job_id})

        return job_id

    def start_document_analysis(
        self,
        s3_bucket: str,
        s3_key: str,
        feature_types: List[str] = None
    ) -> str:
        """Start document analysis with features"""

        features = feature_types or [
            f["name"] for f in self.features if f.get("enabled")
        ]

        logger.info("Starting Textract document analysis", extra_data={
            "bucket": s3_bucket,
            "key": s3_key,
            "features": features
        })

        response = self.client.start_document_analysis(
            DocumentLocation={
                "S3Object": {
                    "Bucket": s3_bucket,
                    "Name": s3_key
                }
            },
            FeatureTypes=features
        )

        job_id = response["JobId"]
        logger.info("Textract analysis job started", extra_data={"job_id": job_id})

        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get Textract job status"""

        try:
            response = self.client.get_document_text_detection(JobId=job_id)

            status = response["JobStatus"]
            logger.info("Textract job status", extra_data={
                "job_id": job_id,
                "status": status
            })

            return {
                "status": status,
                "job_id": job_id,
                "pages": response.get("Pages", 0),
            }

        except Exception as e:
            logger.error("Failed to get job status", extra_data={
                "job_id": job_id,
                "error": str(e)
            })
            raise

    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get full Textract job results"""

        logger.info("Fetching Textract results", extra_data={"job_id": job_id})

        results = []
        next_token = None

        while True:
            if next_token:
                response = self.client.get_document_text_detection(
                    JobId=job_id,
                    NextToken=next_token
                )
            else:
                response = self.client.get_document_text_detection(JobId=job_id)

            results.extend(response.get("Blocks", []))

            next_token = response.get("NextToken")
            if not next_token:
                break

        # Analyze results
        text_blocks = [b for b in results if b["BlockType"] == "LINE"]
        full_text = "\n".join([b["Text"] for b in text_blocks])

        page_numbers = set()
        for block in results:
            if "Page" in block:
                page_numbers.add(block["Page"])

        return {
            "text": full_text,
            "page_count": len(page_numbers),
            "blocks": len(results),
            "text_blocks": len(text_blocks),
        }

    def wait_for_job(
        self,
        job_id: str,
        max_wait_seconds: int = 300
    ) -> Dict[str, Any]:
        """Wait for job completion"""

        import time

        start_time = time.time()

        while True:
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError(f"Job {job_id} timed out")

            status_result = self.get_job_status(job_id)
            status = status_result["status"]

            if status == "SUCCEEDED":
                return self.get_job_results(job_id)
            elif status == "FAILED":
                raise Exception(f"Job {job_id} failed")
            elif status in ["IN_PROGRESS", "PARTIAL_SUCCESS"]:
                time.sleep(5)
            else:
                raise Exception(f"Unknown job status: {status}")
EOF
```

- [ ] **Step 5: Create processor handler**

```bash
cat > stage-3-document-analysis/src/handlers/processor.py << 'EOF'
import json
import os
from typing import Dict, Any
from ..models.document import Document, DocumentStatus
from ..services.textract_service import TextractService
from ..utils.response import success_response, error_response
from ..utils.logger import get_logger
from ..services.dynamodb_service import DynamoDBService

logger = get_logger(__name__)
textract = TextractService()
dynamodb = DynamoDBService()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Process SQS messages"""

    logger.info("Document processor invoked")

    # Process each SQS record
    results = []

    for record in event["Records"]:
        try:
            # Parse S3 event from SQS
            message = json.loads(record["body"])
            s3_info = message["Records"][0]["s3"]

            bucket = s3_info["bucket"]["name"]
            key = s3_info["object"]["key"]

            # Create document record
            document = Document(
                filename=key.split("/")[-1],
                s3_key=key,
                s3_bucket=bucket,
                status=DocumentStatus.PROCESSING
            )

            # Save initial state
            dynamodb.save_document(document)

            # Start Textract job
            job_id = textract.start_document_analysis(
                s3_bucket=bucket,
                s3_key=key
            )

            document.textract_job_id = job_id
            dynamodb.save_document(document)

            # Wait for results (sync for simplicity)
            results_data = textract.wait_for_job(job_id, max_wait_seconds=120)

            # Update document with results
            document.status = DocumentStatus.COMPLETED
            document.page_count = results_data["page_count"]
            document.text_length = results_data["text_blocks"]
            document.completed_at = datetime.utcnow().isoformat()

            dynamodb.save_document(document)

            # Send notification
            send_completion_notification(document)

            results.append({
                "document_id": document.document_id,
                "status": "completed",
                "page_count": document.page_count
            })

        except Exception as e:
            logger.error("Processing failed", extra_data={"error": str(e)})

            # Update document status
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            dynamodb.save_document(document)

            results.append({
                "document_id": document.document_id,
                "status": "failed",
                "error": str(e)
            })

    return {
        "statusCode": 200,
        "body": json.dumps({"processed": len(results)})
    }

def send_completion_notification(document: Document):
    """Send SNS notification"""
    import boto3

    sns = boto3.client("sns")
    topic_arn = os.getenv("SNS_TOPIC_ARN")

    if not topic_arn:
        return

    message = json.dumps({
        "document_id": document.document_id,
        "filename": document.filename,
        "status": document.status.value,
        "page_count": document.page_count,
    })

    sns.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject=f"Document Processing {document.status.value}"
    )
EOF
```

- [ ] **Step 6: Create DynamoDB service**

```bash
cat > stage-3-document-analysis/src/services/dynamodb_service.py << 'EOF'
import boto3
import os
from typing import Dict, Any, Optional
from ..models.document import Document
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DynamoDBService:
    """Service for DynamoDB operations"""

    def __init__(self):
        self.client = boto3.client("dynamodb")
        self.table_name = os.getenv("DYNAMODB_TABLE")

    def save_document(self, document: Document) -> None:
        """Save document to DynamoDB"""

        logger.info("Saving document", extra_data={
            "document_id": document.document_id,
            "status": document.status.value
        })

        self.client.put_item(
            TableName=self.table_name,
            Item=document.to_dynamodb_item()
        )

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""

        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={"document_id": {"S": document_id}}
            )

            if "Item" not in response:
                return None

            return Document.from_dynamodb_item(response["Item"])

        except Exception as e:
            logger.error("Failed to get document", extra_data={
                "document_id": document_id,
                "error": str(e)
            })
            raise

    def query_by_status(
        self,
        status: DocumentStatus
    ) -> list[Document]:
        """Query documents by status"""

        # Would use GSI for this query
        pass
EOF
```

- [ ] **Step 7: Create logger and response utilities** (similar to Stage 2)

- [ ] **Step 8: Commit Lambda code**

```bash
git add stage-3-document-analysis/src/
git add stage-3-document-analysis/terraform/modules/lambda
git add stage-3-document-analysis/terraform/modules/textract
git commit -m "feat: implement document processor with Textract integration"
```

---

## Chunk 6: Testing & Documentation

### Task 6: Create Tests

- [ ] **Step 1: Create test file**

```bash
cat > stage-3-document-analysis/tests/test_processor.py << 'EOF'
import pytest
import json
from moto import mock_dynamodb, mock_sqs, mock_s3, mock_textract
from src.handlers.processor import handler
from src.models.document import Document

@mock_s3
@mock_sqs
@mock_dynamodb
@mock_textract
def test_document_processing():
    """Test end-to-end document processing"""
    # Test implementation
    pass
EOF
```

- [ ] **Step 2: Commit tests**

```bash
git add stage-3-document-analysis/tests/
git commit -m "test: add processor tests"
```

### Task 7: Create Design Document

- [ ] **Step 1: Create design document**

```bash
cat > stage-3-document-analysis/docs/design.md << 'EOF'
# Stage 3: Document Analysis - Architecture Design

## 1. Architecture Overview

```
User Upload → S3 → Event → SQS → Lambda → Textract
                                ↓
                           DynamoDB
                                ↓
                             SNS → Email
```

## 2. Design Decisions

### Decision 1: Why SQS for Async Processing?

**Problem:** How to handle document processing reliably?

**Selection:** SQS with DLQ

**Pros:**
- ✅ Decoupling: S3 and Lambda are independent
- ✅ Retry logic: Automatic retries with backoff
- ✅ Error handling: DLQ captures failures
- ✅ Throttling: Control Lambda invocation rate
- ✅ Ordering: FIFO queues available if needed

**Cons:**
- ❌ Complexity: Additional component to manage
- ❌ Cost: $0.40 per million requests
- ❌ Latency: Polling adds ~100ms

**Mitigation:**
- Use dead letter queues for failed messages
- Set appropriate visibility timeout
- Monitor DLQ with CloudWatch alarms

---

### Decision 2: DynamoDB Schema Design

**Partition Key:** document_id (UUID)

**Global Secondary Indexes:**
1. status-uploaded_at: Query by processing status
2. user_id-uploaded_at: Query by user (future)

**Why This Design:**
- Access pattern: Get document by ID
- Access pattern: List all pending documents
- Access pattern: List completed documents

**Pros:**
- Single operation to get document
- Efficient status queries
- Scalable to millions of documents

**Cons:**
- Need to project status to GSI
- Additional write cost for GSIs

---

### Decision 3: Why Textract Async API?

**Problem:** Sync vs Async Textract?

**Selection:** Async (StartDocumentAnalysis)

**Pros:**
- ✅ Handles large documents (>10 MB)
- ✅ No Lambda timeout concerns
- ✅ Better for batch processing
- ✅ Can poll for status

**Cons:**
- ❌ More complex (need to poll)
- ❌ Slower for small documents
- ❌ Need to track job IDs

**Mitigation:**
- Store job ID in DynamoDB
- Use Step Functions for complex workflows
- Set appropriate timeouts

---

### Decision 4: SNS for Notifications

**Problem:** How to notify users of completion?

**Selection:** SNS with email subscription

**Pros:**
- ✅ Multiple subscribers possible
- ✅ Fan-out to many endpoints
- ✅ Simple to set up
- ✅ Built-in retry

**Cons:**
- ❌ Email delivery can be slow
- ❌ Limited customization
- ❌ Spam folder issues

**Alternatives:**
- WebSocket for real-time
- Webhook for custom handling
- Push notifications

---

## 3. Cost Analysis

| Component | Unit Cost | Monthly (1K docs) |
|-----------|-----------|------------------|
| S3 Storage | $0.023/GB | ~$0.50 |
| Lambda | $0.20/1M req | ~$0.20 |
| SQS | $0.40/1M req | ~$0.40 |
| DynamoDB | On-demand | ~$1-3 |
| Textract | $1.50/1M pages | ~$1.50 |
| SNS | $0.50/1M notif | ~$0.50 |

**Total: ~$5-10/month** for 1000 documents

---

**Design Document Created:** 2026-03-10
EOF
```

- [ ] **Step 2: Commit**

```bash
git add stage-3-document-analysis/docs/
git commit -m "docs: add architecture design document"
```

---

## Completion Checklist

- [ ] S3 bucket with versioning
- [ ] SQS queue with DLQ
- [ ] DynamoDB table with GSIs
- [ ] Lambda processor function
- [ ] Textract integration
- [ ] SNS notifications
- [ ] Documentation complete
- [ ] Tests written

---

**Implementation Plan Created:** 2026-03-10
**Estimated Time:** 3-4 weeks
**Next:** Begin implementation
