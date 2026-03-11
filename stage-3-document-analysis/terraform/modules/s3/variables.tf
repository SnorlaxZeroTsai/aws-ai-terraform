variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

variable "sse_algorithm" {
  description = "Server-side encryption algorithm"
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "aws:kms"], var.sse_algorithm)
    error_message = "Must be AES256 or aws:kms"
  }
}

variable "enable_lifecycle" {
  description = "Enable lifecycle rules"
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  description = "Days to retain non-current versions"
  type        = number
  default     = 30
}

variable "logging_enabled" {
  description = "Enable S3 access logging"
  type        = bool
  default     = false
}

variable "logging_target_bucket" {
  description = "Target bucket for logs"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
