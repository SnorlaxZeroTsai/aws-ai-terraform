# Get Stage 1 VPC configuration
data "terraform_remote_state" "stage1" {
  backend = "local"

  config = {
    path = "${path.module}/../../stage-1-terraform-foundation/terraform/terraform.tfstate"
  }
}

# Secrets Manager Module
module "secrets_manager" {
  source = "./modules/secrets_manager"

  secret_name = var.secret_name
  description = "Configuration and API keys for Stage 2 AI Chatbot"

  secret_value = {
    # Add your configuration here via terraform.tfvars
    # Example:
    # BEDROCK_API_KEY = "your-key-here"
  }

  tags = merge(
    {
      Name = "${var.project_name}-secrets"
    },
    var.additional_tags
  )
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  function_name = "${var.project_name}-stage2-chatbot"
  description   = "AI Chatbot Lambda function using AWS Bedrock Claude"

  runtime      = var.lambda_runtime
  handler      = "handlers/chat.handler"
  timeout      = var.lambda_timeout
  memory_size  = var.lambda_memory_size

  source_dir = "${path.module}/../src"

  subnet_ids         = data.terraform_remote_state.stage1.outputs.public_subnet_ids
  security_group_ids = null  # Use default VPC security group

  environment_variables = {
    PROJECT_NAME    = var.project_name
    STAGE           = "2"
    ENVIRONMENT     = var.environment
  }

  bedrock_model_id = var.bedrock_model_id
  secret_arn       = module.secrets_manager.secret_arn

  log_retention_in_days = var.cloudwatch_log_retention

  tags = merge(
    {
      Name = "${var.project_name}-lambda"
    },
    var.additional_tags
  )
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  api_name    = "${var.project_name}-stage2-api"
  description = "API Gateway for Stage 2 AI Chatbot"

  stage_name         = var.api_gateway_stage_name
  lambda_function_arn = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  lambda_invoke_arn   = module.lambda.invoke_arn

  enable_cors = true

  tags = merge(
    {
      Name = "${var.project_name}-api-gateway"
    },
    var.additional_tags
  )
}

# CloudWatch Module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  dashboard_name = "${var.project_name}-stage2-dashboard"

  lambda_function_name = module.lambda.function_name
  api_gateway_id       = module.api_gateway.api_id

  enable_alarms = var.enable_cloudwatch_alarms

  tags = var.additional_tags
}
