# Stage 2: AI Chatbot Service - Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a serverless AI chatbot API using AWS Lambda, API Gateway, and Bedrock Claude, demonstrating modern cloud architecture patterns for AI applications.

**Architecture:** API Gateway provides REST endpoint → Lambda function handles chat logic → Bedrock Claude API generates responses → CloudWatch logs and monitors.

**Tech Stack:** Terraform, AWS Lambda (Python), API Gateway, Bedrock Claude, Secrets Manager, CloudWatch, Python 3.11

---

## Chunk 1: Project Setup and Dependencies

### Task 1: Create Stage Directory Structure

**Files:**
- Create: `stage-2-ai-chatbot/README.md`
- Create: `stage-2-ai-chatbot/terraform/main.tf`
- Create: `stage-2-ai-chatbot/terraform/variables.tf`
- Create: `stage-2-ai-chatbot/terraform/outputs.tf`
- Create: `stage-2-ai-chatbot/terraform/provider.tf`
- Create: `stage-2-ai-chatbot/.gitignore`
- Create: `stage-2-ai-chatbot/requirements.txt`
- Create: `stage-2-ai-chatbot/src/handlers/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p stage-2-ai-chatbot/terraform/modules/{lambda,api_gateway,secrets_manager,cloudwatch}
mkdir -p stage-2-ai-chatbot/src/{handlers,services,prompts,utils}
mkdir -p stage-2-ai-chatbot/tests
mkdir -p stage-2-ai-chatbot/docs
```

- [ ] **Step 2: Create .gitignore**

```bash
cat > stage-2-ai-chatbot/.gitignore << 'EOF'
# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfbackup
.terraform.tfstate.lock.info

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local

# Testing
.pytest_cache/
.coverage
htmlcov/
EOF
```

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
      Stage     = "2-chatbot"
      ManagedBy = "Terraform"
    }
  }
}

# Data source for VPC from Stage 1
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
  description = "Environment name"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "api_name" {
  description = "Name for the API Gateway"
  type        = string
  default     = "ai-chatbot"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_memory_size" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 256

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Memory must be between 128 and 10240 MB."
  }
}

variable "bedrock_model_id" {
  description = "Bedrock model ID"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"

  validation {
    condition     = can(regex("^anthropic\\.", var.bedrock_model_id))
    error_message = "Model ID must be a valid Bedrock model identifier."
  }
}

variable "max_tokens" {
  description = "Maximum tokens in response"
  type        = number
  default     = 1000

  validation {
    condition     = var.max_tokens >= 1 && var.max_tokens <= 4096
    error_message = "Max tokens must be between 1 and 4096."
  }
}

variable "enable_api_key_auth" {
  description = "Enable API key authentication"
  type        = bool
  default     = true
}
```

- [ ] **Step 5: Create outputs.tf**

```hcl
output "api_endpoint_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.endpoint_url
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = module.lambda.function_arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = module.cloudwatch.log_group_name
}
```

- [ ] **Step 6: Create initial main.tf**

```hcl
# Stage 2: AI Chatbot Service
# Modules will be added as we build
```

- [ ] **Step 7: Create requirements.txt**

```bash
cat > stage-2-ai-chatbot/requirements.txt << 'EOF'
# AWS SDK
boto3==1.34.84
botocore==1.34.84

# HTTP
requests==2.31.0

# Validation
pydantic==2.6.1
pydantic-settings==2.1.0

# Utilities
python-dotenv==1.0.1

# Testing
pytest==8.0.2
pytest-mock==3.12.0
pytest-cov==4.1.0
moto==5.0.2

# Lambda dependencies (for local testing)
awslambdaric==2.0.9
EOF
```

- [ ] **Step 8: Create README.md**

```bash
cat > stage-2-ai-chatbot/README.md << 'EOF'
# Stage 2: AI Chatbot Service

## Learning Objectives

After completing this stage, you will be able to:
- [ ] Design serverless architectures with Lambda and API Gateway
- [ ] Integrate LLM APIs (Bedrock Claude) into applications
- [ ] Implement secure secrets management
- [ ] Set up CloudWatch monitoring and logging
- [ ] Understand serverless trade-offs vs containers

## Architecture Overview

```
┌─────────┐      ┌──────────────┐      ┌──────────┐      ┌─────────┐
│  User   │ ───> │ API Gateway  │ ───> │  Lambda  │ ───> │ Bedrock │
└─────────┘      └──────────────┘      └──────────┘      └─────────┘
                                              │
                                              ↓
                                        ┌──────────┐
                                        │CloudWatch│
                                        └──────────┘
                                              ↑
                                        ┌──────────┐
                                        │ Secrets  │
                                        │ Manager  │
                                        └──────────┘
```

## Prerequisites

- Completed Stage 1 (for VPC infrastructure)
- AWS Account with Bedrock enabled
- Python 3.11+
- Terraform 1.0+

## Design Decisions

See [docs/design.md](docs/design.md) for detailed architecture decisions including:
- Why Lambda vs ECS vs EC2
- Why API Gateway vs ALB
- Cold start mitigation strategies
- Cost analysis and optimization

## Deployment

### 1. Set up Python environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Bedrock access

Ensure your account has:
- Bedrock enabled in the region
- IAM permissions for bedrock:InvokeModel
- Model access for Claude

### 3. Deploy infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. Test the API

```bash
# Get API endpoint
API_URL=$(terraform output -raw api_endpoint_url)

# Test chat endpoint
curl -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "message": "Hello, how are you?",
    "conversation_id": "test-123"
  }'
```

## API Reference

### POST /chat

Send a message to the chatbot.

**Request:**
```json
{
  "message": "User message here",
  "conversation_id": "optional-conversation-id",
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "AI response here",
  "conversation_id": "conv-uuid",
  "model": "anthropic.claude-3-sonnet-20240229-v1:0",
  "tokens_used": {
    "input": 10,
    "output": 50,
    "total": 60
  },
  "timestamp": "2024-03-10T12:00:00Z"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run integration tests (requires deployed resources)
pytest tests/integration/ -v
```

## Monitoring

```bash
# View logs
aws logs tail /aws/lambda/ai-chatbot --follow

# View metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ai-chatbot
```

## Cost Estimate

| Resource | Cost |
|----------|------|
| Lambda | ~$0.20 per 1M requests |
| API Gateway | ~$3.50 per 1M API calls |
| Bedrock Claude | ~$3 per 1M input tokens, ~$15 per 1M output tokens |
| CloudWatch Logs | ~$0.50 per GB ingested |

**Estimated monthly cost:** $5-20 for moderate usage

## Cleanup

```bash
cd terraform
terraform destroy
```

## Troubleshooting

### Common Issues

**Issue: Lambda timeout**
- Increase timeout in variables.tf
- Optimize prompt size
- Check Bedrock service health

**Issue: Cold starts > 5 seconds**
- Enable Provisioned Concurrency
- Reduce package size
- Optimize initialization code

**Issue: API key authentication failing**
- Verify API key is created
- Check API Gateway settings
- Review CloudWatch logs

## Next Steps

After completing this stage:
1. Review architecture decisions in `docs/design.md`
2. Experiment with different prompts and parameters
3. Add conversation history persistence
4. Proceed to Stage 3: Document Analysis System
EOF
```

- [ ] **Step 9: Create Python package structure**

```bash
touch stage-2-ai-chatbot/src/__init__.py
touch stage-2-ai-chatbot/src/handlers/__init__.py
touch stage-2-ai-chatbot/src/services/__init__.py
touch stage-2-ai-chatbot/src/prompts/__init__.py
touch stage-2-ai-chatbot/src/utils/__init__.py
```

- [ ] **Step 10: Commit initial structure**

```bash
git add stage-2-ai-chatbot/
git commit -m "feat: stage-2 initial project structure"
```

---

## Chunk 2: Lambda Module

### Task 2: Create Lambda Infrastructure

**Files:**
- Create: `stage-2-ai-chatbot/terraform/modules/lambda/main.tf`
- Create: `stage-2-ai-chatbot/terraform/modules/lambda/variables.tf`
- Create: `stage-2-ai-chatbot/terraform/modules/lambda/outputs.tf`

- [ ] **Step 1: Create Lambda module main.tf**

```hcl
# Archive the Lambda function code
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

# Lambda execution role
data "aws_iam_policy_document" "lambda_assume_role" {
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
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = var.tags
}

# IAM policy for Lambda
data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "bedrock:InvokeModel"
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = var.secrets_arn != null ? [var.secrets_arn] : []
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${var.function_name}-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}

# Lambda function
resource "aws_lambda_function" "this" {
  function_name    = var.function_name
  description      = "AI Chatbot handler using Bedrock Claude"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.chat.handler"
  runtime          = "python3.11"
  timeout          = var.timeout
  memory_size      = var.memory_size
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  filename         = data.archive_file.lambda_zip.output_path

  environment {
    variables = {
      AWS_REGION                  = var.aws_region
      BEDROCK_MODEL_ID            = var.bedrock_model_id
      MAX_TOKENS                  = var.max_tokens
      LOG_LEVEL                   = var.log_level
      SECRETS_ARN                 = try(var.secrets_arn, "")
      ENVIRONMENT                = var.environment
    }
  }

  tags = var.tags

  depends_on = [
    aws_iam_role_policy.lambda,
    aws_cloudwatch_log_group.this
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.arn
  principal     = "apigateway.amazonaws.com"

  source_arn = "${var.api_execution_arn}/*"
}

# Reserved concurrency (optional, for cost control)
resource "aws_lambda_provisioned_concurrency_config" "this" {
  count = var.provisioned_concurrency > 0 ? 1 : 0

  function_name                     = aws_lambda_function.this.function_name
  provisioned_concurrent_executions = var.provisioned_concurrency

  qualifiers = ["$LATEST"]
}
```

- [ ] **Step 2: Create Lambda module variables.tf**

```hcl
variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 256
}

variable "bedrock_model_id" {
  description = "Bedrock model ID"
  type        = string
}

variable "max_tokens" {
  description = "Maximum tokens in response"
  type        = number
  default     = 1000
}

variable "log_level" {
  description = "Log level"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, or ERROR."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch retention period."
  }
}

variable "api_execution_arn" {
  description = "API Gateway execution ARN"
  type        = string
}

variable "secrets_arn" {
  description = "Secrets Manager secret ARN"
  type        = string
  default     = null
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "provisioned_concurrency" {
  description = "Provisioned concurrency units"
  type        = number
  default     = 0
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create Lambda module outputs.tf**

```hcl
output "function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.this.function_name
}

output "function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.this.arn
}

output "invoke_arn" {
  description = "Lambda invoke ARN"
  value       = aws_lambda_function.this.invoke_arn
}

output "role_arn" {
  description = "Lambda IAM role ARN"
  value       = aws_iam_role.lambda.arn
}
```

- [ ] **Step 4: Update main.tf to reference Lambda module**

```hcl
# Add to main.tf:

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  function_name    = "${var.api_name}-lambda"
  aws_region       = var.aws_region
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  bedrock_model_id = var.bedrock_model_id
  max_tokens       = var.max_tokens
  environment      = var.environment

  api_execution_arn = module.api_gateway.execution_arn
  secrets_arn       = try(module.secrets_manager.secret_arn, null)

  tags = {
    Stage = "2-chatbot"
  }
}
```

- [ ] **Step 5: Validate Terraform**

```bash
cd stage-2-ai-chatbot/terraform
terraform fmt
terraform validate
```

- [ ] **Step 6: Commit Lambda module**

```bash
git add stage-2-ai-chatbot/terraform/modules/lambda
git commit -m "feat: add Lambda module with CloudWatch logging"
```

---

## Chunk 3: API Gateway Module

### Task 3: Create API Gateway Infrastructure

**Files:**
- Create: `stage-2-ai-chatbot/terraform/modules/api_gateway/main.tf`
- Create: `stage-2-ai-chatbot/terraform/modules/api_gateway/variables.tf`
- Create: `stage-2-ai-chatbot/terraform/modules/api_gateway/outputs.tf`

- [ ] **Step 1: Create API Gateway module main.tf**

```hcl
# REST API
resource "aws_api_gateway_rest_api" "this" {
  name        = var.api_name
  description = "AI Chatbot API"
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# API Resource: /chat
resource "aws_api_gateway_resource" "chat" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "chat"
}

# API Resource: /health
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "health"
}

# POST Method for /chat
resource "aws_api_gateway_method" "chat_post" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_resource.chat.id
  http_method   = "POST"
  authorization = var.authorization_type

  dynamic "authorizer_id" {
    for_each = var.authorization_type == "CUSTOM" ? [1] : []
    content {
      authorizer_id = aws_api_gateway_authorizer.api_key[0].id
    }
  }
}

# GET Method for /health
resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
}

# Integration for /chat POST
resource "aws_api_gateway_integration" "chat_post" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.chat.id
  http_method = aws_api_gateway_method.chat_post.http_method

  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# Integration for /health GET
resource "aws_api_gateway_integration" "health_get" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method

  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = var.lambda_invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id

  triggers = {
    redployment = sha1(jsonencode([
      aws_api_gateway_resource.chat.id,
      aws_api_gateway_resource.health.id,
      aws_api_gateway_method.chat_post.id,
      aws_api_gateway_method.health_get.id,
      aws_api_gateway_integration.chat_post.id,
      aws_api_gateway_integration.health_get.id
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "this" {
  deployment_id = aws_api_gateway_deployment.this.id
  rest_api_id   = aws_api_gateway_rest_api.this.id
  stage_name    = var.stage_name

  tags = var.tags
}

# API Key (if enabled)
resource "aws_api_gateway_api_key" "this" {
  count = var.enable_api_key ? 1 : 0

  name = "${var.api_name}-api-key"

  tags = var.tags
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "this" {
  count = var.enable_api_key ? 1 : 0

  name = "${var.api_name}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.this.id
    stage  = aws_api_gateway_stage.this.stage_name
  }

  throttle_settings {
    rate_limit  = var.throttle_rate_limit
    burst_limit = var.throttle_burst_limit
  }

  quota_settings {
    limit  = var.quota_limit
    offset = var.quota_offset
    period = var.quota_period
  }
}

# API Key association
resource "aws_api_gateway_usage_plan_key" "this" {
  count = var.enable_api_key ? 1 : 0

  key_id        = aws_api_gateway_api_key.this[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.this[0].id
}

# API Key Authorizer (if enabled)
resource "aws_api_gateway_authorizer" "api_key" {
  count = var.enable_api_key ? 1 : 0

  name                   = "api-key-authorizer"
  rest_api_id            = aws_api_gateway_rest_api.this.id
  authorizer_uri         = var.lambda_invoke_arn
  authorizer_credentials = var.api_key_authorizer_role_arn
  type                   = "REQUEST"
}
```

- [ ] **Step 2: Create API Gateway module variables.tf**

```hcl
variable "api_name" {
  description = "API Gateway name"
  type        = string
}

variable "stage_name" {
  description = "Deployment stage name"
  type        = string
  default     = "v1"
}

variable "lambda_invoke_arn" {
  description = "Lambda invoke ARN"
  type        = string
}

variable "authorization_type" {
  description = "API Gateway authorization type"
  type        = string
  default     = "NONE"

  validation {
    condition     = contains(["NONE", "AWS_IAM", "CUSTOM"], var.authorization_type)
    error_message = "Authorization must be NONE, AWS_IAM, or CUSTOM."
  }
}

variable "enable_api_key" {
  description = "Enable API key authentication"
  type        = bool
  default     = false
}

variable "api_key_authorizer_role_arn" {
  description = "IAM role ARN for API key authorizer"
  type        = string
  default     = null
}

variable "throttle_rate_limit" {
  description = "Throttle rate limit"
  type        = number
  default     = 10
}

variable "throttle_burst_limit" {
  description = "Throttle burst limit"
  type        = number
  default     = 20
}

variable "quota_limit" {
  description = "Usage plan quota limit"
  type        = number
  default     = 1000
}

variable "quota_offset" {
  description = "Usage plan quota offset"
  type        = number
  default     = 0
}

variable "quota_period" {
  description = "Usage plan quota period"
  type        = string
  default     = "MONTH"

  validation {
    condition     = contains(["DAY", "WEEK", "MONTH"], var.quota_period)
    error_message = "Period must be DAY, WEEK, or MONTH."
  }
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create API Gateway module outputs.tf**

```hcl
output "api_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.this.id
}

output "api_endpoint_url" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_rest_api.this.invoke_url}/${aws_api_gateway_stage.this.stage_name}"
}

output "execution_arn" {
  description = "API Gateway execution ARN"
  value       = aws_api_gateway_rest_api.this.execution_arn
}

output "api_key" {
  description = "API key value (sensitive)"
  value       = try(aws_api_gateway_api_key.this[0].value, null)
  sensitive   = true
}

output "api_key_id" {
  description = "API key ID"
  value       = try(aws_api_gateway_api_key.this[0].id, null)
}
```

- [ ] **Step 4: Update main.tf**

```hcl
# Add to main.tf:

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  api_name        = var.api_name
  lambda_invoke_arn = module.lambda.invoke_arn

  authorization_type = var.enable_api_key_auth ? "CUSTOM" : "NONE"
  enable_api_key     = var.enable_api_key_auth

  tags = {
    Stage = "2-chatbot"
  }
}
```

- [ ] **Step 5: Add API key variables**

```hcl
# Add to variables.tf:

variable "throttle_rate_limit" {
  description = "API throttle rate limit per second"
  type        = number
  default     = 10
}

variable "throttle_burst_limit" {
  description = "API throttle burst limit"
  type        = number
  default     = 20
}

variable "quota_limit" {
  description = "API quota limit per period"
  type        = number
  default     = 10000
}

variable "quota_period" {
  description = "API quota period"
  type        = string
  default     = "MONTH"

  validation {
    condition     = contains(["DAY", "WEEK", "MONTH"], var.quota_period)
    error_message = "Period must be DAY, WEEK, or MONTH."
  }
}
```

- [ ] **Step 6: Validate and commit**

```bash
terraform fmt
terraform validate

git add stage-2-ai-chatbot/terraform/modules/api_gateway
git add stage-2-ai-chatbot/terraform/main.tf stage-2-ai-chatbot/terraform/variables.tf
git commit -m "feat: add API Gateway with chat and health endpoints"
```

---

## Chunk 4: Secrets Manager Module

### Task 4: Create Secrets Manager Infrastructure

**Files:**
- Create: `stage-2-ai-chatbot/terraform/modules/secrets_manager/main.tf`
- Create: `stage-2-ai-chatbot/terraform/modules/secrets_manager/variables.tf`
- Create: `stage-2-ai-chatbot/terraform/modules/secrets_manager/outputs.tf`

- [ ] **Step 1: Create Secrets Manager module main.tf**

```hcl
# Random password for API key
resource "random_password" "api_key" {
  count = var.create_api_key_secret ? 1 : 0

  length  = 32
  special = false
}

# Secret for API key
resource "aws_secretsmanager_secret" "api_key" {
  count = var.create_api_key_secret ? 1 : 0

  name                    = "${var.secret_prefix}/api-key"
  description             = "API key for chatbot authentication"
  recovery_window_in_days = var.recovery_window_days

  tags = var.tags
}

# Secret version
resource "aws_secretsmanager_secret_version" "api_key" {
  count = var.create_api_key_secret ? 1 : 0

  secret_id = aws_secretsmanager_secret.api_key[0].id
  secret_string = jsonencode({
    api_key = random_password.api_key[0].result
  })
}

# Secret for Bedrock (optional, for custom endpoint)
resource "aws_secretsmanager_secret" "bedrock" {
  count = var.create_bedrock_secret ? 1 : 0

  name                    = "${var.secret_prefix}/bedrock-config"
  description             = "Bedrock configuration"
  recovery_window_in_days = var.recovery_window_days

  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "bedrock" {
  count = var.create_bedrock_secret ? 1 : 0

  secret_id = aws_secretsmanager_secret.bedrock[0].id
  secret_string = jsonencode({
    endpoint_url = try(var.bedrock_endpoint_url, "")
    api_key      = try(var.bedrock_api_key, "")
  })
}
```

- [ ] **Step 2: Create Secrets Manager module variables.tf**

```hcl
variable "secret_prefix" {
  description = "Prefix for secret names"
  type        = string
}

variable "create_api_key_secret" {
  description = "Create API key secret"
  type        = bool
  default     = true
}

variable "create_bedrock_secret" {
  description = "Create Bedrock config secret"
  type        = bool
  default     = false
}

variable "bedrock_endpoint_url" {
  description = "Custom Bedrock endpoint URL"
  type        = string
  default     = null
}

variable "bedrock_api_key" {
  description = "Bedrock API key (if using custom endpoint)"
  type        = string
  default     = null
  sensitive   = true
}

variable "recovery_window_days" {
  description = "Days to retain deleted secret"
  type        = number
  default     = 30

  validation {
    condition     = var.recovery_window_days >= 0 && var.recovery_window_days <= 30
    error_message = "Recovery window must be between 0 and 30 days."
  }
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create Secrets Manager module outputs.tf**

```hcl
output "secret_arn" {
  description = "Primary secret ARN"
  value       = try(aws_secretsmanager_secret.api_key[0].arn, null)
}

output "api_key" {
  description = "Generated API key"
  value       = try(random_password.api_key[0].result, null)
  sensitive   = true
}
```

- [ ] **Step 4: Update main.tf**

```hcl
# Add to main.tf:

# Secrets Manager Module
module "secrets_manager" {
  source = "./modules/secrets_manager"

  secret_prefix = "ai-chatbot/${var.environment}"

  create_api_key_secret = var.enable_api_key_auth

  tags = {
    Stage = "2-chatbot"
  }
}
```

- [ ] **Step 5: Validate and commit**

```bash
terraform fmt
terraform validate

git add stage-2-ai-chatbot/terraform/modules/secrets_manager stage-2-ai-chatbot/terraform/main.tf
git commit -m "feat: add Secrets Manager for secure credentials"
```

---

## Chunk 5: Lambda Function Implementation

### Task 5: Create Chat Handler

**Files:**
- Create: `stage-2-ai-chatbot/src/handlers/chat.py`
- Create: `stage-2-ai-chatbot/src/services/llm_service.py`
- Create: `stage-2-ai-chatbot/src/prompts/chat_templates.py`
- Create: `stage-2-ai-chatbot/src/utils/logger.py`
- Create: `stage-2-ai-chatbot/src/utils/response.py`

- [ ] **Step 1: Create logger utility**

```bash
cat > stage-2-ai-chatbot/src/utils/logger.py << 'EOF'
import logging
import os
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for CloudWatch"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Get configured logger"""
    logger = logging.getLogger(name)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger
EOF
```

- [ ] **Step 2: Create response utility**

```bash
cat > stage-2-ai-chatbot/src/utils/response.py << 'EOF'
from typing import Any, Dict
from http import HTTPStatus

def create_response(
    status_code: int,
    body: Any,
    headers: Dict[str, str] = None
) -> Dict[str, Any]:
    """Create API Gateway response"""

    response = {
        "statusCode": status_code,
        "body": json.dumps(body) if isinstance(body, (dict, list)) else body,
    }

    if headers:
        response["headers"] = headers
    else:
        response["headers"] = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }

    return response

def success_response(data: Any) -> Dict[str, Any]:
    """Create success response"""
    return create_response(HTTPStatus.OK, data)

def error_response(
    message: str,
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
    error_code: str = None
) -> Dict[str, Any]:
    """Create error response"""
    body = {"error": message}

    if error_code:
        body["error_code"] = error_code

    return create_response(status_code, body)

def validation_error(errors: Dict[str, str]) -> Dict[str, Any]:
    """Create validation error response"""
    return error_response(
        "Validation failed",
        HTTPStatus.BAD_REQUEST,
        "VALIDATION_ERROR"
    )
EOF
```

- [ ] **Step 3: Create chat templates**

```bash
cat > stage-2-ai-chatbot/src/prompts/chat_templates.py << 'EOF'
from typing import Dict, Any

DEFAULT_SYSTEM_PROMPT = """You are Claude, a helpful AI assistant created by Anthropic.

You are designed to be:
- Helpful: Provide accurate, useful information
- Harmless: Avoid generating harmful content
- Honest: Be truthful and acknowledge uncertainty

Keep responses concise and relevant to the user's question."""

CHAT_TEMPLATE = """{system_prompt}

Human: {user_message}

Assistant:"""

def build_chat_prompt(
    user_message: str,
    system_prompt: str = None,
    conversation_history: list = None
) -> str:
    """Build chat prompt with optional history"""

    system = system_prompt or DEFAULT_SYSTEM_PROMPT

    if conversation_history:
        # Build conversation from history
        messages = [f"Human: {msg['user']}\nAssistant: {msg['assistant']}"
                   for msg in conversation_history[-5:]]  # Last 5 exchanges
        messages.append(f"Human: {user_message}")
        return f"{system}\n\n" + "\n\n".join(messages)

    return CHAT_TEMPLATE.format(
        system_prompt=system,
        user_message=user_message
    )

def extract_system_prompt(config: Dict[str, Any]) -> str:
    """Extract system prompt from config"""
    return config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
EOF
```

- [ ] **Step 4: Create LLM service**

```bash
cat > stage-2-ai-chatbot/src/services/llm_service.py << 'EOF'
import boto3
import json
import os
from typing import Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    """Service for interacting with Bedrock Claude"""

    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))

    def invoke_claude(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        stop_sequences: list = None
    ) -> Dict[str, Any]:
        """Invoke Claude model"""

        logger.info("Invoking Claude model", extra_data={
            "model": self.model_id,
            "prompt_length": len(prompt)
        })

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
        }

        if stop_sequences:
            request_body["stop_sequences"] = stop_sequences

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response["body"].read())

            logger.info("Claude invocation successful", extra_data={
                "input_tokens": response_body.get("usage", {}).get("input_tokens"),
                "output_tokens": response_body.get("usage", {}).get("output_tokens")
            })

            return {
                "response": response_body["content"][0]["text"],
                "model": self.model_id,
                "tokens_used": response_body.get("usage", {}),
                "stop_reason": response_body.get("stop_reason")
            }

        except Exception as e:
            logger.error("Claude invocation failed", extra_data={"error": str(e)})
            raise

    def stream_claude(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = 0.7
    ):
        """Stream Claude responses"""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens or self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            for event in response["body"]:
                chunk = json.loads(event["value"]["chunk"]["bytes"])
                if "delta" in chunk and "text" in chunk["delta"]:
                    yield chunk["delta"]["text"]

        except Exception as e:
            logger.error("Claude stream failed", extra_data={"error": str(e)})
            raise
EOF
```

- [ ] **Step 5: Create main chat handler**

```bash
cat > stage-2-ai-chatbot/src/handlers/chat.py << 'EOF'
import json
import uuid
import os
from typing import Dict, Any
from datetime import datetime

from ..services.llm_service import LLMService
from ..prompts.chat_templates import build_chat_prompt
from ..utils.response import success_response, error_response, validation_error
from ..utils.logger import get_logger

logger = get_logger(__name__)
llm_service = LLMService()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for chat endpoint"""

    logger.info("Chat request received", extra_data={
        "request_id": context.request_id if context else "local"
    })

    try:
        # Parse request
        body = parse_event_body(event)
        validated = validate_request(body)

        if "errors" in validated:
            return validation_error(validated["errors"])

        # Build prompt
        prompt = build_chat_prompt(
            user_message=validated["message"],
            system_prompt=validated.get("system_prompt"),
            conversation_history=validated.get("conversation_history")
        )

        # Invoke LLM
        result = llm_service.invoke_claude(
            prompt=prompt,
            max_tokens=validated.get("max_tokens"),
            temperature=validated.get("temperature", 0.7)
        )

        # Build response
        response_data = {
            "response": result["response"],
            "conversation_id": validated.get("conversation_id", str(uuid.uuid4())),
            "model": result["model"],
            "tokens_used": result["tokens_used"],
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info("Chat request successful", extra_data={
            "conversation_id": response_data["conversation_id"],
            "tokens_used": result["tokens_used"]
        })

        return success_response(response_data)

    except ValueError as e:
        logger.error("Validation error", extra_data={"error": str(e)})
        return error_response(str(e), 400, "VALIDATION_ERROR")

    except Exception as e:
        logger.error("Chat request failed", extra_data={"error": str(e)})
        return error_response("Internal server error", 500, "INTERNAL_ERROR")

def parse_event_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse event body from API Gateway or Lambda test"""

    if "body" in event:
        if isinstance(event["body"], str):
            return json.loads(event["body"])
        return event["body"]

    return event

def validate_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate request data"""

    errors = {}
    result = {}

    # Required: message
    if "message" not in data or not data["message"].strip():
        errors["message"] = "Message is required and cannot be empty"
    else:
        result["message"] = data["message"].strip()

    # Optional: conversation_id
    if "conversation_id" in data:
        result["conversation_id"] = data["conversation_id"]

    # Optional: max_tokens
    if "max_tokens" in data:
        max_tokens = data["max_tokens"]
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 4096:
            errors["max_tokens"] = "Must be between 1 and 4096"
        else:
            result["max_tokens"] = max_tokens

    # Optional: temperature
    if "temperature" in data:
        temp = data["temperature"]
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 1:
            errors["temperature"] = "Must be between 0 and 1"
        else:
            result["temperature"] = float(temp)

    # Optional: system_prompt
    if "system_prompt" in data:
        result["system_prompt"] = data["system_prompt"]

    # Optional: conversation_history
    if "conversation_history" in data:
        history = data["conversation_history"]
        if isinstance(history, list):
            result["conversation_history"] = history

    if errors:
        return {"errors": errors}

    return result
EOF
```

- [ ] **Step 6: Create health handler**

```bash
cat > stage-2-ai-chatbot/src/handlers/health.py << 'EOF'
import os
from datetime import datetime
from ..utils.response import success_response
from ..utils.logger import get_logger

logger = get_logger(__name__)

def handler(event, context) -> dict:
    """Health check handler"""

    logger.info("Health check requested")

    return success_response({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "region": os.getenv("AWS_REGION"),
        "environment": os.getenv("ENVIRONMENT", "dev")
    })
EOF
```

- [ ] **Step 7: Create router**

```bash
cat > stage-2-ai-chatbot/src/handlers/router.py << 'EOF'
import json
from .chat import handler as chat_handler
from .health import handler as health_handler

def handler(event, context):
    """Route requests to appropriate handler"""

    path = event.get("path", "")
    http_method = event.get("httpMethod", "")

    if path.endswith("/chat") and http_method == "POST":
        return chat_handler(event, context)
    elif path.endswith("/health") and http_method == "GET":
        return health_handler(event, context)
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Not found"})
        }
EOF
```

- [ ] **Step 8: Update main handler**

```bash
cat > stage-2-ai-chatbot/src/handlers/handler.py << 'EOF'
from .router import handler

# Lambda entry point
lambda_handler = handler
EOF
```

- [ ] **Step 9: Commit Lambda code**

```bash
git add stage-2-ai-chatbot/src/
git commit -m "feat: implement chat and health handlers with LLM service"
```

---

## Chunk 6: Testing

### Task 6: Create Tests

**Files:**
- Create: `stage-2-ai-chatbot/tests/test_handlers.py`
- Create: `stage-2-ai-chatbot/tests/test_llm_service.py`
- Create: `stage-2-ai-chatbot/tests/conftest.py`
- Create: `stage-2-ai-chatbot/tests/__init__.py`

- [ ] **Step 1: Create test configuration**

```bash
cat > stage-2-ai-chatbot/tests/conftest.py << 'EOF'
import pytest
import os
from unittest.mock import Mock

@pytest.fixture
def mock_bedrock_response():
    """Mock Bedrock response"""
    return {
        "body": Mock(
            read=lambda: b'{"content":[{"text":"Hello! How can I help you today?"}],"usage":{"input_tokens":10,"output_tokens":9},"stop_reason":"end_turn"}'
        )
    }

@pytest.fixture
def mock_event():
    """Mock API Gateway event"""
    return {
        "path": "/v1/chat",
        "httpMethod": "POST",
        "body": json.dumps({
            "message": "Hello"
        }),
        "headers": {
            "Content-Type": "application/json"
        }
    }

@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = Mock()
    context.request_id = "test-request-id"
    context.function_name = "test-function"
    return context

def pytest_configure(config):
    """Configure pytest"""
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"
    os.environ["MAX_TOKENS"] = "1000"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ENVIRONMENT"] = "test"
EOF
```

- [ ] **Step 2: Create handler tests**

```bash
cat > stage-2-ai-chatbot/tests/test_handlers.py << 'EOF'
import pytest
import json
from unittest.mock import Mock, patch
from src.handlers.chat import handler, parse_event_body, validate_request
from src.handlers.health import handler as health_handler

class TestChatHandler:
    """Test chat handler"""

    def test_parse_event_body_api_gateway(self):
        """Test parsing API Gateway event"""
        event = {"body": '{"message": "test"}'}
        result = parse_event_body(event)
        assert result == {"message": "test"}

    def test_parse_event_body_direct(self):
        """Test parsing direct event"""
        event = {"message": "test"}
        result = parse_event_body(event)
        assert result == {"message": "test"}

    def test_validate_request_success(self):
        """Test successful validation"""
        data = {"message": "Hello"}
        result = validate_request(data)
        assert "errors" not in result
        assert result["message"] == "Hello"

    def test_validate_request_missing_message(self):
        """Test validation with missing message"""
        data = {}
        result = validate_request(data)
        assert "errors" in result
        assert "message" in result["errors"]

    def test_validate_request_invalid_max_tokens(self):
        """Test validation with invalid max_tokens"""
        data = {"message": "Hello", "max_tokens": 50000}
        result = validate_request(data)
        assert "errors" in result
        assert "max_tokens" in result["errors"]

    def test_validate_request_invalid_temperature(self):
        """Test validation with invalid temperature"""
        data = {"message": "Hello", "temperature": 2.0}
        result = validate_request(data)
        assert "errors" in result
        assert "temperature" in result["errors"]

    @patch("src.handlers.chat.llm_service")
    def test_chat_handler_success(self, mock_llm, mock_event, mock_context, mock_bedrock_response):
        """Test successful chat request"""
        mock_llm.invoke_claude.return_value = {
            "response": "Hello!",
            "model": "test-model",
            "tokens_used": {"input_tokens": 10, "output_tokens": 5},
            "stop_reason": "end_turn"
        }

        result = handler(mock_event, mock_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["response"] == "Hello!"
        assert "conversation_id" in body
        assert "tokens_used" in body

    @patch("src.handlers.chat.llm_service")
    def test_chat_handler_with_temperature(self, mock_llm, mock_event, mock_context):
        """Test chat with temperature parameter"""
        mock_event["body"] = json.dumps({
            "message": "Hello",
            "temperature": 0.5
        })
        mock_llm.invoke_claude.return_value = {
            "response": "Hello!",
            "model": "test-model",
            "tokens_used": {},
            "stop_reason": "end_turn"
        }

        result = handler(mock_event, mock_context)

        assert result["statusCode"] == 200
        mock_llm.invoke_claude.assert_called_once()
        call_kwargs = mock_llm.invoke_claude.call_args[1]
        assert call_kwargs["temperature"] == 0.5

class TestHealthHandler:
    """Test health handler"""

    def test_health_handler(self, mock_context):
        """Test health check"""
        result = health_handler({}, mock_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "healthy"
        assert "version" in body
        assert "timestamp" in body
EOF
```

- [ ] **Step 3: Create LLM service tests**

```bash
cat > stage-2-ai-chatbot/tests/test_llm_service.py << 'EOF'
import pytest
from unittest.mock import Mock, patch
from src.services.llm_service import LLMService

class TestLLMService:
    """Test LLM service"""

    def test_init(self):
        """Test service initialization"""
        service = LLMService()
        assert service.client is not None
        assert service.model_id is not None

    @patch("src.services.llm_service.boto3.client")
    def test_invoke_claude_success(self, mock_boto3_client, mock_bedrock_response):
        """Test successful Claude invocation"""
        mock_client = Mock()
        mock_client.invoke_model.return_value = mock_bedrock_response
        mock_boto3_client.return_value = mock_client

        service = LLMService()
        result = service.invoke_claude("Hello")

        assert "response" in result
        assert result["response"] == "Hello! How can I help you today?"
        assert "model" in result
        assert "tokens_used" in result

    @patch("src.services.llm_service.boto3.client")
    def test_invoke_claude_with_custom_params(self, mock_boto3_client, mock_bedrock_response):
        """Test Claude invocation with custom parameters"""
        mock_client = Mock()
        mock_client.invoke_model.return_value = mock_bedrock_response
        mock_boto3_client.return_value = mock_client

        service = LLMService()
        result = service.invoke_claude(
            "Hello",
            max_tokens=500,
            temperature=0.3
        )

        assert "response" in result
        # Verify the call was made with correct params
        call_args = mock_client.invoke_model.call_args
        request_body = call_args[1]["body"]
        body_dict = eval(request_body)
        assert body_dict["max_tokens"] == 500
        assert body_dict["temperature"] == 0.3

    @patch("src.services.llm_service.boto3.client")
    def test_invoke_claude_error(self, mock_boto3_client):
        """Test Claude invocation error handling"""
        mock_client = Mock()
        mock_client.invoke_model.side_effect = Exception("AWS Error")
        mock_boto3_client.return_value = mock_client

        service = LLMService()

        with pytest.raises(Exception):
            service.invoke_claude("Hello")
EOF
```

- [ ] **Step 4: Create pytest config**

```bash
cat > stage-2-ai-chatbot/pytest.ini << 'EOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
EOF
```

- [ ] **Step 5: Commit tests**

```bash
git add stage-2-ai-chatbot/tests/
git commit -m "test: add unit tests for handlers and LLM service"
```

---

## Chunk 7: Documentation

### Task 7: Create Design Document

**Files:**
- Create: `stage-2-ai-chatbot/docs/design.md`

- [ ] **Step 1: Create design document**

```bash
cat > stage-2-ai-chatbot/docs/design.md << 'EOF'
# Stage 2: AI Chatbot - Architecture Design

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         API Gateway                         │
│                      (REST API + Auth)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Lambda Function                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Router     │→ │ Chat Handler │→ │ LLM Service  │      │
│  └──────────────┘  └──────────────┘  └──────┬───────┘      │
└────────────────────────────────────────────────┼─────────────┘
                                                 │
                                                 ↓
┌─────────────────────────────────────────────────────────────┐
│                      AWS Bedrock                             │
│                    (Claude API)                              │
└─────────────────────────────────────────────────────────────┘
                           ↑
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                     Cross-Service Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Secrets Mgr  │  │ CloudWatch   │  │    X-Ray     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 2. Design Decisions

### Decision 1: Serverless vs Container vs VM

**Problem:** What compute architecture for the chatbot API?

**Options:**
- A. Serverless (Lambda)
- B. Containers (ECS/EKS)
- C. Virtual Machines (EC2)

**Selection:** Option A - AWS Lambda

**Pros:**
- ✅ Zero infrastructure management
- ✅ Automatic scaling (0 to millions of requests)
- ✅ Pay-per-use (only pay when code runs)
- ✅ Built-in high availability across AZs
- ✅ Fast iteration and deployment

**Cons:**
- ❌ Cold starts (100-500ms latency on first invoke)
- ❌ 15-minute execution timeout
- ❌ Limited deployment package size (250 MB uncompressed)
- ❌ Memory/CPU configurations are coupled
- ❌ Local development differs from production

**Mitigation:**
- Use Provisioned Concurrency for predictable latency
- Optimize package size and initialization code
- Design stateless functions for horizontal scaling
- Use SAM/Serverless Framework for local testing

**Constraints:**
- 📊 Technical: 15-minute timeout, 6 MB request payload, 250 MB deployment
- 💰 Cost: $0.20 per 1M requests + compute time
- 📈 Scalability: 1000 concurrent executions per region (can be increased)
- 🔒 Security: IAM-based authorization, VPC isolation possible

**Why Not Other Options:**
- **ECS/EKS:** Management burden for simple API, baseline cost even at zero traffic
- **EC2:** Manual scaling, patching, and high availability configuration

---

### Decision 2: API Gateway vs Application Load Balancer

**Problem:** How to expose the Lambda function as HTTP API?

**Selection:** API Gateway REST API

**Pros:**
- ✅ Managed service with automatic scaling
- ✅ Built-in authentication (API keys, IAM, Cognito, Lambda authorizers)
- ✅ Request/response validation and transformation
- ✅ Usage plans and throttling
- ✅ Direct Lambda integration (no need for ALB)
- ✅ Stage variables for environment management

**Cons:**
- ❌ Additional cost (~$3.50 per million calls)
- ❌ Configuration complexity
- ❌ Another service to manage and monitor

**Mitigation:**
- Use API Gateway for external APIs, direct Lambda invoke for internal
- Monitor usage and optimize API call patterns
- Use Terraform to version control configuration

**Constraints:**
- 📊 Technical: 29-second timeout at integration layer, payload limits
- 💰 Cost: $3.50 per million API calls, data transfer charges
- 📈 Scalability: >10,000 requests per second per region
- 🔒 Security: Multiple authentication methods, WAF integration

---

### Decision 3: Bedrock vs Direct LLM Provider Integration

**Problem:** How to access LLM capabilities?

**Selection:** AWS Bedrock

**Pros:**
- ✅ Unified API for multiple models (Claude, Llama, Mistral, etc.)
- ✅ AWS-native integration (IAM, VPC, CloudWatch)
- ✅ No API keys to manage (uses IAM)
- ✅ Pay-per-use with volume discounts
- ✅ Data residency options
- ✅ Future-proofs against model changes

**Cons:**
- ❌ Vendor lock-in to AWS
- ❌ Slight latency vs direct API calls
- ❌ Model availability varies by region
- ❌ Limited fine-tuning options

**Mitigation:**
- Abstract LLM service interface for provider flexibility
- Monitor Bedrock roadmap for new models/features
- Use VPC endpoints to reduce latency

**Cost Comparison:**
- Claude Sonnet via Bedrock: ~$3 per million input tokens
- Claude Sonnet direct API: ~$3 per million input tokens
- Difference: Minimal, but Bedrock includes network transfer

---

### Decision 4: Secrets Management Strategy

**Problem:** How to manage sensitive configuration?

**Options:**
- A. Environment variables
- B. Secrets Manager
- C. Parameter Store
- D. S3 Encrypted

**Selection:** Secrets Manager (with Environment Variables for non-sensitive)

**Strategy:**
- Environment Variables: Non-sensitive config (model ID, region, timeouts)
- Secrets Manager: API keys, custom endpoints, authentication tokens

**Pros:**
- ✅ Automatic rotation support
- ✅ Fine-grained IAM policies
- ✅ Encrypted at rest and in transit
- ✅ Audit logs via CloudTrail
- ✅ Pay per secret/month (not per API call)

**Cons:**
- ❌ Additional cost ($0.40 per secret/month + $0.05 per 10,000 API calls)
- ❌ Slight cold start impact for secret retrieval

**Constraints:**
- 📊 Technical: 10 KB max secret size, 100 KB with Secret Binary
- 💰 Cost: $0.40 per secret/month
- 📈 Scalability: 10,000 API calls per second per region
- 🔒 Security: KMS encryption, IAM policies

---

### Decision 5: CloudWatch Logs vs Third-Party Logging

**Problem:** How to collect and analyze logs?

**Selection:** CloudWatch Logs (standard)

**Pros:**
- ✅ Native Lambda integration
- ✅ Automatic log aggregation
- ✅ CloudWatch Insights for querying
- ✅ Alarms and dashboards
- ✅ No additional infrastructure

**Cons:**
- ❌ Query syntax can be complex
- ❌ Cost at high volume ($0.50 per GB ingested)
- ❌ Retention costs add up
- ❌ Limited visualization vs ELK/Datadog

**Mitigation:**
- Set appropriate log retention (7 days for dev)
- Use structured logging (JSON) for better querying
- Consider CloudWatch Logs Subscription to S3 for archiving
- Evaluate Datadog/New Relic for production if needed

---

### Decision 6: Cold Start Mitigation

**Problem:** How to minimize Lambda cold starts?

**Analysis:**

Cold start contributors:
1. **Code download:** 50-500ms (package size)
2. **Function initialization:** 100-500ms (imports, config)
3. **VPC setup:** 0-5000ms (if VPC configured)

**Selected Strategies:**

1. **Minimize package size**
   - Only include necessary dependencies
   - Use Lambda Layers for common packages
   - Bundle dependencies efficiently

2. **Optimize initialization**
   - Lazy-load expensive imports
   - Move initialization outside handler
   - Reuse clients/connections

3. **Provisioned Concurrency** (optional)
   - Keeps functions warm
   - Adds baseline cost (~$0.005 per hour per concurrency)
   - Use for predictable baseline traffic

4. **Consider alternative for high-throughput scenarios**
   - For >1000 requests per second, consider ECS
   - For <100 requests per second, Lambda is ideal

---

## 3. Cost Analysis

### Component Costs

| Component | Unit Cost | Monthly Cost (at 100K requests) |
|-----------|-----------|--------------------------------|
| Lambda | $0.20 per 1M requests + compute | ~$2 |
| API Gateway | $3.50 per 1M calls | ~$0.35 |
| Bedrock Claude | $3 per 1M input tokens, $15 per 1M output | ~$5-10* |
| CloudWatch Logs | $0.50 per GB ingested | ~$1-2 |
| Secrets Manager | $0.40 per secret/month | ~$0.40 |
| Data Transfer | $0.09 per GB (first 10 GB) | ~$0.10 |

*Assuming 100K requests/month with 1K tokens each

**Total: ~$10-20/month** for moderate usage (100K requests)

### Cost Optimization Strategies

1. **Reduce logging verbosity** in production
2. **Set appropriate CloudWatch retention** (7 days for dev)
3. **Use provisioned concurrency sparingly** (only for baseline)
4. **Optimize prompt size** (fewer tokens = lower Bedrock cost)
5. **Consider caching** for repeated queries

---

## 4. Security Considerations

### Authentication & Authorization

**Strategy: Defense in Depth**

1. **API Layer:** API Gateway with API keys
2. **Function Layer:** IAM policies for Lambda
3. **Service Layer:** IAM for Bedrock access
4. **Data Layer:** KMS encryption for secrets

### Input Validation

- Sanitize all user inputs
- Validate message length (max 100K characters)
- Rate limiting (API Gateway throttling)
- Parameter validation (temperature, max_tokens)

### Secrets Management

- Never log sensitive data
- Use IAM roles instead of API keys where possible
- Rotate secrets regularly
- Audit access via CloudTrail

---

## 5. Monitoring & Observability

### Key Metrics

1. **Lambda:**
   - Invocations, errors, duration, throttles
   - Concurrent executions
   - Memory usage

2. **API Gateway:**
   - Count, latency, 4XX/5XX errors
   - Integration latency

3. **Bedrock:**
   - Token usage
   - Model invocation latency

### Alarms

- Lambda error rate > 5%
- API Gateway 5XX errors > 1%
- Lambda duration > 5 seconds
- Est. cost > $50/month

---

## 6. Performance Expectations

### Latency Breakdown

| Component | Typical | P95 | P99 |
|-----------|---------|-----|-----|
| API Gateway | 50ms | 100ms | 200ms |
| Lambda (warm) | 100-300ms | 500ms | 1s |
| Lambda (cold) | 500ms | 2s | 5s |
| Bedrock API | 500ms-2s | 3s | 5s |
| **Total (warm)** | **650ms-2.3s** | **3.6s** | **6s** |
| **Total (cold)** | **1s-2.5s** | **5s** | **10s** |

### Throughput

- **Burst:** 1000 concurrent executions
- **Sustained:** 500 requests/second per region
- **API Gateway:** 10,000 requests/second per region

---

## 7. Alternatives Considered

### Why not FastAPI/ECS?

- **Cost:** ECS tasks have baseline cost even at idle
- **Complexity:** Need to manage scaling, load balancing, health checks
- **Operational Burden:** Patching, security updates, monitoring

**Use ECS when:**
- Very consistent, high traffic (avoid cold starts)
- Long-running requests (>15 minutes)
- Need specialized hardware (GPUs)
- Complex orchestration requirements

### Why not direct API integration?

- **Lock-in:** Tied to specific provider's API
- **Migration:** Hard to switch models or providers
- **Optimization:** Can't easily implement A/B testing

---

## 8. Lessons Learned

### What Works Well

1. **Serverless for AI APIs**: Great fit for spiky or unpredictable traffic
2. **Bedrock abstraction**: Easy to switch models
3. **CloudWatch Logs**: Sufficient for most debugging
4. **API Gateway throttling**: Simple rate limiting

### Potential Improvements

1. **Add response caching**: Reduce repeated calls
2. **Implement conversation persistence**: DynamoDB for history
3. **Add streaming responses**: Better UX for long responses
4. **Implement observability**: X-Ray for distributed tracing

### Common Pitfalls

1. **Forgetting to set log retention**: Costs accumulate
2. **Over-provisioning Lambda memory**: Higher cost without benefit
3. **Not testing cold starts**: Production surprise
4. **Logging sensitive data**: Security risk

---

**Design Document Created:** 2026-03-10
**Next:** Deploy and test the chatbot service
EOF
```

- [ ] **Step 2: Commit design document**

```bash
git add stage-2-ai-chatbot/docs/design.md
git commit -m "docs: add comprehensive architecture design document"
```

---

## Completion Checklist

- [ ] All Terraform modules created (Lambda, API Gateway, Secrets Manager, CloudWatch)
- [ ] Lambda handlers implemented (chat, health)
- [ ] LLM service with Bedrock integration
- [ ] Unit tests with >80% coverage
- [ ] Documentation complete (README, design)
- [ ] Code committed with descriptive messages

---

## Deployment Instructions

```bash
# 1. Set up environment
cd stage-2-ai-chatbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Ensure Stage 1 VPC exists
cd ../stage-1-terraform-foundation/terraform
terraform output vpc_id

# 3. Deploy Stage 2
cd ../../stage-2-ai-chatbot/terraform
terraform init
terraform plan
terraform apply

# 4. Test
API_URL=$(terraform output -raw api_endpoint_url)
API_KEY=$(terraform output -raw api_key)

curl -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"message": "Hello!"}'

# 5. Check logs
aws logs tail /aws/lambda/ai-chatbot-lambda --follow

# 6. Cleanup
terraform destroy
```

---

**Implementation Plan Created:** 2026-03-10
**Estimated Time:** 3-4 weeks
**Next:** Begin implementation
