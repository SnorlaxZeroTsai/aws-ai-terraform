# Stage 5: Autonomous Agent - Main Configuration

data "terraform_remote_state" "stage1" {
  backend = "s3"

  config = {
    bucket = var.stage1_state_bucket
    key    = var.stage1_state_key
    region = var.aws_region
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Stage       = "5"
    ManagedBy   = "Terraform"
  }
}

# Data source for VPC from Stage 1
data "aws_vpc" "stage1_vpc" {
  count = var.stage1_state_bucket != "" ? 1 : 0
  id    = try(data.terraform_remote_state.stage1.outputs.vpc_id, null)
}

data "aws_subnets" "stage1_private" {
  count = var.stage1_state_bucket != "" ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [try(data.terraform_remote_state.stage1.outputs.vpc_id, "")]
  }
  tags = {
    Tier = "private"
  }
}

# S3 Bucket for Tool Definitions
module "s3" {
  source = "./modules/s3"

  bucket_name = "${var.project_name}-tool-definitions-${var.environment}"
  tags        = local.common_tags
}

# DynamoDB Tables for Memory
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name        = var.project_name
  environment         = var.environment
  read_capacity       = var.dynamodb_read_capacity
  write_capacity      = var.dynamodb_write_capacity
  memory_ttl_days     = var.memory_ttl_days
  tags                = local.common_tags
}

# Lambda Functions
module "lambda" {
  source = "./modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  aws_region         = var.aws_region
  timeout            = var.lambda_timeout
  memory_size        = var.lambda_memory_size
  bedrock_model_id   = var.bedrock_model_id

  conversation_table = module.dynamodb.conversation_table_name
  episodic_table     = module.dynamodb.episodic_table_name
  semantic_table     = module.dynamodb.semantic_table_table_name
  tool_results_table = module.dynamodb.tool_results_table_name
  tool_bucket        = module.s3.bucket_name

  vpc_id             = try(data.terraform_remote_state.stage1.outputs.vpc_id, null)
  subnet_ids         = try(data.terraform_remote_state.stage1.outputs.private_subnet_ids, null)

  tags               = local.common_tags
}

# Step Functions State Machine
module "step_functions" {
  source = "./modules/step_functions"

  project_name          = var.project_name
  environment           = var.environment
  max_iterations        = var.max_iterations
  agent_core_lambda_arn = module.lambda.agent_core_lambda_arn
  tool_executor_arn     = module.lambda.tool_executor_lambda_arn
  reasoning_engine_arn  = module.lambda.reasoning_engine_lambda_arn

  tags                  = local.common_tags
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "agent_logs" {
  count             = var.enable_cloudwatch_logs ? 1 : 0
  name              = "/aws/lambda/${var.project_name}-agent-core"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}
