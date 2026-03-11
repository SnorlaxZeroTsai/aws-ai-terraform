# Stage 3 Deployment Checklist

## Pre-Deployment Checklist

### Prerequisites
- [ ] AWS CLI installed and configured
- [ ] Terraform 1.0+ installed
- [ ] Python 3.11+ installed
- [ ] AWS account with Textract enabled
- [ ] Appropriate IAM permissions

### Configuration
- [ ] Copy `terraform/terraform.tfvars.template` to `terraform/terraform.tfvars`
- [ ] Update `terraform.tfvars` with your values
- [ ] Verify AWS region in `terraform.tfvars`
- [ ] Set notification email (optional)

## Deployment Steps

### 1. Initialize Terraform
```bash
cd stage-3-document-analysis/terraform
terraform init
```

**Expected Output:**
- Terraform initialized
- Provider plugins downloaded
- Backend configured

### 2. Validate Configuration
```bash
terraform validate
```

**Expected Output:**
- Success! The configuration is valid

### 3. Format Check
```bash
terraform fmt -check
```

**Expected Output:**
- All files formatted correctly

### 4. Plan Deployment
```bash
terraform plan
```

**Expected Resources to Create:**
- 1 S3 bucket (with versioning, encryption)
- 1 DynamoDB table (with GSIs)
- 1 SQS queue (processing)
- 1 SQS queue (DLQ)
- 1 SNS topic (optional)
- 2 Lambda functions (upload, analysis)
- 1 IAM role
- 5 IAM policies
- 2 CloudWatch log groups
- 1 S3 event notification
- 1 SQS trigger
- 1 Lambda permission
- 2 CloudWatch alarms

**Expected Output:**
- Plan: X to add, 0 to change, 0 to destroy

### 5. Apply Deployment
```bash
terraform apply
```

**Confirm:** Type `yes` when prompted

**Expected Output:**
- All resources created successfully
- Outputs displayed

### 6. Note Outputs
```bash
terraform output
```

**Save these values:**
- `s3_bucket_name`: For uploads
- `dynamodb_table_name`: For queries
- `sqs_queue_url`: For monitoring
- `sns_topic_arn`: For notifications
- Lambda function names: For logs

## Post-Deployment Verification

### 1. Verify S3 Bucket
```bash
aws s3 ls s3://$(terraform output s3_bucket_name)
```

**Expected:** Empty bucket or no error

### 2. Verify DynamoDB Table
```bash
aws dynamodb describe-table \
  --table-name $(terraform output dynamodb_table_name)
```

**Expected:** Table status: ACTIVE

### 3. Verify SQS Queue
```bash
aws sqs get-queue-attributes \
  --queue-url $(terraform output sqs_queue_url) \
  --attribute-names All
```

**Expected:** Queue attributes displayed

### 4. Verify Lambda Functions
```bash
aws lambda get-function-configuration \
  --function-name $(terraform output upload_function_name)

aws lambda get-function-configuration \
  --function-name $(terraform output analysis_function_name)
```

**Expected:** Function configurations displayed

### 5. Verify CloudWatch Log Groups
```bash
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/stage3
```

**Expected:** 2 log groups (upload, analysis)

## Testing

### 1. Upload Test Document
```bash
# Create test PDF
echo "Test document" > test.txt
# Or use a real PDF file

# Upload to S3
aws s3 cp test.pdf s3://$(terraform output s3_bucket_name)/uploads/test.pdf
```

### 2. Check DynamoDB
```bash
aws dynamodb scan \
  --table-name $(terraform output dynamodb_table_name)
```

**Expected:** Document with status PENDING or PROCESSING

### 3. Check Lambda Logs (Upload Handler)
```bash
aws logs tail /aws/lambda/$(terraform output upload_function_name) --follow
```

**Expected:** Logs showing document processed

### 4. Wait for Processing
```bash
# Wait 1-2 minutes for Textract to complete
sleep 120
```

### 5. Check Document Status
```bash
aws dynamodb query \
  --table-name $(terraform output dynamodb_table_name) \
  --key-condition-expression 'document_id = :id' \
  --expression-attribute-values '{":id": {"S": "<document-id>"}}'
```

**Expected:** Status: COMPLETED with results

### 6. Check Lambda Logs (Analysis Handler)
```bash
aws logs tail /aws/lambda/$(terraform output analysis_function_name) --follow
```

**Expected:** Logs showing Textract job completed

### 7. Check SQS Queue
```bash
aws sqs get-queue-attributes \
  --queue-url $(terraform output sqs_queue_url) \
  --attribute-names ApproximateNumberOfMessages
```

**Expected:** ApproximateNumberOfMessages: 0

## Monitoring Setup

### 1. Create CloudWatch Dashboard
```bash
# Navigate to CloudWatch in AWS Console
# Create new dashboard
# Add widgets for:
#   - Lambda invocations
#   - SQS queue depth
#   - DynamoDB reads/writes
```

### 2. Verify Alarms
```bash
aws cloudwatch describe-alarms \
  --alarm-names PREFIX/stage3*
```

**Expected:** 2 alarms (DLQ, errors)

### 3. Test DLQ Alarm
```bash
# Send invalid message to SQS
aws sqs send-message \
  --queue-url $(terraform output sqs_queue_url) \
  --message-body "invalid"

# Wait for Lambda to fail and retry 3 times
# Message should move to DLQ

# Check DLQ
aws sqs receive-message \
  --queue-url <dlq-url-from-outputs>
```

**Expected:** Alarm triggered

## Cleanup

### 1. Empty S3 Bucket
```bash
aws s3 rm s3://$(terraform output s3_bucket_name) --recursive
```

### 2. Destroy Infrastructure
```bash
cd terraform
terraform destroy
```

**Confirm:** Type `yes` when prompted

### 3. Verify Cleanup
```bash
# Check for remaining resources
aws s3 ls
aws dynamodb list-tables
aws lambda list-functions
```

**Expected:** No stage3 resources remaining

## Troubleshooting

### Issue: Terraform init fails
**Solution:** Check internet connection, verify AWS credentials

### Issue: Terraform apply fails
**Solution:** Check IAM permissions, review error message

### Issue: Lambda timeout
**Solution:** Increase timeout in Lambda module, check Textract limits

### Issue: Document stuck in PENDING
**Solution:** Check SQS queue, verify Lambda logs

### Issue: Textract job fails
**Solution:** Verify file format, check file size, review error message

### Issue: No SNS notification
**Solution:** Verify email subscription, check SNS topic

## Production Considerations

### 1. Enable Versioning
Already enabled by default

### 2. Enable Logging
- CloudWatch Logs: 7-day retention (default)
- S3 access logs: Optional

### 3. Enable Monitoring
- CloudWatch alarms: Created by default
- Dashboard: Manual setup

### 4. Enable Backup
- DynamoDB PITR: Enabled by default
- S3 versioning: Enabled by default

### 5. Cost Optimization
- Review Lambda memory allocation
- Optimize Textract features
- Set appropriate lifecycle policies

## Next Steps

- [ ] Deploy Stage 4 (RAG Knowledge Base)
- [ ] Add document preview generation
- [ ] Implement batch processing
- [ ] Add webhook notifications
- [ ] Create API Gateway endpoint

## Support

- AWS Documentation: https://docs.aws.amazon.com/
- Terraform Documentation: https://www.terraform.io/docs
- Project Issues: Check GitHub issues

---

**Last Updated:** 2026-03-11
**Version:** 1.0
