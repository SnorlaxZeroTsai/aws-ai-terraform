variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "read_capacity" {
  description = "Read capacity units (-1 for on-demand)"
  type        = number
  default     = -1
}

variable "write_capacity" {
  description = "Write capacity units (-1 for on-demand)"
  type        = number
  default     = -1
}

variable "memory_ttl_days" {
  description = "TTL for memory records in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
