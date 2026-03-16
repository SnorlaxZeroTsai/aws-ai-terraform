# Stage 2: AI Chatbot Service

> **🎯 Educational Goal:** This stage teaches you serverless architecture patterns for AI applications using AWS Lambda, API Gateway, and Bedrock.

## 📚 Learning Path (Read First!)

**Before deploying anything**, read the teaching documents in order to understand the architecture decisions:

1. **[Why Serverless?](docs/00-why-serverless.md)** - Understand the value of serverless and when to use it
2. **[Lambda vs Containers vs VM](docs/01-lambda-vs-containers.md)** - Choose the right compute service for your AI application
3. **[API Gateway Choices](docs/02-api-gateway-choices.md)** - Design your API layer (REST vs HTTP vs WebSocket)
4. **[Bedrock Integration](docs/03-bedrock-integration.md)** - Integrate AI models with best practices
5. **[Secrets Management](docs/04-secrets-management.md)** - Securely manage API keys and credentials
6. **[Monitoring & Observability](docs/05-monitoring-observability.md)** - Track system health and performance
7. **[Error Handling Patterns](docs/06-error-handling-patterns.md)** - Build reliable systems with proper error handling

Each document answers the 4 critical questions:
- ✅ **Why** design it this way?
- ✅ **What** are the alternatives?
- ✅ **What** are the tradeoffs?
- ✅ **When** should we reconsider?

---

## Overview

This stage implements a complete serverless chatbot service that demonstrates:
- AWS Lambda for serverless compute
- API Gateway for REST API endpoints
- AWS Bedrock for LLM integration (Claude)
- Secrets Manager for secure credential storage
- CloudWatch for logging and monitoring

## Architecture

```
API Gateway (REST API)
    ↓ POST /chat
Lambda Function (Python)
    ↓
AWS Bedrock (Claude API)
    ↓
Response → API Gateway → Client
```

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Terraform >= 1.0
- Python 3.11+
- Stage 1 (Terraform Foundation) completed

## Quick Start

### 1. Configuration

Copy the template file and add your values:

```bash
cd terraform
cp terraform.tfvars.template terraform.tfvars
```

Edit `terraform.tfvars` with your configuration. The minimal required values are already set as defaults.

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan the Deployment

```bash
terraform plan
```

Review the plan to ensure all resources will be created correctly.

### 4. Deploy

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 5. Test the API

After deployment completes, Terraform will output the API endpoint. Test it:

```bash
# Get the endpoint from Terraform outputs
terraform output chat_endpoint_url

# Test with curl
curl -X POST $(terraform output chat_endpoint_url) \
  -H 'Content-Type: application/json' \
  -d '{"message": "Hello! What can you do?"}'
```

## Project Structure

```
stage-2-ai-chatbot/
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # Main configuration
│   ├── variables.tf       # Variable definitions
│   ├── outputs.tf         # Output values
│   ├── provider.tf        # AWS provider
│   └── modules/           # Reusable modules
│       ├── lambda/        # Lambda function module
│       ├── api_gateway/   # API Gateway module
│       ├── secrets_manager/ # Secrets Manager module
│       └── cloudwatch/    # Monitoring module
├── src/                    # Application code
│   ├── handlers/
│   │   └── chat.py        # Lambda entry point
│   ├── services/
│   │   └── llm_service.py # Bedrock integration
│   ├── prompts/
│   │   └── chat_templates.py # System prompts
│   └── utils/
│       └── response.py    # Response utilities
├── tests/
│   └── api_tests.py       # API tests
└── docs/
    ├── design.md          # Architecture decisions
    └── ARCHITECTURE.md    # Technical details
```

## Configuration

### Variables

Key variables in `terraform.tfvars`:

- `aws_region`: AWS region (default: us-east-1)
- `environment`: Environment name (default: dev)
- `bedrock_model_id`: Claude model to use
- `lambda_timeout`: Lambda timeout in seconds
- `lambda_memory_size`: Lambda memory in MB
- `cloudwatch_log_retention`: Log retention days

### Environment Variables

The Lambda function uses these environment variables:
- `BEDROCK_MODEL_ID`: Claude model ID
- `SECRET_ARN`: Secrets Manager secret ARN
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## API Usage

### Endpoint: POST /chat

**Request:**
```json
{
  "message": "Your message here",
  "history": [],  // Optional conversation history
  "max_tokens": 1000,  // Optional
  "temperature": 0.7   // Optional
}
```

**Response:**
```json
{
  "message": "Claude's response",
  "model": "anthropic.claude-3-sonnet-1-20240229-v1:0"
}
```

**Error Response:**
```json
{
  "error": "Error message",
  "success": false
}
```

## Monitoring

### CloudWatch Dashboard

Access the dashboard:
```bash
terraform output cloudwatch_dashboard_url
```

The dashboard includes:
- Lambda invocation metrics
- Error rates
- Duration statistics
- API Gateway metrics
- Log streams

### Alarms

The following alarms are configured:
- Lambda error rate
- Lambda duration threshold
- API Gateway 5XX errors

## Cost Estimation

Estimated monthly costs (us-east-1, dev environment):

- Lambda: ~$0.00 (within free tier)
- API Gateway: ~$0.00 (within free tier)
- CloudWatch Logs: ~$0.50 (1M requests)
- CloudWatch Alarms: ~$0.00 (3 alarms)
- **Total**: ~$0.50/month

Note: Actual costs depend on usage. See `/scripts/cost-estimate.sh` for detailed estimation.

## Troubleshooting

### Lambda Timeout

If you're getting timeouts:
1. Increase `lambda_timeout` in variables
2. Check Bedrock API latency in CloudWatch
3. Consider reducing `max_tokens` in requests

### API Gateway Errors

Check CloudWatch logs:
```bash
aws logs tail /aws/lambda/$(terraform output lambda_function_name) --follow
```

### Permission Errors

Ensure your AWS credentials have permissions for:
- Lambda
- API Gateway
- Bedrock
- Secrets Manager
- CloudWatch

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

## Next Steps

- Stage 3: Document Analysis System
- Add authentication (Cognito)
- Implement rate limiting
- Add conversation persistence (DynamoDB)

## Learning Objectives

After completing this stage, you should understand:
1. Serverless architecture benefits and tradeoffs
2. Lambda function configuration and deployment
3. API Gateway REST API setup
4. AWS Bedrock integration
5. CloudWatch monitoring and alerting
6. Secrets Manager for secure storage

## Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform state: `terraform show`
3. Validate configuration: `terraform validate`
4. Check AWS Service Health Dashboard
