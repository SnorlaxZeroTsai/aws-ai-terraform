variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "max_iterations" {
  description = "Maximum agent reasoning iterations"
  type        = number
  default     = 10
}

variable "agent_core_lambda_arn" {
  description = "ARN of the agent core Lambda function"
  type        = string
}

variable "tool_executor_arn" {
  description = "ARN of the tool executor Lambda function"
  type        = string
}

variable "reasoning_engine_arn" {
  description = "ARN of the reasoning engine Lambda function"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
