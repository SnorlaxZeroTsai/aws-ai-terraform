variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "description" {
  description = "Description of the API Gateway"
  type        = string
  default     = "AI Chatbot API"
}

variable "stage_name" {
  description = "Deployment stage name"
  type        = string
  default     = "v1"
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to integrate"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to integrate"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  type        = string
}

variable "enable_cors" {
  description = "Enable CORS on the API"
  type        = bool
  default     = true
}

variable "cors_allowed_origins" {
  description = "Allowed CORS origins"
  type        = list(string)
  default     = ["*"]
}

variable "cors_allowed_methods" {
  description = "Allowed CORS methods"
  type        = list(string)
  default     = ["POST", "OPTIONS"]
}

variable "cors_allowed_headers" {
  description = "Allowed CORS headers"
  type        = list(string)
  default     = ["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
}

variable "tags" {
  description = "Tags to apply to the API Gateway"
  type        = map(string)
  default     = {}
}
