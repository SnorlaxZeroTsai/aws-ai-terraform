variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "aws-ai-roadmap"
}

# Lambda Configuration
variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 256
}

variable "lambda_runtime" {
  description = "Lambda function runtime"
  type        = string
  default     = "python3.11"
}

# API Gateway Configuration
variable "api_gateway_stage_name" {
  description = "API Gateway deployment stage name"
  type        = string
  default     = "v1"
}

# Bedrock Configuration
variable "bedrock_model_id" {
  description = "Bedrock model ID for Claude"
  type        = string
  default     = "anthropic.claude-3-sonnet-1-20240229-v1:0"
}

variable "bedrock_max_tokens" {
  description = "Maximum tokens for Bedrock responses"
  type        = number
  default     = 1000
}

variable "bedrock_temperature" {
  description = "Temperature for Bedrock responses (0.0-1.0)"
  type        = number
  default     = 0.7

  validation {
    condition     = var.bedrock_temperature >= 0.0 && var.bedrock_temperature <= 1.0
    error_message = "Temperature must be between 0.0 and 1.0"
  }
}

# CloudWatch Configuration
variable "cloudwatch_log_retention" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudwatch_log_retention)
    error_message = "Log retention must be a valid CloudWatch retention period."
  }
}

variable "enable_cloudwatch_alarms" {
  description = "Enable CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

# Secrets Manager Configuration
variable "secret_name" {
  description = "Name of the secret in Secrets Manager"
  type        = string
  default     = "stage2-chatbot-secrets"
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
