# Terraform Issues Fix - Design Document

**Date**: 2026-03-18
**Author**: Claude (Sonnet 4.6)
**Status**: Draft

## Overview

This document describes the design for fixing three Terraform configuration issues across Stages 2, 3, and 4 of the AWS AI Infrastructure project. The issues range from syntax errors to architectural circular dependencies.

## Problem Statement

### Issue #1: Stage 2 - CloudWatch Dashboard Syntax Error
**Location**: `stage-2-ai-chatbot/terraform/modules/cloudwatch/main.tf`

The CloudWatch dashboard configuration uses incorrect JSON object syntax (`expression" : "value"`) instead of Terraform expression syntax (`expression = "value"`).

**Error Message**:
```
Error: Missing key/value separator
Error: Invalid multi-line string
```

### Issue #2: Stage 3 - Multiple Configuration Errors

1. **S3 Lifecycle**: Missing required `filter` or `prefix` attribute in `aws_s3_bucket_lifecycle_configuration`
2. **DynamoDB**: Invalid `replicas` attribute in lifecycle block (should be `replica` or removed)
3. **SNS**: Unsupported `auto_confirm_subscription` argument

### Issue #3: Stage 4 - Circular Dependency

**Cycle Path**:
```
module.opensearch.var.instance_type
→ module.opensearch.output.domain_arn
→ module.opensearch.var.domain_arn (self-reference!)
→ module.opensearch.var.lambda_security_group_id
→ module.lambda.aws_security_group.lambda
→ module.lambda.aws_lambda_function.index
→ module.opensearch.aws_opensearch_domain.main
→ module.lambda.var.opensearch_domain_endpoint (close)
```

The lambda module needs opensearch outputs, while opensearch needs lambda outputs.

## Design Solution

### Principle: Modularization with Clear Boundaries

Extract shared infrastructure resources into a dedicated module to eliminate circular dependencies and establish clear ownership boundaries.

---

## Issue #1: CloudWatch Dashboard Fix

### Approach: Syntax Correction with Refactoring

**Changes to `stage-2-ai-chatbot/terraform/modules/cloudwatch/main.tf`**:

1. Fix JSON syntax errors (lines 82-88):
   - Change `expression" : "value"` to `expression = "value"`
   - Change `label" : "value"` to `label = "value"`
   - Change `id" : "value"` to `id = "value"`

2. Refactor dashboard widgets for better maintainability:
   - Use consistent Terraform expression syntax throughout
   - Ensure proper JSON escaping in `jsonencode()` blocks

**Example Fix**:
```hcl
# Before (incorrect):
metrics = [[{
  expression" : "errors/(invocations) * 100",
  label" : "Error Rate (%)",
  id" : "e1"
}]]

# After (correct):
metrics = [[{
  expression = "errors/(invocations) * 100",
  label      = "Error Rate (%)",
  id         = "e1"
}]]
```

---

## Issue #2: Stage 3 Configuration Fixes

### S3 Lifecycle Configuration

**Add filter with prefix**:
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

**Rationale**: The prefix aligns with the document upload use case and satisfies AWS requirements.

### DynamoDB Lifecycle Fix

**Remove invalid lifecycle block**:
```hcl
# Remove this entire section:
lifecycle {
  ignore_changes = [replicas]
}
```

**Rationale**:
- PAY_PER_REQUEST billing mode doesn't use replicas
- Global tables (which use replicas) require separate configuration
- If global tables are needed later, add proper replica configuration

### SNS Subscription Fix

**Remove unsupported parameter**:
```hcl
resource "aws_sns_topic_subscription" "email" {
  count = var.enabled && var.notification_email != null ? 1 : 0

  topic_arn = aws_sns_topic.this[0].arn
  protocol  = "email"
  endpoint  = var.notification_email

  # Remove this line (not supported):
  # auto_confirm_subscription = false
}
```

**Rationale**: Email subscriptions require manual confirmation via email link - this is correct AWS behavior and cannot be automated.

---

## Issue #3: Circular Dependency Resolution

### Root Cause Analysis

The circular dependency occurs because:
1. Lambda needs OpenSearch domain endpoint (runtime dependency)
2. OpenSearch needs Lambda security group and IAM role (access policy dependency)
3. OpenSearch incorrectly references its own output as a variable

### Solution: Extract Shared Infrastructure

**Create new module**: `stage-4-rag-knowledge-base/terraform/modules/shared_infrastructure/`

**Module Structure**:
```
shared_infrastructure/
├── main.tf          # Creates IAM role and security group
├── variables.tf     # Defines inputs (vpc_id, environment, etc.)
├── outputs.tf       # Outputs role ARN, name, and SG ID
└── README.md        # Module documentation
```

### shared_infrastructure Module Specification

**modules/shared_infrastructure/main.tf**:
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
  }
}

# Basic Lambda Execution Role Policy
resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
```

**modules/shared_infrastructure/variables.tf**:
```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Lambda will be deployed"
  type        = string
}
```

**modules/shared_infrastructure/outputs.tf**:
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

### Updated main.tf Dependencies

```hcl
# 1. Shared infrastructure (no module dependencies)
module "shared_infrastructure" {
  source = "./modules/shared_infrastructure"

  environment = var.environment
  vpc_id      = data.terraform_remote_state.stage1.outputs.vpc_id
}

# 2. Bedrock (no module dependencies)
module "bedrock" {
  source = "./modules/bedrock"

  environment        = var.environment
  embedding_model_id = var.bedrock_embedding_model
  llm_model_id       = var.bedrock_llm_model
}

# 3. S3 (no module dependencies)
module "s3" {
  source = "./modules/s3"

  bucket_name = var.documents_bucket_name
  environment = var.environment
}

# 4. CloudWatch Log Group (standalone resource, no dependencies)
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/${var.opensearch_domain_name}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-opensearch-logs-${var.environment}"
    Stage = "4"
  }
}

# 5. OpenSearch (depends on shared_infrastructure)
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
  # Pass from shared_infrastructure
  lambda_security_group_id     = module.shared_infrastructure.lambda_security_group_id
  lambda_execution_role_arn    = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name   = module.shared_infrastructure.lambda_execution_role_name
  # Pass from main.tf resource
  cloudwatch_log_arn           = aws_cloudwatch_log_group.opensearch.arn
}

# 6. Lambda (depends on shared_infrastructure, opensearch, s3, bedrock)
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
  # Pass from shared_infrastructure
  lambda_execution_role_arn     = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name    = module.shared_infrastructure.lambda_execution_role_name
  lambda_security_group_id      = module.shared_infrastructure.lambda_security_group_id
}
```

### Updated opensearch Module

**modules/opensearch/variables.tf** - Changes:
- **Add**: `lambda_security_group_id` (passed from shared_infrastructure via main.tf)
- **Add**: `lambda_execution_role_arn` (passed from shared_infrastructure via main.tf)
- **Add**: `lambda_execution_role_name` (passed from shared_infrastructure via main.tf)
- **Add**: `cloudwatch_log_arn` (passed from aws_cloudwatch_log_group resource in main.tf)
- **Remove**: `domain_arn` (now uses self-reference internally)

**modules/opensearch/main.tf** - Changes:
```hcl
# In access_policies, use self-reference instead of variable:
access_policies = jsonencode({
  Version = "2012-10-17"
  Statement = [
    {
      Action    = "es:*"
      Effect    = "Allow"
      Principal = { AWS = var.lambda_execution_role_arn }
      Resource  = "${aws_opensearch_domain.main.arn}/*"  # Self-reference
    }
  ]
})

# Remove this resource (moved to main.tf):
# resource "aws_cloudwatch_log_group" "opensearch" { ... }
```

### Updated lambda Module

**modules/lambda/variables.tf** - Add:
```hcl
variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  type        = string
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  type        = string
}
```

**modules/lambda/main.tf** - Remove:
```hcl
# Remove these resources (moved to shared_infrastructure):
# resource "aws_iam_role" "lambda_execution" { ... }
# resource "aws_security_group" "lambda" { ... }
```

**modules/lambda/main.tf** - Update aws_lambda_function:
```hcl
resource "aws_lambda_function" "index" {
  # ... other fields ...

  role = var.lambda_execution_role_arn  # Use variable instead of resource reference

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]  # Use variable instead of resource reference
  }
}
```

**modules/lambda/outputs.tf** - Add passthrough outputs for backward compatibility:
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

# Existing outputs remain unchanged
output "index_function_name" {
  description = "Name of the index Lambda function"
  value       = aws_lambda_function.index.function_name
}

output "index_function_arn" {
  description = "ARN of the index Lambda function"
  value       = aws_lambda_function.index.arn
}

# ... other existing outputs ...
```

---

## New Dependency Graph

```
main.tf
│
├── shared_infrastructure (no module dependencies)
│   └── outputs: lambda_execution_role_arn, lambda_security_group_id, etc.
│
├── bedrock (no module dependencies)
│
├── s3 (no module dependencies)
│
├── aws_cloudwatch_log_group.opensearch (standalone resource)
│
├── opensearch (depends_on: shared_infrastructure)
│   └── needs: shared_infrastructure outputs (access policies)
│
└── lambda (depends_on: shared_infrastructure, opensearch, s3, bedrock)
    └── needs: opensearch.domain_endpoint (runtime)
```

---

## State Migration Strategy

### Critical: Resource Movement Between Modules

This design moves resources from their original modules to a new shared_infrastructure module. This requires careful state migration to avoid resource deletion and recreation.

### Migration Process

**Before making any code changes**:

1. **Backup state files**:
```bash
cp terraform.tfstate terraform.tfstate.backup
cp terraform.tfstate.d/terraform.tfstate terraform.tfstate.d/terraform.tfstate.backup
```

2. **Document current resource addresses**:
```bash
terraform state list > resources-before.txt
```

### Migration Steps (After Code Changes)

**Step 1: Move IAM Role**
```bash
# From: module.lambda.aws_iam_role.lambda_execution
# To:   module.shared_infrastructure.aws_iam_role.lambda_execution
terraform state mv 'module.lambda.aws_iam_role.lambda_execution' 'module.shared_infrastructure.aws_iam_role.lambda_execution'
```

**Step 2: Move Security Group**
```bash
# From: module.lambda.aws_security_group.lambda
# To:   module.shared_infrastructure.aws_security_group.lambda
terraform state mv 'module.lambda.aws_security_group.lambda' 'module.shared_infrastructure.aws_security_group.lambda'
```

**Step 3: Move IAM Policy Attachment**
```bash
# From: module.lambda.aws_iam_role_policy_attachment.basic_execution
# To:   module.shared_infrastructure.aws_iam_role_policy_attachment.basic_execution
terraform state mv 'module.lambda.aws_iam_role_policy_attachment.basic_execution' 'module.shared_infrastructure.aws_iam_role_policy_attachment.basic_execution'
```

**Step 4: Move CloudWatch Log Group**
```bash
# From: module.opensearch.aws_cloudwatch_log_group.opensearch
# To:   aws_cloudwatch_log_group.opensearch
terraform state mv 'module.opensearch.aws_cloudwatch_log_group.opensearch' 'aws_cloudwatch_log_group.opensearch'
```

**Step 5: Verify**
```bash
terraform plan
# Should show "No changes" or minimal changes (no resource recreation)
```

### Rollback Plan

If migration fails:
```bash
# Restore from backup
cp terraform.tfstate.backup terraform.tfstate

# Or reverse the moves
terraform state mv 'module.shared_infrastructure.aws_iam_role.lambda_execution' 'module.lambda.aws_iam_role.lambda_execution'
terraform state mv 'module.shared_infrastructure.aws_security_group.lambda' 'module.lambda.aws_security_group.lambda'
terraform state mv 'module.shared_infrastructure.aws_iam_role_policy_attachment.basic_execution' 'module.lambda.aws_iam_role_policy_attachment.basic_execution'
terraform state mv 'aws_cloudwatch_log_group.opensearch' 'module.opensearch.aws_cloudwatch_log_group.opensearch'
```

---

## Testing Strategy

### 1. Syntax Validation
```bash
# Stage 2
cd stage-2-ai-chatbot/terraform
terraform init
terraform validate

# Stage 3
cd stage-3-document-analysis/terraform
terraform init
terraform validate

# Stage 4
cd stage-4-rag-knowledge-base/terraform
terraform init
terraform validate
```

### 2. Plan Validation
```bash
# Verify no circular dependencies
terraform plan

# Should complete successfully without cycle errors
```

### 3. State Migration Test (Stage 4 only)
```bash
# Test migration in development environment first
terraform state mv <source> <destination>
terraform plan  # Verify no unexpected changes
```

### 4. Incremental Testing
Test in order: Stage 2 → Stage 3 → Stage 4
Each stage must pass before proceeding to next

---

## Backward Compatibility

### Breaking Changes (Stage 4)

**Internal Changes**:
- Lambda and OpenSearch modules no longer create IAM role and security group
- These resources moved to shared_infrastructure module
- CloudWatch log group moved from opensearch module to main.tf

**External Compatibility**:
- All module outputs remain unchanged
- Existing consumers of these outputs will continue to work
- Module interface changes are internal implementation details

### Module Interface Changes

**Before**:
```hcl
module "lambda" {
  # Lambda created its own role and SG
  source = "./modules/lambda"
  # No role/SG parameters needed
}

module "opensearch" {
  # OpenSearch expected to receive role/SG as variables
  source = "./modules/opensearch"
  lambda_security_group_id  = module.lambda.lambda_security_group_id
  lambda_execution_role_arn = module.lambda.lambda_execution_role_arn
}
```

**After**:
```hcl
module "shared_infrastructure" {
  # New module creates shared resources
  source = "./modules/shared_infrastructure"
  environment = var.environment
  vpc_id      = var.vpc_id
}

module "lambda" {
  # Lambda receives role/SG as variables
  source = "./modules/lambda"
  lambda_execution_role_arn    = module.shared_infrastructure.lambda_execution_role_arn
  lambda_security_group_id     = module.shared_infrastructure.lambda_security_group_id
}

module "opensearch" {
  # OpenSearch receives role/SG from shared_infrastructure
  source = "./modules/opensearch"
  lambda_security_group_id     = module.shared_infrastructure.lambda_security_group_id
  lambda_execution_role_arn    = module.shared_infrastructure.lambda_execution_role_arn
}
```

### Output Compatibility

All existing module outputs are preserved:
- `module.lambda.lambda_execution_role_arn` (now passed through from shared_infrastructure)
- `module.lambda.lambda_security_group_id` (now passed through from shared_infrastructure)
- `module.opensearch.domain_endpoint` (unchanged)
- All other outputs unchanged

**Note**: Outputs that were previously module-sourced may now be passthrough outputs from shared_infrastructure.

---

## Implementation Checklist

### Pre-Implementation
- [ ] Backup all Terraform state files
- [ ] Document current resource addresses (`terraform state list`)
- [ ] Create development/testing environment

### Stage 2 Implementation
- [ ] Fix CloudWatch dashboard syntax errors
- [ ] Run `terraform init` and `terraform validate`
- [ ] Run `terraform plan` to verify changes

### Stage 3 Implementation
- [ ] Add S3 lifecycle filter with prefix
- [ ] Remove DynamoDB lifecycle ignore_changes block
- [ ] Remove SNS auto_confirm_subscription parameter
- [ ] Run `terraform init` and `terraform validate`
- [ ] Run `terraform plan` to verify changes

### Stage 4 Implementation
- [ ] Create shared_infrastructure module (main.tf, variables.tf, outputs.tf)
- [ ] Update lambda module:
  - [ ] Add new variables (lambda_execution_role_arn, lambda_execution_role_name, lambda_security_group_id)
  - [ ] Remove aws_iam_role.lambda_execution resource
  - [ ] Remove aws_security_group.lambda resource
  - [ ] Update aws_lambda_function to use new variables
- [ ] Update opensearch module:
  - [ ] Add new variables (lambda_security_group_id, lambda_execution_role_arn, lambda_execution_role_name, cloudwatch_log_arn)
  - [ ] Remove domain_arn variable
  - [ ] Update access_policies to use self-reference
  - [ ] Remove aws_cloudwatch_log_group.opensearch resource
- [ ] Update Stage 4 main.tf:
  - [ ] Add shared_infrastructure module block
  - [ ] Update lambda module to pass new variables
  - [ ] Update opensearch module to pass new variables
  - [ ] Move aws_cloudwatch_log_group.opensearch to main.tf
  - [ ] Update module dependency order
- [ ] Run `terraform init` and `terraform validate`
- [ ] **CRITICAL**: Perform state migration:
  - [ ] Move aws_iam_role.lambda_execution
  - [ ] Move aws_security_group.lambda
  - [ ] Move aws_iam_role_policy_attachment.basic_execution
  - [ ] Move aws_cloudwatch_log_group.opensearch
- [ ] Run `terraform plan` to verify no unexpected resource recreation
- [ ] Update module READMEs with new architecture

### Post-Implementation
- [ ] Verify passthrough outputs resolve correctly:
  - [ ] `terraform output module.lambda.lambda_execution_role_arn`
  - [ ] `terraform output module.lambda.lambda_security_group_id`
  - [ ] `terraform output module.lambda.lambda_execution_role_name`
- [ ] Confirm existing consumers of lambda outputs still work
- [ ] Close GitHub issues #1, #2, #3
- [ ] Update project documentation
- [ ] Create pull request with changes

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| State migration failure | High | Low | Test migration in dev environment first; keep backups |
| Resource recreation during migration | High | Low | Careful state mv commands; verify with terraform plan |
| Breaking existing deployments | High | Medium | Maintain output compatibility; thorough testing |
| Missing IAM permissions after migration | Medium | Low | Include all necessary policies in shared_infrastructure |
| Terraform provider version conflicts | Low | Low | Pin provider versions in all modules |

---

## Success Criteria

1. All `terraform init` commands complete successfully
2. All `terraform validate` commands pass with no errors
3. `terraform plan` completes with no circular dependency warnings
4. State migration completes without resource recreation
5. All existing outputs remain accessible
6. GitHub issues #1, #2, #3 are resolved

---

## References

- GitHub Issues: #1, #2, #3
- Terraform State Migration Documentation: https://www.terraform.io/cli/commands/state/mv
- Terraform AWS Provider Documentation
- AWS CloudWatch Dashboard Reference
- OpenSearch Security Best Practices
