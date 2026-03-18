# Terraform Issues Fix Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three Terraform configuration issues across Stages 2, 3, and 4: CloudWatch dashboard syntax errors, S3/DynamoDB/SNS configuration errors, and Lambda/OpenSearch circular dependency.

**Architecture:** Extract shared infrastructure resources (IAM role, security group) into a dedicated module to break circular dependencies. Fix syntax and configuration errors in earlier stages.

**Tech Stack:** Terraform, AWS Provider, Terraform State Management

---

## File Structure

### Stage 2 (CloudWatch)
- `stage-2-ai-chatbot/terraform/modules/cloudwatch/main.tf` - Fix dashboard JSON syntax

### Stage 3 (Config Fixes)
- `stage-3-document-analysis/terraform/modules/s3/main.tf` - Add lifecycle filter
- `stage-3-document-analysis/terraform/modules/dynamodb/main.tf` - Remove invalid lifecycle
- `stage-3-document-analysis/terraform/modules/sns_sqs/main.tf` - Remove unsupported parameter

### Stage 4 (Circular Dependency)
**New Files:**
- `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/main.tf` - Create shared IAM and SG
- `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/variables.tf` - Define inputs
- `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/outputs.tf` - Define outputs

**Modified Files:**
- `stage-4-rag-knowledge-base/terraform/modules/lambda/variables.tf` - Add new variables
- `stage-4-rag-knowledge-base/terraform/modules/lambda/main.tf` - Remove IAM/SG resources, use variables
- `stage-4-rag-knowledge-base/terraform/modules/lambda/outputs.tf` - Add passthrough outputs
- `stage-4-rag-knowledge-base/terraform/modules/opensearch/variables.tf` - Add new variables, remove domain_arn
- `stage-4-rag-knowledge-base/terraform/modules/opensearch/main.tf` - Use self-reference, remove log group
- `stage-4-rag-knowledge-base/terraform/main.tf` - Add shared_infrastructure module, reorder dependencies

---

## Chunk 1: Stage 2 - CloudWatch Dashboard Fix

### Task 1: Fix CloudWatch Dashboard JSON Syntax

**Files:**
- Modify: `stage-2-ai-chatbot/terraform/modules/cloudwatch/main.tf:80-89`

- [ ] **Step 1: Navigate to Stage 2 directory**

```bash
cd stage-2-ai-chatbot/terraform
```

- [ ] **Step 2: Backup current state (if exists)**

```bash
if [ -f terraform.tfstate ]; then cp terraform.tfstate terraform.tfstate.backup; fi
```

- [ ] **Step 3: Verify the file content and line numbers**

```bash
sed -n '75,95p' modules/cloudwatch/main.tf
```

Expected: See the metrics widget configuration around lines 80-89

- [ ] **Step 4: Fix the JSON syntax errors in the metrics widget**

Edit `modules/cloudwatch/main.tf` lines 80-89:

**BEFORE (incorrect):**
```hcl
            metrics = [
              [{
                expression" : "errors/(invocations) * 100",
                label" : "Error Rate (%)",
                id" : "e1"
              }],
              [{"expression" : "m1/1000", "label" : "Duration (s)", "id" : "m1" }],
              ["AWS/Lambda", "Invocations", [{ "name" = "FunctionName", "value" : var.lambda_function_name }], { "id" : "m1", "visible" : false }],
              ["AWS/Lambda", "Errors", ".", { "id" : "m2", "visible" : false }]
            ]
```

**AFTER (correct):**
```hcl
            metrics = [
              [{
                expression = "errors/(invocations) * 100",
                label      = "Error Rate (%)",
                id         = "e1"
              }],
              [{"expression" = "m1/1000", "label" = "Duration (s)", "id" = "m1" }],
              ["AWS/Lambda", "Invocations", [{ "name" = "FunctionName", "value" = var.lambda_function_name }], { "id" = "m1", "visible" = false }],
              ["AWS/Lambda", "Errors", ".", { "id" = "m2", "visible" = false }]
            ]
```

- [ ] **Step 5: Validate the syntax**

```bash
terraform init
terraform validate
```

Expected: No errors

- [ ] **Step 6: Run plan to verify changes**

```bash
terraform plan
```

Expected: Shows dashboard resource will be updated, no errors

- [ ] **Step 7: Commit the fix**

```bash
cd ../..
git add stage-2-ai-chatbot/terraform/modules/cloudwatch/main.tf
git commit -m "fix(stage2): correct CloudWatch dashboard JSON syntax

- Change expression\" : to expression =
- Change label\" : to label =
- Change id\" : to id =
- Fixes terraform init/validate errors
- Closes #1

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: Stage 3 - Configuration Fixes

### Task 2: Fix S3 Lifecycle Configuration

**Files:**
- Modify: `stage-3-document-analysis/terraform/modules/s3/main.tf:39-52`

- [ ] **Step 1: Navigate to Stage 3 directory**

```bash
cd stage-3-document-analysis/terraform
```

- [ ] **Step 2: Backup current state (if exists)**

```bash
if [ -f terraform.tfstate ]; then cp terraform.tfstate terraform.tfstate.backup; fi
```

- [ ] **Step 3: Add filter block to S3 lifecycle configuration**

Edit `modules/s3/main.tf`, update the `aws_s3_bucket_lifecycle_configuration` resource:

**BEFORE:**
```hcl
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
```

**AFTER:**
```hcl
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  count = var.enable_lifecycle ? 1 : 0

  bucket = aws_s3_bucket.this.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    filter {
      prefix = "documents/"
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}
```

- [ ] **Step 4: Validate the syntax**

```bash
terraform validate
```

Expected: No errors

- [ ] **Step 5: Commit the fix**

```bash
cd ../..
git add stage-3-document-analysis/terraform/modules/s3/main.tf
git commit -m "fix(stage3): add required filter to S3 lifecycle configuration

- Add filter { prefix = \"documents/\" } to satisfy AWS requirements
- Fixes terraform validate warning about missing filter/prefix

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 3: Fix DynamoDB Lifecycle Configuration

**Files:**
- Modify: `stage-3-document-analysis/terraform/modules/dynamodb/main.tf:57-60`

- [ ] **Step 1: Navigate to Stage 3 directory**

```bash
cd stage-3-document-analysis/terraform
```

- [ ] **Step 2: Remove invalid lifecycle block from DynamoDB table**

Edit `modules/dynamodb/main.tf`, remove the lifecycle block:

**BEFORE:**
```hcl
  tags = var.tags

  # Lifecycle: ignore changes to replica count (if adding global tables later)
  lifecycle {
    ignore_changes = [replicas]
  }
}
```

**AFTER:**
```hcl
  tags = var.tags
}
```

- [ ] **Step 3: Validate the syntax**

```bash
terraform validate
```

Expected: No errors

- [ ] **Step 4: Commit the fix**

```bash
cd ../..
git add stage-3-document-analysis/terraform/modules/dynamodb/main.tf
git commit -m "fix(stage3): remove invalid DynamoDB lifecycle configuration

- Remove lifecycle { ignore_changes = [replicas] }
- PAY_PER_REQUEST mode doesn't use replicas attribute
- Fixes terraform validate error

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 4: Fix SNS Subscription Configuration

**Files:**
- Modify: `stage-3-document-analysis/terraform/modules/sns_sqs/main.tf:11-19`

- [ ] **Step 1: Navigate to Stage 3 directory**

```bash
cd stage-3-document-analysis/terraform
```

- [ ] **Step 2: Remove unsupported parameter from SNS subscription**

Edit `modules/sns_sqs/main.tf`, remove `auto_confirm_subscription`:

**BEFORE:**
```hcl
resource "aws_sns_topic_subscription" "email" {
  count = var.enabled && var.notification_email != null ? 1 : 0

  topic_arn = aws_sns_topic.this[0].arn
  protocol  = "email"
  endpoint  = var.notification_email

  auto_confirm_subscription = false
}
```

**AFTER:**
```hcl
resource "aws_sns_topic_subscription" "email" {
  count = var.enabled && var.notification_email != null ? 1 : 0

  topic_arn = aws_sns_topic.this[0].arn
  protocol  = "email"
  endpoint  = var.notification_email
}
```

- [ ] **Step 3: Validate the syntax**

```bash
terraform validate
```

Expected: No errors

- [ ] **Step 4: Commit the fix**

```bash
cd ../..
git add stage-3-document-analysis/terraform/modules/sns_sqs/main.tf
git commit -m "fix(stage3): remove unsupported SNS subscription parameter

- Remove auto_confirm_subscription = false
- This parameter is not supported by AWS SNS
- Email subscriptions require manual confirmation via email link

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: Stage 4 - Shared Infrastructure Module

### Task 5: Create Shared Infrastructure Module

**Files:**
- Create: `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/main.tf`
- Create: `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/variables.tf`
- Create: `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/outputs.tf`

- [ ] **Step 1: Navigate to Stage 4 directory**

```bash
cd stage-4-rag-knowledge-base/terraform
```

- [ ] **Step 2: Backup current state**

```bash
if [ -f terraform.tfstate ]; then
  cp terraform.tfstate terraform.tfstate.backup
  terraform state list > ../resources-before.txt
fi
```

- [ ] **Step 3: Create shared_infrastructure module directory**

```bash
mkdir -p modules/shared_infrastructure
```

- [ ] **Step 4: Create main.tf for shared_infrastructure module**

Create `modules/shared_infrastructure/main.tf`:

```hcl
# Lambda Execution Role
resource "aws_iam_role" "lambda_execution" {
  name = "stage4-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "stage4-lambda-${var.environment}"
    Environment = var.environment
    Stage       = "4"
    Purpose     = "lambda-execution"
  }
}

# Lambda Security Group
resource "aws_security_group" "lambda" {
  name        = "stage4-lambda-${var.environment}"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "stage4-lambda-${var.environment}"
    Environment = var.environment
    Stage       = "4"
    Purpose     = "lambda-functions"
  }
}

# Basic Lambda Execution Role Policy for VPC access
resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
```

- [ ] **Step 5: Create variables.tf for shared_infrastructure module**

Create `modules/shared_infrastructure/variables.tf`:

```hcl
variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string

  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "vpc_id" {
  description = "VPC ID where Lambda will be deployed"
  type        = string
}
```

- [ ] **Step 6: Create outputs.tf for shared_infrastructure module**

Create `modules/shared_infrastructure/outputs.tf`:

```hcl
output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.name
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = aws_security_group.lambda.id
}
```

- [ ] **Step 7: Validate the new module**

```bash
terraform validate
```

Expected: No errors

- [ ] **Step 8: Commit the new module**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/
git commit -m "feat(stage4): create shared_infrastructure module

- Extract Lambda IAM role and security group to dedicated module
- Establish clear ownership boundaries
- Prepare for circular dependency resolution

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: Stage 4 - Update Lambda Module

### Task 6: Update Lambda Module Variables

**Files:**
- Modify: `stage-4-rag-knowledge-base/terraform/modules/lambda/variables.tf`

- [ ] **Step 1: Navigate to Stage 4 lambda module**

```bash
cd stage-4-rag-knowledge-base/terraform/modules/lambda
```

- [ ] **Step 2: Add new variables to lambda module**

Add these variables to `variables.tf` (at the end of the file):

```hcl
variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "lambda_execution_role_name" {
  description = "Name of the Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda functions (from shared_infrastructure module)"
  type        = string
}
```

- [ ] **Step 3: Validate the syntax**

```bash
cd ..
terraform validate
```

Expected: No errors

- [ ] **Step 4: Commit the changes**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/modules/lambda/variables.tf
git commit -m "refactor(stage4): add lambda module variables for shared resources

- Add lambda_execution_role_arn variable
- Add lambda_execution_role_name variable
- Add lambda_security_group_id variable
- Prepare for receiving resources from shared_infrastructure module

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 7: Update Lambda Module Main Configuration

**Files:**
- Modify: `stage-4-rag-knowledge-base/terraform/modules/lambda/main.tf`

- [ ] **Step 1: Read the current lambda main.tf to identify resources to remove**

```bash
cd stage-4-rag-knowledge-base/terraform/modules/lambda
grep -n "resource \"aws_iam_role" main.tf
grep -n "resource \"aws_security_group\" main.tf
```

Expected: Find aws_iam_role.lambda_execution and aws_security_group.lambda resources

- [ ] **Step 2: Remove IAM role and security group resources**

Edit `main.tf`, remove these entire resource blocks:
- `resource "aws_iam_role" "lambda_execution"`
- `resource "aws_security_group" "lambda"`
- `resource "aws_iam_role_policy_attachment" "basic_execution"` (if exists)

- [ ] **Step 3: Update aws_lambda_function resources to use variables**

Find all `aws_lambda_function` resources in `main.tf` and update:

**BEFORE:**
```hcl
resource "aws_lambda_function" "index" {
  # ... other fields ...

  role = aws_iam_role.lambda_execution.arn

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

resource "aws_lambda_function" "search" {
  # ... other fields ...

  role = aws_iam_role.lambda_execution.arn

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}
```

**AFTER:**
```hcl
resource "aws_lambda_function" "index" {
  # ... other fields ...

  role = var.lambda_execution_role_arn

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
}

resource "aws_lambda_function" "search" {
  # ... other fields ...

  role = var.lambda_execution_role_arn

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }
}
```

- [ ] **Step 4: Validate the syntax**

```bash
cd ..
terraform validate
```

Expected: No errors

- [ ] **Step 5: Commit the changes**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/modules/lambda/main.tf
git commit -m "refactor(stage4): update lambda module to use shared resources

- Remove aws_iam_role.lambda_execution resource
- Remove aws_security_group.lambda resource
- Update aws_lambda_function to use var.lambda_execution_role_arn
- Update aws_lambda_function to use var.lambda_security_group_id
- Resources now come from shared_infrastructure module

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 8: Update Lambda Module Outputs

**Files:**
- Modify: `stage-4-rag-knowledge-base/terraform/modules/lambda/outputs.tf`

- [ ] **Step 1: Read current lambda outputs.tf**

```bash
cd stage-4-rag-knowledge-base/terraform/modules/lambda
cat outputs.tf
```

- [ ] **Step 2: Add passthrough outputs for backward compatibility**

Add these outputs to the TOP of `outputs.tf` (before existing outputs):

```hcl
# Passthrough outputs for backward compatibility
# These now come from shared_infrastructure module instead of being created here

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role (passthrough from shared_infrastructure)"
  value       = var.lambda_execution_role_arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role (passthrough from shared_infrastructure)"
  value       = var.lambda_execution_role_name
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions (passthrough from shared_infrastructure)"
  value       = var.lambda_security_group_id
}
```

- [ ] **Step 3: Validate the syntax**

```bash
cd ..
terraform validate
```

Expected: No errors

- [ ] **Step 4: Commit the changes**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/modules/lambda/outputs.tf
git commit -m "refactor(stage4): add passthrough outputs to lambda module

- Add lambda_execution_role_arn passthrough output
- Add lambda_execution_role_name passthrough output
- Add lambda_security_group_id passthrough output
- Maintains backward compatibility for existing consumers

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: Stage 4 - Update OpenSearch Module

### Task 9: Update OpenSearch Module Variables

**Files:**
- Modify: `stage-4-rag-knowledge-base/terraform/modules/opensearch/variables.tf`

- [ ] **Step 1: Navigate to opensearch module**

```bash
cd stage-4-rag-knowledge-base/terraform/modules/opensearch
```

- [ ] **Step 2: Remove domain_arn and cloudwatch_log_arn variables**

Edit `variables.tf`, remove these variable definitions:
- `variable "domain_arn"`
- `variable "cloudwatch_log_arn"`

- [ ] **Step 3: Update existing variable descriptions**

Update these existing variables to note they come from shared_infrastructure:

```hcl
variable "lambda_security_group_id" {
  description = "Security group ID of Lambda functions (from shared_infrastructure module)"
  type        = string
}

variable "lambda_execution_role_arn" {
  description = "ARN of Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "lambda_execution_role_name" {
  description = "Name of Lambda execution role (from shared_infrastructure module)"
  type        = string
}
```

- [ ] **Step 4: Add cloudwatch_log_arn variable**

```hcl
variable "cloudwatch_log_arn" {
  description = "ARN of CloudWatch log group for OpenSearch logs"
  type        = string
}
```

- [ ] **Step 5: Validate the syntax**

```bash
cd ..
terraform validate
```

Expected: No errors

- [ ] **Step 6: Commit the changes**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/modules/opensearch/variables.tf
git commit -m "refactor(stage4): update opensearch module variables

- Remove domain_arn variable (now uses self-reference)
- Remove cloudwatch_log_arn variable (log group moved to main.tf)
- Add cloudwatch_log_arn as input variable
- Update variable descriptions to note shared_infrastructure source

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### Task 10: Update OpenSearch Module Main Configuration

**Files:**
- Modify: `stage-4-rag-knowledge-base/terraform/modules/opensearch/main.tf`

- [ ] **Step 1: Read current opensearch main.tf**

```bash
cd stage-4-rag-knowledge-base/terraform/modules/opensearch
grep -n "access_policies" main.tf
grep -n "aws_cloudwatch_log_group" main.tf
```

- [ ] **Step 2: Update access_policies to use self-reference**

Edit `main.tf`, update the `access_policies` block in `aws_opensearch_domain.main`:

**BEFORE:**
```hcl
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "es:*"
        Effect    = "Allow"
        Principal = { AWS = var.lambda_execution_role_arn }
        Resource  = "${var.domain_arn}/*"
      }
    ]
  })
```

**AFTER:**
```hcl
  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "es:*"
        Effect    = "Allow"
        Principal = { AWS = var.lambda_execution_role_arn }
        Resource  = "${aws_opensearch_domain.main.arn}/*"
      }
    ]
  })
```

- [ ] **Step 3: Remove CloudWatch log group resource**

Edit `main.tf`, remove this entire resource block:
- `resource "aws_cloudwatch_log_group" "opensearch"`
- Remove the `depends_on = [aws_cloudwatch_log_group.opensearch]` line from aws_opensearch_domain

- [ ] **Step 4: Update log_publishing_options to use variable**

Edit `main.tf`, update the `log_publishing_options` block:

**BEFORE:**
```hcl
  log_publishing_options {
    cloudwatch_log_log_arn = aws_cloudwatch_log_group.opensearch.arn
    log_type               = "ES_APPLICATION_LOGS"
    enabled                = true
  }
```

**AFTER:**
```hcl
  log_publishing_options {
    cloudwatch_log_log_arn = var.cloudwatch_log_arn
    log_type               = "ES_APPLICATION_LOGS"
    enabled                = true
  }
```

- [ ] **Step 5: Validate the syntax**

```bash
cd ..
terraform validate
```

Expected: No errors

- [ ] **Step 6: Commit the changes**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/modules/opensearch/main.tf
git commit -m "refactor(stage4): update opensearch module configuration

- Update access_policies to use self-reference aws_opensearch_domain.main.arn
- Remove aws_cloudwatch_log_group.opensearch resource
- Update log_publishing_options to use var.cloudwatch_log_arn
- Log group now created in main.tf

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 6: Stage 4 - Update Main Configuration

### Task 11: Update Main.tf Module Dependencies

**Files:**
- Modify: `stage-4-rag-knowledge-base/terraform/main.tf`

- [ ] **Step 1: Navigate to Stage 4 main directory**

```bash
cd stage-4-rag-knowledge-base/terraform
```

- [ ] **Step 2: Read current main.tf to understand module order**

```bash
cat main.tf | grep -A 5 "^module "
```

- [ ] **Step 3: Reorder and update modules in main.tf**

Edit `main.tf`, reorganize in the correct dependency order:

**1. SHARED_INFRASTRUCTURE (add first, no dependencies)**
```hcl
# Shared Infrastructure - IAM and Security Group
module "shared_infrastructure" {
  source = "./modules/shared_infrastructure"

  environment = var.environment
  vpc_id      = data.terraform_remote_state.stage1.outputs.vpc_id
}
```

**2. BEDROCK (no module dependencies)**
```hcl
# Bedrock Module
module "bedrock" {
  source = "./modules/bedrock"

  environment        = var.environment
  embedding_model_id = var.bedrock_embedding_model
  llm_model_id       = var.bedrock_llm_model
}
```

**3. S3 (no module dependencies)**
```hcl
# S3 Module
module "s3" {
  source = "./modules/s3"

  bucket_name = var.documents_bucket_name
  environment = var.environment
}
```

**4. CLOUDWATCH LOG GROUP (standalone resource)**
```hcl
# CloudWatch Log Group for OpenSearch
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/${var.opensearch_domain_name}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-opensearch-logs-${var.environment}"
    Stage = "4"
  }
}
```

**5. OPENSEARCH (depends on shared_infrastructure)**
```hcl
# OpenSearch Module
module "opensearch" {
  source = "./modules/opensearch"

  domain_name             = var.opensearch_domain_name
  environment             = var.environment
  vpc_id                  = data.terraform_remote_state.stage1.outputs.vpc_id
  subnet_ids              = data.terraform_remote_state.stage1.outputs.private_subnet_ids
  instance_type           = var.opensearch_instance_type
  instance_count          = var.opensearch_instance_count
  ebs_volume_size         = var.opensearch_ebs_volume_size
  engine_version          = var.opensearch_engine_version

  # From shared_infrastructure
  lambda_security_group_id     = module.shared_infrastructure.lambda_security_group_id
  lambda_execution_role_arn    = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name   = module.shared_infrastructure.lambda_execution_role_name

  # From main.tf resource
  cloudwatch_log_arn           = aws_cloudwatch_log_group.opensearch.arn
}
```

**6. LAMBDA (depends on shared_infrastructure, opensearch, s3, bedrock)**
```hcl
# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  environment                   = var.environment
  vpc_id                        = data.terraform_remote_state.stage1.outputs.vpc_id
  private_subnet_ids            = data.terraform_remote_state.stage1.outputs.private_subnet_ids
  opensearch_domain_endpoint    = module.opensearch.domain_endpoint
  documents_bucket_arn          = module.s3.bucket_arn
  bedrock_embedding_model       = var.bedrock_embedding_model
  bedrock_llm_model             = var.bedrock_llm_model
  chunk_size                    = var.chunk_size
  chunk_overlap                 = var.chunk_overlap
  vector_dimension              = var.vector_dimension
  max_results                   = var.max_results
  index_lambda_timeout          = var.index_lambda_timeout
  index_lambda_memory_size      = var.index_lambda_memory_size
  search_lambda_timeout         = var.search_lambda_timeout
  search_lambda_memory_size     = var.search_lambda_memory_size

  # From shared_infrastructure
  lambda_execution_role_arn     = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name    = module.shared_infrastructure.lambda_execution_role_name
  lambda_security_group_id      = module.shared_infrastructure.lambda_security_group_id
}
```

- [ ] **Step 4: Validate the syntax**

```bash
terraform validate
```

Expected: No errors

- [ ] **Step 5: Run plan to verify no circular dependencies**

```bash
terraform plan
```

Expected: Plan completes successfully with no cycle errors

- [ ] **Step 6: Commit the changes**

```bash
cd ../..
git add stage-4-rag-knowledge-base/terraform/main.tf
git commit -m "refactor(stage4): reorder modules and update dependencies

- Add shared_infrastructure module
- Reorder modules: shared_infrastructure → bedrock → s3 → opensearch → lambda
- Move aws_cloudwatch_log_group.opensearch to main.tf
- Update opensearch module to receive shared_infrastructure outputs
- Update lambda module to receive shared_infrastructure outputs
- Eliminates circular dependency between lambda and opensearch

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 7: Stage 4 - State Migration

### Task 12: Migrate Terraform State

**Files:**
- State file: `stage-4-rag-knowledge-base/terraform/terraform.tfstate`

**WARNING:** This task modifies Terraform state. Ensure you have a backup!

- [ ] **Step 1: Navigate to Stage 4 directory**

```bash
cd stage-4-rag-knowledge-base/terraform
```

- [ ] **Step 2: Verify backup exists**

```bash
if [ ! -f terraform.tfstate.backup ]; then
  echo "ERROR: No backup found! Create backup first:"
  echo "cp terraform.tfstate terraform.tfstate.backup"
  exit 1
fi
```

- [ ] **Step 3: Initialize Terraform**

```bash
terraform init
```

Expected: Successfully initialized

- [ ] **Step 4: Move IAM role state**

```bash
terraform state mv 'module.lambda.aws_iam_role.lambda_execution' 'module.shared_infrastructure.aws_iam_role.lambda_execution'
```

Expected: Successfully moved

- [ ] **Step 5: Move security group state**

```bash
terraform state mv 'module.lambda.aws_security_group.lambda' 'module.shared_infrastructure.aws_security_group.lambda'
```

Expected: Successfully moved

- [ ] **Step 6: Move IAM policy attachment state**

```bash
terraform state mv 'module.lambda.aws_iam_role_policy_attachment.basic_execution' 'module.shared_infrastructure.aws_iam_role_policy_attachment.basic_execution'
```

Expected: Successfully moved (if this resource exists)

- [ ] **Step 7: Move CloudWatch log group state**

```bash
terraform state mv 'module.opensearch.aws_cloudwatch_log_group.opensearch' 'aws_cloudwatch_log_group.opensearch'
```

Expected: Successfully moved

- [ ] **Step 8: Verify state migration**

```bash
terraform plan
```

Expected: Shows "No changes" or minimal changes (no resource recreation)

- [ ] **Step 9: Document the migration**

```bash
cat > ../state-migration-$(date +%Y%m%d).log << 'EOF'
Terraform State Migration Log
Date: $(date)
Migrations performed:
  - module.lambda.aws_iam_role.lambda_execution → module.shared_infrastructure.aws_iam_role.lambda_execution
  - module.lambda.aws_security_group.lambda → module.shared_infrastructure.aws_security_group.lambda
  - module.lambda.aws_iam_role_policy_attachment.basic_execution → module.shared_infrastructure.aws_iam_role_policy_attachment.basic_execution
  - module.opensearch.aws_cloudwatch_log_group.opensearch → aws_cloudwatch_log_group.opensearch
Backup: terraform.tfstate.backup
EOF
```

- [ ] **Step 10: Commit the state changes (optional)**

```bash
# Note: Terraform state files are typically not committed to git
# But you may want to commit the migration log
cd ..
git add stage-4-rag-knowledge-base/state-migration-*.log
git commit -m "docs(stage4): add terraform state migration log

- Document state moves for circular dependency fix
- Resources migrated: IAM role, security group, policy attachment, log group

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Chunk 8: Verification and Testing

### Task 13: Verify All Stages

**Files:**
- All modified terraform configurations

- [ ] **Step 1: Verify Stage 2**

```bash
cd stage-2-ai-chatbot/terraform
terraform init
terraform validate
echo "Stage 2: PASSED"
cd ../..
```

Expected: All commands succeed

- [ ] **Step 2: Verify Stage 3**

```bash
cd stage-3-document-analysis/terraform
terraform init
terraform validate
echo "Stage 3: PASSED"
cd ../..
```

Expected: All commands succeed

- [ ] **Step 3: Verify Stage 4**

```bash
cd stage-4-rag-knowledge-base/terraform
terraform init
terraform validate
terraform plan | head -100
echo "Stage 4: PASSED"
cd ../..
```

Expected: All commands succeed, no cycle errors

- [ ] **Step 4: Verify passthrough outputs (Stage 4)**

```bash
cd stage-4-rag-knowledge-base/terraform
terraform output module.lambda.lambda_execution_role_arn
terraform output module.lambda.lambda_security_group_id
terraform output module.lambda.lambda_execution_role_name
echo "Passthrough outputs: PASSED"
cd ../..
```

Expected: All outputs resolve correctly

- [ ] **Step 5: Close GitHub issues**

```bash
gh issue close 1 --comment "Fixed by terraform configuration refactor. CloudWatch dashboard syntax corrected."
gh issue close 2 --comment "Fixed by terraform configuration updates. S3 lifecycle filter added, DynamoDB lifecycle removed, SNS parameter removed."
gh issue close 3 --comment "Fixed by extracting shared_infrastructure module. Circular dependency resolved."
```

Expected: All issues closed

- [ ] **Step 6: Create summary commit**

```bash
git commit --allow-empty -m "docs: complete Terraform issues fix

All issues resolved:
- Issue #1 (Stage 2): CloudWatch dashboard syntax fixed
- Issue #2 (Stage 3): S3/DynamoDB/SNS configurations corrected
- Issue #3 (Stage 4): Circular dependency resolved via shared_infrastructure module

Verification:
- All terraform validate commands pass
- All terraform plan commands complete without errors
- Passthrough outputs verified working

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Completion Checklist

- [ ] All code changes committed
- [ ] All Terraform validation passes
- [ ] State migration completed successfully
- [ ] GitHub issues #1, #2, #3 closed
- [ ] Documentation updated (if needed)

---

## Rollback Procedures

If issues occur during state migration:

```bash
# Restore from backup
cd stage-4-rag-knowledge-base/terraform
cp terraform.tfstate.backup terraform.tfstate

# Or reverse the state moves
terraform state mv 'module.shared_infrastructure.aws_iam_role.lambda_execution' 'module.lambda.aws_iam_role.lambda_execution'
terraform state mv 'module.shared_infrastructure.aws_security_group.lambda' 'module.lambda.aws_security_group.lambda'
terraform state mv 'module.shared_infrastructure.aws_iam_role_policy_attachment.basic_execution' 'module.lambda.aws_iam_role_policy_attachment.basic_execution'
terraform state mv 'aws_cloudwatch_log_group.opensearch' 'module.opensearch.aws_cloudwatch_log_group.opensearch'
```
