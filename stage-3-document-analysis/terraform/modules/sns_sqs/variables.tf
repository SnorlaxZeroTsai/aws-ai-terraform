variable "enabled" {
  description = "Enable async processing"
  type        = bool
  default     = true
}

variable "queue_name" {
  description = "SQS queue name"
  type        = string
}

variable "topic_name" {
  description = "SNS topic name"
  type        = string
}

variable "notification_email" {
  description = "Email for SNS notifications"
  type        = string
  default     = null
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for queue policy"
  type        = string
  default     = null
}

variable "message_retention_seconds" {
  description = "Message retention period in seconds"
  type        = number
  default     = 1209600 # 14 days
}

variable "receive_wait_time_seconds" {
  description = "Wait time for receive request"
  type        = number
  default     = 20
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout for messages"
  type        = number
  default     = 300
}

variable "max_receive_count" {
  description = "Max receive count before sending to DLQ"
  type        = number
  default     = 3
}

variable "dlq_retention_seconds" {
  description = "DLQ retention period in seconds"
  type        = number
  default     = 1209600 # 14 days
}

variable "enable_alarms" {
  description = "Enable CloudWatch alarms"
  type        = bool
  default     = true
}

variable "alarm_actions" {
  description = "Alarm action ARNs"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
