variable "project_name" {
  description = "Project name"
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

variable "timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for reasoning"
  type        = string
}

variable "max_iterations" {
  description = "Maximum agent iterations"
  type        = number
  default     = 10
}

variable "conversation_table" {
  description = "Conversation memory table name"
  type        = string
}

variable "episodic_table" {
  description = "Episodic memory table name"
  type        = string
}

variable "semantic_table" {
  description = "Semantic memory table name"
  type        = string
}

variable "tool_results_table" {
  description = "Tool results table name"
  type        = string
}

variable "tool_bucket" {
  description = "S3 bucket for tool definitions"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Lambda functions"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "Subnet IDs for Lambda functions"
  type        = list(string)
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
