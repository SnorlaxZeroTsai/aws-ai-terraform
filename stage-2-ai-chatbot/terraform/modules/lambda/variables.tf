variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "description" {
  description = "Description of the Lambda function"
  type        = string
  default     = "AI Chatbot handler using AWS Bedrock Claude"
}

variable "runtime" {
  description = "Lambda function runtime"
  type        = string
  default     = "python3.11"
}

variable "handler" {
  description = "Lambda function handler"
  type        = string
  default     = "handlers/chat.handler"
}

variable "timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30

  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "Timeout must be between 1 and 900 seconds."
  }
}

variable "memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 256

  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "Memory size must be between 128 and 10240 MB."
  }
}

variable "source_dir" {
  description = "Path to the Lambda source code directory"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for Lambda ENI"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "List of security group IDs for Lambda"
  type        = list(string)
  default     = null
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for Claude"
  type        = string
}

variable "secret_arn" {
  description = "ARN of the secret in Secrets Manager"
  type        = string
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to the Lambda function"
  type        = map(string)
  default     = {}
}
