variable "platform_name" {
  description = "Platform name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "functions" {
  description = "List of Lambda functions to create"
  type = list(object({
    name          = string
    description   = string
    handler       = string
    runtime       = string
    timeout       = number
    memory_size   = number
    source_dir    = string
    environment   = map(string)
  }))
  default = []
}

variable "vpc_config" {
  description = "VPC configuration for Lambda"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention days"
  type        = number
  default     = 7
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
