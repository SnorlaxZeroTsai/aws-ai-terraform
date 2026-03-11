variable "table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
}

variable "enable_autoscaling" {
  description = "Enable autoscaling for read/write capacity"
  type        = bool
  default     = false
}

variable "autoscaling_max_read_capacity" {
  description = "Maximum read capacity for autoscaling"
  type        = number
  default     = 100
}

variable "autoscaling_min_read_capacity" {
  description = "Minimum read capacity for autoscaling"
  type        = number
  default     = 5
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "Alarm action ARNs (e.g., SNS topics)"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
