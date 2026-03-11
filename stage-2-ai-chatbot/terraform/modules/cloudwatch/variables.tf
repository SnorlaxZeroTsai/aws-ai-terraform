variable "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  type        = string
  default     = "stage2-chatbot-dashboard"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to monitor"
  type        = string
}

variable "api_gateway_id" {
  description = "ID of the API Gateway to monitor"
  type        = string
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "error_threshold_percentage" {
  description = "Error rate threshold for alarms (percentage)"
  type        = number
  default     = 5.0

  validation {
    condition     = var.error_threshold_percentage >= 0 && var.error_threshold_percentage <= 100
    error_message = "Error threshold must be between 0 and 100."
  }
}

variable "latency_threshold_ms" {
  description = "Latency threshold for alarms (milliseconds)"
  type        = number
  default     = 10000

  validation {
    condition     = var.latency_threshold_ms > 0
    error_message = "Latency threshold must be greater than 0."
  }
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications (optional)"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to CloudWatch resources"
  type        = map(string)
  default     = {}
}
