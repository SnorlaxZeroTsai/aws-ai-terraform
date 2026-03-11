variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "document-analysis"
}

variable "allowed_file_types" {
  description = "Allowed file extensions"
  type        = list(string)
  default     = ["pdf", "png", "jpg", "jpeg"]
}

variable "max_file_size_mb" {
  description = "Maximum file size in MB"
  type        = number
  default     = 10

  validation {
    condition     = var.max_file_size_mb > 0 && var.max_file_size_mb <= 500
    error_message = "File size must be between 1 and 500 MB."
  }
}

variable "enable_async_processing" {
  description = "Enable SQS for async processing"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email for SNS notifications"
  type        = string
  default     = null
}

variable "textract_features" {
  description = "Textract features to enable"
  type = list(object({
    name    = string
    enabled = bool
  }))
  default = [
    { name = "TABLES", enabled = true },
    { name = "FORMS", enabled = true },
    { name = "LAYOUT", enabled = false }
  ]
}
