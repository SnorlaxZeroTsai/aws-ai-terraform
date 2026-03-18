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

**Resources in shared_infrastructure**:
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
}
```

**Updated main.tf dependencies**:
```hcl
# 1. Shared infrastructure (no dependencies)
module "shared_infrastructure" {
  source = "./modules/shared_infrastructure"

  environment = var.environment
  vpc_id      = data.terraform_remote_state.stage1.outputs.vpc_id
}

# 2. Lambda (depends on shared_infrastructure)
module "lambda" {
  source = "./modules/lambda"

  environment                   = var.environment
  vpc_id                        = data.terraform_remote_state.stage1.outputs.vpc_id
  private_subnet_ids            = data.terraform_remote_state.stage1.outputs.private_subnet_ids
  opensearch_domain_endpoint    = module.opensearch.domain_endpoint
  documents_bucket_arn          = module.s3.bucket_arn
  # Use shared infrastructure outputs:
  lambda_execution_role_arn     = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name    = module.shared_infrastructure.lambda_execution_role_name
  lambda_security_group_id      = module.shared_infrastructure.lambda_security_group_id
  # ... other variables
}

# 3. OpenSearch (depends on shared_infrastructure)
module "opensearch" {
  source = "./modules/opensearch"

  domain_name             = var.opensearch_domain_name
  environment             = var.environment
  vpc_id                  = data.terraform_remote_state.stage1.outputs.vpc_id
  subnet_ids              = data.terraform_remote_state.stage1.outputs.private_subnet_ids
  # Use shared infrastructure outputs:
  lambda_security_group_id     = module.shared_infrastructure.lambda_security_group_id
  lambda_execution_role_arn    = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name   = module.shared_infrastructure.lambda_execution_role_name
  # Use self-reference instead of variable:
  domain_arn               = aws_opensearch_domain.main.arn
  cloudwatch_log_arn       = aws_cloudwatch_log_group.opensearch.arn
}

# 4. CloudWatch Log Group (standalone resource)
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/${var.opensearch_domain_name}"
  retention_in_days = 7
}
```

**Updated opensearch module variables.tf**:
- Remove: `lambda_security_group_id`, `lambda_execution_role_arn`, `lambda_execution_role_name`, `domain_arn`, `cloudwatch_log_arn`
- These are now passed from main.tf outputs or resources

**Updated lambda module main.tf**:
- Remove: `aws_iam_role.lambda_execution`, `aws_security_group.lambda`
- These are now created in shared_infrastructure module

---

## New Dependency Graph

```
main.tf
│
├── shared_infrastructure (no module dependencies)
│   └── outputs: lambda_execution_role_arn, lambda_security_group_id, etc.
│
├── lambda (depends_on: shared_infrastructure, opensearch, s3, bedrock)
│   └── needs: opensearch.domain_endpoint (runtime)
│
├── opensearch (depends_on: shared_infrastructure)
│   └── needs: shared_infrastructure outputs (access policies)
│
├── s3 (no module dependencies)
│
└── bedrock (no module dependencies)
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

### 3. Incremental Testing
Test in order: Stage 2 → Stage 3 → Stage 4
Each stage must pass before proceeding to next

---

## Backward Compatibility

### Preserved Outputs
All existing module outputs remain unchanged:
- Stage 2: All CloudWatch outputs preserved
- Stage 3: All S3, DynamoDB, SNS/SQS outputs preserved
- Stage 4: All Lambda, OpenSearch, S3, Bedrock outputs preserved

### Variable Compatibility
- Existing variables remain functional
- New variables added only where necessary
- No breaking changes to module interfaces

---

## Implementation Checklist

- [ ] Fix Stage 2 CloudWatch dashboard syntax
- [ ] Add S3 lifecycle filter with prefix
- [ ] Remove DynamoDB lifecycle ignore_changes
- [ ] Remove SNS auto_confirm_subscription parameter
- [ ] Create shared_infrastructure module
- [ ] Update lambda module to use shared resources
- [ ] Update opensearch module to use shared resources
- [ ] Update Stage 4 main.tf dependency order
- [ ] Run terraform init/validate on all stages
- [ ] Run terraform plan to verify no cycles
- [ ] Update documentation

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing deployments | High | Maintain output compatibility; test in dev environment first |
| Missing IAM permissions | Medium | Include all necessary IAM policies in shared_infrastructure |
| Terraform state corruption | Low | Backup state files before applying changes |

---

## Success Criteria

1. All `terraform init` commands complete successfully
2. All `terraform validate` commands pass with no errors
3. `terraform plan` completes with no circular dependency warnings
4. All existing outputs remain accessible
5. No unexpected resource recreation in plan output

---

## References

- GitHub Issues: #1, #2, #3
- Terraform AWS Provider Documentation
- AWS CloudWatch Dashboard Reference
- OpenSearch Security Best Practices
