variable "platform_name" {
  description = "Platform name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "api_gateway_name" {
  description = "API Gateway name for metrics"
  type        = string
}

variable "ecs_cluster_name" {
  description = "ECS cluster name for metrics"
  type        = string
}

variable "ecs_service_name" {
  description = "ECS service name for metrics"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention days"
  type        = number
  default     = 7
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "enable_sns" {
  description = "Enable SNS notifications for alarms"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email for alarm notifications"
  type        = string
  default     = null
}

variable "api_5xx_threshold" {
  description = "API Gateway 5XX error threshold"
  type        = number
  default     = 50
}

variable "api_latency_threshold" {
  description = "API Gateway latency threshold (ms)"
  type        = number
  default     = 10000
}

variable "ecs_cpu_threshold" {
  description = "ECS CPU threshold (percent)"
  type        = number
  default     = 80
}

variable "ecs_memory_threshold" {
  description = "ECS memory threshold (percent)"
  type        = number
  default     = 85
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
