variable "bucket_name" {
  description = "Name of the S3 bucket for document storage"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "index_lambda_arn" {
  description = "ARN of the index Lambda function"
  type        = string
}

variable "index_lambda_function_name" {
  description = "Name of the index Lambda function"
  type        = string
}
