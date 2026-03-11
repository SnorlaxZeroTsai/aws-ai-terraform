variable "upload_function_name" {
  description = "Name of the upload handler Lambda function"
  type        = string
}

variable "analysis_function_name" {
  description = "Name of the analysis handler Lambda function"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for document uploads"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  type        = string
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "sqs_queue_arn" {
  description = "SQS queue ARN"
  type        = string
}

variable "sqs_queue_url" {
  description = "SQS queue URL"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic ARN"
  type        = string
}

variable "textract_features" {
  description = "Textract features to enable"
  type = list(object({
    name    = string
    enabled = bool
  }))
  default = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
