variable "platform_name" {
  description = "Platform name"
  type        = string
}

variable "create_xray_resources" {
  description = "Create X-Ray specific resources"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
  default     = null
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
