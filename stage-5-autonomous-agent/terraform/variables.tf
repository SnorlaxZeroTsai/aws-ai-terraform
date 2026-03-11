variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource tagging"
  type        = string
  default     = "autonomous-agent"
}

variable "max_iterations" {
  description = "Maximum number of agent reasoning iterations"
  type        = number
  default     = 10
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for reasoning"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (use -1 for on-demand)"
  type        = number
  default     = -1
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (use -1 for on-demand)"
  type        = number
  default     = -1
}

variable "memory_ttl_days" {
  description = "Default TTL for conversation memory in days"
  type        = number
  default     = 7
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "stage1_state_bucket" {
  description = "S3 bucket containing Stage 1 Terraform state"
  type        = string
}

variable "stage1_state_key" {
  description = "Key for Stage 1 Terraform state file"
  type        = string
  default     = "terraform-foundation/terraform.tfstate"
}
