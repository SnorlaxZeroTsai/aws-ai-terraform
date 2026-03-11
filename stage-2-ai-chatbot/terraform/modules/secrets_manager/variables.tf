variable "secret_name" {
  description = "Name of the secret"
  type        = string
}

variable "description" {
  description = "Description of the secret"
  type        = string
  default     = "AI Chatbot configuration and API keys"
}

variable "secret_value" {
  description = "Secret value as a map of key-value pairs"
  type        = map(string)
  default = {
    # Example: Add your API keys and configuration here
    # BEDROCK_API_KEY = "your-api-key-here"
  }
  sensitive = true
}

variable "recovery_window_in_days" {
  description = "Number of days to retain deleted secret before permanent deletion"
  type        = number
  default     = 30

  validation {
    condition     = var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30
    error_message = "Recovery window must be between 7 and 30 days."
  }
}

variable "kms_key_id" {
  description = "KMS key ID to use for encryption. If null, default alias/aws/secretsmanager key is used"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to the secret"
  type        = map(string)
  default     = {}
}
