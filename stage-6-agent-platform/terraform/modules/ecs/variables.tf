variable "platform_name" {
  description = "Name of the platform"
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

variable "repository_name" {
  description = "ECR repository name"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
}

variable "task_cpu" {
  description = "ECS task CPU units"
  type        = number
}

variable "task_memory" {
  description = "ECS task memory in MB"
  type        = number
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
}

variable "container_port" {
  description = "Container port"
  type        = number
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling"
  type        = bool
}

variable "min_capacity" {
  description = "Minimum capacity"
  type        = number
}

variable "max_capacity" {
  description = "Maximum capacity"
  type        = number
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
}

variable "log_retention_days" {
  description = "CloudWatch log retention days"
  type        = number
}

# VPC Configuration
variable "create_vpc_resources" {
  description = "Create VPC resources"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

# Load Balancer
variable "target_group_arn" {
  description = "Target group ARN for ALB"
  type        = string
}

variable "load_balancer_security_groups" {
  description = "Security groups for load balancer"
  type        = list(string)
  default     = []
}

# Integration with other services
variable "lambda_function_arns" {
  description = "ARNs of Lambda functions to invoke"
  type        = list(string)
  default     = []
}

variable "step_function_arns" {
  description = "ARNs of Step Functions to invoke"
  type        = list(string)
  default     = []
}

variable "dynamodb_table_arns" {
  description = "ARNs of DynamoDB tables to access"
  type        = list(string)
  default     = []
}

variable "s3_bucket_arns" {
  description = "ARNs of S3 buckets to access"
  type        = list(string)
  default     = []
}

# Container Configuration
variable "environment_variables" {
  description = "Additional environment variables"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "container_secrets" {
  description = "Secrets for container"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

# Alarms
variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "enable_alarm_actions" {
  description = "Enable alarm actions"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email for alarm notifications"
  type        = string
  default     = null
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
