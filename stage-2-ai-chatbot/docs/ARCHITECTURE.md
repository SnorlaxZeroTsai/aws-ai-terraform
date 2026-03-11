# Stage 2: AI Chatbot Service - Architecture

This document provides technical details of the Stage 2 AI Chatbot Service architecture.

## System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                                │
│                    (Web, Mobile, CLI)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS POST
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REST API (Regional)                                  │  │
│  │  - POST /chat                                         │  │
│  │  - OPTIONS /chat (CORS)                               │  │
│  │  - Request validation                                 │  │
│  │  - Throttling & limits                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ AWS_PROXY Integration
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   AWS Lambda                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Python 3.11 Runtime                                  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Handler Layer (chat.py)                       │  │  │
│  │  │  - Event parsing                               │  │  │
│  │  │  - Request validation                          │  │  │
│  │  │  - Response formatting                         │  │  │
│  │  │  - Error handling                              │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Service Layer (llm_service.py)                │  │  │
│  │  │  - Bedrock client                              │  │  │
│  │  │  - Conversation management                     │  │  │
│  │  │  - Prompt building                            │  │  │
│  │  │  - Response extraction                         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Prompts Layer (chat_templates.py)             │  │  │
│  │  │  - System prompts                              │  │  │
│  │  │  - Context injection                           │  │  │
│  │  │  - History formatting                          │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Environment Variables:                                      │
│  - BEDROCK_MODEL_ID                                          │
│  - SECRET_ARN                                                │
│  - LOG_LEVEL                                                 │
└───────────┬─────────────────────────────┬────────────────────┘
            │                             │
            │                             │
            ▼                             ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│   AWS Bedrock        │      │   Secrets Manager            │
│  ┌────────────────┐  │      │  ┌────────────────────────┐  │
│  │  Claude 3      │  │      │  │  Encrypted Secrets     │  │
│  │  Sonnet        │  │      │  │  - API Keys            │  │
│  │                │  │      │  │  - Configuration       │  │
│  └────────────────┘  │      │  └────────────────────────┘  │
└──────────────────────┘      └──────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CloudWatch                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Logs                                                 │  │
│  │  - /aws/lambda/stage2-chatbot                         │  │
│  │  - API Gateway execution logs                         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Metrics                                              │  │
│  │  - Invocations, Errors, Duration                     │  │
│  │  - Throttles, ConcurrentExecutions                    │  │
│  │  - API Gateway: Count, Latency, 4XX, 5XX             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Alarms                                               │  │
│  │  - Lambda error rate                                 │  │
│  │  - Lambda duration threshold                         │  │
│  │  - API Gateway 5XX errors                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Dashboard                                            │  │
│  │  - Real-time visualization                           │  │
│  │  - Log queries                                       │  │
│  │  - Metric trends                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API Specification

### POST /chat

**Description:** Send a message to the AI chatbot and receive a response.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "string (required) - User message",
  "history": [
    {
      "role": "string (user|assistant) - Speaker role",
      "content": "string - Message content"
    }
  ], // optional - Conversation history
  "max_tokens": "number (optional) - Max response tokens (default: 1000)",
  "temperature": "number (optional) - Response creativity 0.0-1.0 (default: 0.7)"
}
```

**Success Response (200 OK):**
```json
{
  "message": "string - AI response",
  "model": "string - Model ID used"
}
```

**Error Response (4xx/5xx):**
```json
{
  "error": "string - Error message",
  "success": false
}
```

**Status Codes:**
- `200 OK` - Successful response
- `400 Bad Request` - Invalid request (missing message, invalid JSON)
- `500 Internal Server Error` - Server or Bedrock error

### OPTIONS /chat

**Description:** CORS preflight request (automatically handled).

## Data Flow

### 1. Request Processing Flow

```
Client Request
    │
    ├─→ API Gateway (REST API)
    │   ├─→ Method validation
    │   ├─→ CORS check
    │   └─→ Proxy to Lambda
    │
    ├─→ Lambda Function
    │   ├─→ handler(event, context)
    │   │   ├─→ Parse request body
    │   │   ├─→ Validate message field
    │   │   ├─→ Extract optional parameters
    │   │   └─→ Call LLM service
    │   │
    │   └─→ LLM Service
    │       ├─→ Build conversation
    │       ├─→ Get system prompt
    │       ├─→ Prepare payload
    │       ├─→ Invoke Bedrock
    │       ├─→ Extract response
    │       └─→ Return text
    │
    ├─→ Bedrock API
    │   ├─→ Validate request
    │   ├─→ Process with Claude
    │   └─→ Return response
    │
    └─→ Response Flow
        ├─→ Format response (JSON)
        ├─→ Add CORS headers
        ├─→ Return to API Gateway
        └─→ Return to client
```

### 2. Error Handling Flow

```
Error Occurs
    │
    ├─→ Catch exception in handler
    │   ├─→ Log error with context
    │   ├─→ Determine error type
    │   └─→ Return appropriate error response
    │
    ├─→ Validation Errors → 400
    │   └─→ Missing/invalid fields
    │
    ├─→ Bedrock Errors → 500
    │   ├─→ API throttling
    │   ├─→ Model unavailable
    │   └─→ Invalid response
    │
    └─→ System Errors → 500
        ├─→ Timeout
        ├─→ Out of memory
        └─→ Configuration error
```

## Infrastructure Components

### Lambda Function

**Configuration:**
- **Runtime:** Python 3.11
- **Handler:** `handlers/chat.handler`
- **Timeout:** 30 seconds
- **Memory:** 256 MB
- **Deployment Package:** ZIP with dependencies
- **Concurrent Executions:** Account default (1000)

**IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::*:foundation-model/anthropic.claude-3-sonnet-1-20240229-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:stage2-chatbot-secrets-*"
    }
  ]
}
```

### API Gateway

**Configuration:**
- **Type:** REST API (Regional)
- **Stage:** v1
- **Endpoint Type:** EDGE (optimization for global access)
- **Authorization:** NONE (Stage 2 only, will add Cognito in Stage 6)
- **Request Validation:** Disabled (validation in Lambda)

**CORS Settings:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key
Access-Control-Allow-Methods: POST,OPTIONS
```

**Stage Variables:** None (all config in environment variables)

### CloudWatch

**Log Groups:**
- `/aws/lambda/aws-ai-roadmap-stage2-chatbot`
  - Retention: 7 days
  - Format: JSON

**Metrics Collected:**
- Lambda:
  - Invocations (Sum)
  - Errors (Sum)
  - Duration (Average, p95, p99)
  - Throttles (Sum)
  - ConcurrentExecutions (Average)
- API Gateway:
  - Count (Sum)
  - Latency (Average)
  - IntegrationLatency (Average)
  - 4XXError (Sum)
  - 5XXError (Sum)

**Alarms:**
1. `stage2-chatbot-errors`: Errors > 5 in 5 minutes
2. `stage2-chatbot-duration`: Duration > 10s for 2 consecutive periods
3. `stage2-api-5xx`: 5XX errors > 10 in 5 minutes

## Security Model

### Authentication & Authorization

**Stage 2 (Current):**
- No authentication (public API)
- Suitable for learning/development

**Future Stages:**
- Stage 6: Add Amazon Cognito
- Stage 6: API Gateway authorizers
- Stage 6: JWT token validation

### Network Security

**VPC Configuration:**
- Lambda deployed in public subnets (from Stage 1)
- Direct internet access for Bedrock API
- No VPC endpoints required (can add for production)

**Security Groups:**
- Uses default VPC security group
- Outbound: All traffic allowed (for Bedrock)
- Inbound: No inbound rules (Lambda doesn't accept inbound)

### Data Security

**Encryption:**
- Secrets Manager: Automatic KMS encryption
- CloudWatch Logs: Automatic encryption
- API Gateway: TLS 1.2+ for HTTPS
- Bedrock: Encrypted in transit and at rest

**Secrets Management:**
- No credentials in code
- API keys in Secrets Manager
- IAM roles for access control
- Principle of least privilege

## Monitoring & Observability

### Logging Strategy

**Log Levels:**
- INFO: Normal operations (request received, response sent)
- ERROR: Errors and exceptions
- DEBUG: Detailed troubleshooting (enable via LOG_LEVEL)

**Log Structure:**
```json
{
  "timestamp": "2026-03-11T12:00:00.000Z",
  "level": "INFO",
  "message": "Processing chat request",
  "request_id": "123-456-789",
  "function_name": "stage2-chatbot",
  "event": {
    "body": {...},
    "headers": {...}
  }
}
```

### Metrics Strategy

**Key Performance Indicators (KPIs):**
1. **Availability:** Uptime percentage (target: 99.9%)
2. **Error Rate:** Error percentage (target: <1%)
3. **Latency:** Average response time (target: <5s)
4. **Throttling:** Throttled request count (target: 0)

**CloudWatch Dashboard Widgets:**
1. Request volume over time
2. Error rate percentage
3. P95 latency
4. Concurrent executions
5. API Gateway 4XX/5XX breakdown

### Alerting Strategy

**Alarm Actions:**
- Stage 2: CloudWatch console only
- Future: SNS notifications
- Future: PagerDuty integration

**Alarm Thresholds:**
- Errors: >5 in 5 minutes (2 evaluation periods)
- Duration: >10s average (2 evaluation periods)
- 5XX: >10 in 5 minutes (2 evaluation periods)

## Deployment

### Terraform Module Structure

```
stage-2-ai-chatbot/
├── terraform/
│   ├── main.tf                 # Root module
│   ├── variables.tf            # Root variables
│   ├── outputs.tf              # Root outputs
│   ├── provider.tf             # AWS provider
│   └── modules/
│       ├── lambda/             # Lambda module
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── api_gateway/        # API Gateway module
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── secrets_manager/    # Secrets Manager module
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       └── cloudwatch/         # CloudWatch module
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
```

### Dependencies

**External Dependencies:**
- Stage 1 VPC (via terraform_remote_state)
- AWS Bedrock service availability
- IAM permissions

**Module Dependencies:**
```
main.tf
├── secrets_manager (independent)
├── lambda (depends on: secrets_manager)
├── api_gateway (depends on: lambda)
└── cloudwatch (depends on: lambda, api_gateway)
```

### Deployment Commands

```bash
# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply

# Destroy
terraform destroy

# Format
terraform fmt

# Validate
terraform validate
```

## Testing

### Manual Testing

```bash
# Get the endpoint
ENDPOINT=$(terraform output chat_endpoint_url)

# Test basic request
curl -X POST $ENDPOINT \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello!"}'

# Test with history
curl -X POST $ENDPOINT \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "What did I just say?",
    "history": [
      {"role": "user", "content": "My name is Alice"},
      {"role": "assistant", "content": "Hello Alice!"}
    ]
  }'

# Test error handling
curl -X POST $ENDPOINT \
  -H 'Content-Type: application/json' \
  -d '{"invalid": "data"}'
```

### Automated Testing

See `/tests/api_tests.py` for automated API tests.

## Troubleshooting

### Common Issues

**1. Cold Start Latency**
- Symptom: First request takes >3 seconds
- Cause: Lambda initialization
- Solution: Use provisioned concurrency (not needed for dev)

**2. Timeout Errors**
- Symptom: 5xx response from API
- Cause: Bedrock API slow or timeout
- Solution: Increase Lambda timeout or reduce max_tokens

**3. Permission Errors**
- Symptom: 500 Internal Server Error
- Cause: IAM permissions missing
- Solution: Check CloudWatch logs, verify IAM roles

**4. Invalid Response**
- Symptom: Malformed JSON from API
- Cause: Bedrock response format changed
- Solution: Check response extraction in llm_service.py

### Debugging

**View Logs:**
```bash
# Get log group name
LOG_GROUP=$(terraform output cloudwatch_log_group_name)

# Tail logs
aws logs tail $LOG_GROUP --follow
```

**Test Lambda Locally:**
```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Invoke Lambda locally
sam local invoke "ChatFunction" -e event.json
```

**Check Bedrock Access:**
```bash
# Verify model access
aws bedrock list-foundation-models --by-provider anthropic
```

## Performance Optimization

### Lambda Optimization

**Memory vs Cost:**
- 256 MB: Good balance, ~1.5 GB/s network
- 512 MB: Faster cold starts, 2x cost
- 1024 MB: Best performance, 4x cost

**Recommendation:** Start with 256 MB, increase if needed

**Timeout Optimization:**
- Most requests complete in 2-5 seconds
- 30-second timeout handles edge cases
- Monitor P95 duration in CloudWatch

### API Gateway Optimization

**Caching (Future):**
- Enable caching for repeated queries
- Reduces Bedrock API calls
- TTL: 5 minutes for chat

**Throttling (Future):**
- Set rate limits per API key
- Prevent abuse and cost overrun
- Default: 100 requests/second

## Cost Management

### Monitoring Costs

**CloudWatch Cost Alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name stage2-cost-alarm \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum
```

### Cost Optimization

1. **Reduce Log Retention:** 7 days → 3 days for dev
2. **Disable Unused Alarms:** Set `enable_cloudwatch_alarms = false`
3. **Optimize Lambda Memory:** Test different sizes
4. **API Gateway Caching:** Enable for high-traffic scenarios

## Future Enhancements

### Stage 3 Integration
- Document upload trigger
- Async processing with SQS
- Status polling endpoint

### Stage 4 Integration
- RAG context injection
- Vector search integration
- Hybrid retrieval strategy

### Stage 5 Integration
- Tool use capabilities
- Function calling
- Agent orchestration

### Stage 6 Integration
- Multi-agent routing
- AuthN/AuthZ
- Rate limiting per user
- Custom domain name
- Multi-region deployment

---

**Document Version:** 1.0
**Last Updated:** 2026-03-11
**Maintained By:** AWS AI Learning Roadmap Project
