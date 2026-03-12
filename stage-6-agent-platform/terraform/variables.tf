variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "platform_name" {
  description = "Name of the AI Agent Platform"
  type        = string
  default     = "ai-agent-platform"
}

variable "domain_name" {
  description = "Custom domain name for API Gateway (optional)"
  type        = string
  default     = null
}

variable "certificate_arn" {
  description = "ACM certificate ARN for custom domain (optional)"
  type        = string
  default     = null
}

# ECS Configuration
variable "ecs_task_cpu" {
  description = "ECS task CPU units (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.ecs_task_cpu)
    error_message = "CPU must be valid ECS value: 256, 512, 1024, 2048, or 4096."
  }
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB (512-16384)"
  type        = number
  default     = 1024

  validation {
    condition     = var.ecs_task_memory >= 512 && var.ecs_task_memory <= 16384
    error_message = "Memory must be between 512 and 16384 MB."
  }
}

variable "desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2

  validation {
    condition     = var.desired_count >= 1
    error_message = "Desired count must be at least 1."
  }
}

variable "enable_auto_scaling" {
  description = "Enable ECS auto-scaling"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum number of ECS tasks for auto-scaling"
  type        = number
  default     = 2

  validation {
    condition     = var.min_capacity >= 1
    error_message = "Minimum capacity must be at least 1."
  }
}

variable "max_capacity" {
  description = "Maximum number of ECS tasks for auto-scaling"
  type        = number
  default     = 10

  validation {
    condition     = var.max_capacity >= var.min_capacity
    error_message = "Maximum capacity must be >= minimum capacity."
  }
}

variable "container_port" {
  description = "Container port for the orchestrator service"
  type        = number
  default     = 8000
}

# Docker Image Configuration
variable "ecr_repository_name" {
  description = "ECR repository name for the orchestrator image"
  type        = string
  default     = "ai-agent-orchestrator"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

# API Gateway Configuration
variable "api_gateway_name" {
  description = "Name of the API Gateway"
  type        = string
  default     = "ai-agent-platform-api"
}

variable "api_gateway_stage_name" {
  description = "Deployment stage name for API Gateway"
  type        = string
  default     = "v1"
}

variable "enable_api_gateway_logging" {
  description = "Enable API Gateway access logs"
  type        = bool
  default     = true
}

variable "api_gateway_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 100
}

variable "api_gateway_throttling_rate_limit" {
  description = "API Gateway throttling rate limit"
  type        = number
  default     = 50
}

# Lambda Configuration
variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 30

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 256

  validation {
    condition     = contains([128, 256, 512, 1024, 2048], var.lambda_memory_size)
    error_message = "Lambda memory must be 128, 256, 512, 1024, or 2048 MB."
  }
}

# X-Ray Configuration
variable "enable_xray" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = true
}

# CloudWatch Configuration
variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarm notifications"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = null
}

variable "retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.retention_days)
    error_message = "Invalid retention days value."
  }
}

# Authentication Configuration
variable "auth_type" {
  description = "Authentication type (jwt, api_key, cognito)"
  type        = string
  default     = "jwt"

  validation {
    condition     = contains(["jwt", "api_key", "cognito"], var.auth_type)
    error_message = "Auth type must be jwt, api_key, or cognito."
  }
}

variable "jwt_secret" {
  description = "JWT secret key (use Secrets Manager in production)"
  type        = string
  sensitive   = true
  default     = null
}

variable "cognito_user_pool_arn" {
  description = "Cognito user pool ARN (if using Cognito auth)"
  type        = string
  default     = null
}

# Monitoring Configuration
variable "enable_prometheus" {
  description = "Enable Prometheus metrics endpoint"
  type        = bool
  default     = true
}

variable "prometheus_port" {
  description = "Port for Prometheus metrics"
  type        = number
  default     = 9090
}

# Cost Control
variable "cost_allocation_tag" {
  description = "Cost allocation tag for billing"
  type        = string
  default     = "ai-platform"
}

# Feature Flags
variable "enable_chatbot_agent" {
  description = "Enable chatbot agent integration"
  type        = bool
  default     = true
}

variable "enable_rag_agent" {
  description = "Enable RAG agent integration"
  type        = bool
  default     = true
}

variable "enable_autonomous_agent" {
  description = "Enable autonomous agent integration"
  type        = bool
  default     = true
}

variable "enable_document_agent" {
  description = "Enable document analysis agent integration"
  type        = bool
  default     = true
}
