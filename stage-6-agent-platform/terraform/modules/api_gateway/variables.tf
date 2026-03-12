variable "platform_name" {
  description = "Platform name"
  type        = string
}

variable "api_name" {
  description = "API Gateway name"
  type        = string
}

variable "stage_name" {
  description = "Deployment stage name"
  type        = string
}

variable "orchestrator_url" {
  description = "URL of the orchestrator service"
  type        = string
}

variable "load_balancer_arns" {
  description = "ARNs of load balancers for VPC link"
  type        = list(string)
}

variable "auth_type" {
  description = "Authentication type"
  type        = string
}

variable "authorizer_lambda_invoke_arn" {
  description = "Invoke ARN of authorizer Lambda"
  type        = string
  default     = null
}

variable "authorizer_role_arn" {
  description = "IAM role ARN for authorizer"
  type        = string
  default     = null
}

variable "cloudwatch_role_arn" {
  description = "CloudWatch role ARN for API Gateway"
  type        = string
  default     = null
}

variable "throttling_burst_limit" {
  description = "Throttling burst limit"
  type        = number
}

variable "throttling_rate_limit" {
  description = "Throttling rate limit"
  type        = number
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
}

variable "log_retention_days" {
  description = "Log retention days"
  type        = number
}

variable "domain_name" {
  description = "Custom domain name"
  type        = string
  default     = null
}

variable "certificate_arn" {
  description = "ACM certificate ARN"
  type        = string
  default     = null
}

variable "lambda_integrations" {
  description = "Lambda functions to integrate with"
  type = list(object({
    function_name = string
    invoke_arn    = string
  }))
  default = []
}

variable "common_tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
