# Main Terraform configuration for Stage 6: AI Agent Platform

# locals
locals {
  common_tags = {
    Project   = "ai-learning-roadmap"
    Stage     = "6-agent-platform"
    ManagedBy = "Terraform"
  }

  # Extract VPC information from Stage 1
  vpc_id              = try(data.terraform_remote_state.stage1.outputs.vpc_id, null)
  private_subnet_ids  = try(data.terraform_remote_state.stage1.outputs.private_subnet_ids, [])

  # Extract Lambda function ARNs from previous stages
  chatbot_lambda_arn     = try(data.terraform_remote_state.stage2.outputs.lambda_function_arn, null)
  rag_search_lambda_arn  = try(data.terraform_remote_state.stage4.outputs.search_lambda_function_arn, null)
  agent_core_lambda_arn  = try(data.terraform_remote_state.stage5.outputs.agent_core_lambda_arn, null)

  # Extract other resources
  opensearch_endpoint    = try(data.terraform_remote_state.stage4.outputs.opensearch_domain_endpoint, null)
  step_function_arn      = try(data.terraform_remote_state.stage5.outputs.step_function_arn, null)
  document_bucket        = try(data.terraform_remote_state.stage3.outputs.s3_bucket_name, null)

  orchestrator_url = "http://${aws_lb.internal.dns_name}:${var.container_port}"
}

# Application Load Balancer for ECS
resource "aws_lb" "internal" {
  name               = "${var.platform_name}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = local.private_subnet_ids

  enable_deletion_protection = false
  enable_http2              = true

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-alb"
    }
  )
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.platform_name}-alb-"
  description = "Security group for ALB"
  vpc_id      = local.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [local.vpc_id]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [local.vpc_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-alb"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_target_group" "orchestrator" {
  name        = "${var.platform_name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = local.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = local.common_tags
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.internal.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.orchestrator.arn
  }
}

# IAM role for API Gateway CloudWatch logs
resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.platform_name}-apigw-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "api_gateway_cloudwatch" {
  name = "${var.platform_name}-apigw-cloudwatch-policy"
  role = aws_iam_role.api_gateway_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:FilterLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"

  platform_name = var.platform_name
  environment   = var.environment
  aws_region    = var.aws_region

  repository_name = var.ecr_repository_name
  image_tag       = var.image_tag
  task_cpu        = var.ecs_task_cpu
  task_memory     = var.ecs_task_memory
  desired_count   = var.desired_count
  container_port  = var.container_port

  enable_auto_scaling = var.enable_auto_scaling
  min_capacity        = var.min_capacity
  max_capacity        = var.max_capacity

  enable_xray          = var.enable_xray
  log_retention_days   = var.retention_days
  enable_alarms        = var.enable_cloudwatch_alarms
  enable_alarm_actions = var.enable_cloudwatch_alarms
  alarm_email          = var.alarm_email

  create_vpc_resources    = false
  vpc_id                  = local.vpc_id
  private_subnet_ids      = local.private_subnet_ids
  target_group_arn        = aws_lb_target_group.orchestrator.arn
  load_balancer_security_groups = [aws_security_group.alb.id]

  lambda_function_arns = compact([
    local.chatbot_lambda_arn,
    local.rag_search_lambda_arn,
    local.agent_core_lambda_arn
  ])

  step_function_arns = compact([
    local.step_function_arn
  ])

  dynamodb_table_arns = []
  s3_bucket_arns      = []

  environment_variables = []

  common_tags = local.common_tags
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  platform_name = var.platform_name
  api_name      = var.api_gateway_name
  stage_name    = var.api_gateway_stage_name

  orchestrator_url = local.orchestrator_url
  load_balancer_arns = [aws_lb.internal.arn]

  auth_type = var.auth_type
  # authorizer_lambda_invoke_arn = module.lambda.authorizer_invoke_arn
  # authorizer_role_arn          = module.lambda.authorizer_role_arn
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn

  throttling_burst_limit = var.api_gateway_throttling_burst_limit
  throttling_rate_limit  = var.api_gateway_throttling_rate_limit

  enable_xray        = var.enable_xray
  log_retention_days = var.retention_days

  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn

  lambda_integrations = []

  common_tags = local.common_tags
}

# Lambda Module (for lightweight functions)
module "lambda" {
  source = "./modules/lambda"

  platform_name = var.platform_name
  environment   = var.environment
  aws_region    = var.aws_region

  functions = []

  vpc_config = var.vpc_config != null ? {
    subnet_ids         = var.vpc_config.subnet_ids
    security_group_ids = var.vpc_config.security_group_ids
  } : null

  enable_xray        = var.enable_xray
  log_retention_days = var.retention_days

  common_tags = local.common_tags
}

# X-Ray Module
module "xray" {
  source = "./modules/xray"

  platform_name        = var.platform_name
  create_xray_resources = var.enable_xray
  kms_key_arn          = var.kms_key_arn

  common_tags = local.common_tags
}

# CloudWatch Module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  platform_name     = var.platform_name
  aws_region        = var.aws_region
  api_gateway_name  = var.api_gateway_name
  ecs_cluster_name  = module.ecs.cluster_name
  ecs_service_name  = module.ecs.service_name

  log_retention_days    = var.retention_days
  enable_alarms         = var.enable_cloudwatch_alarms
  enable_sns            = var.enable_cloudwatch_alarms
  alarm_email           = var.alarm_email
  api_5xx_threshold     = var.api_5xx_threshold
  api_latency_threshold = var.api_latency_threshold
  ecs_cpu_threshold     = var.ecs_cpu_threshold
  ecs_memory_threshold  = var.ecs_memory_threshold

  common_tags = local.common_tags
}

# VPC Config for Lambda (from Stage 1)
variable "vpc_config" {
  description = "VPC configuration for Lambda functions"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
}

variable "api_5xx_threshold" {
  description = "API Gateway 5XX error threshold"
  type        = number
  default     = 50
}

variable "api_latency_threshold" {
  description = "API Gateway latency threshold"
  type        = number
  default     = 10000
}

variable "ecs_cpu_threshold" {
  description = "ECS CPU threshold"
  type        = number
  default     = 80
}

variable "ecs_memory_threshold" {
  description = "ECS memory threshold"
  type        = number
  default     = 85
}
