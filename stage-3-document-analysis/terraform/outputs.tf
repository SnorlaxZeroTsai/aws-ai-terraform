output "s3_bucket_name" {
  description = "S3 bucket for document uploads"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3.bucket_arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  value       = try(module.sns_sqs.topic_arn, null)
}

output "sqs_queue_url" {
  description = "SQS queue URL for document processing"
  value       = try(module.sns_sqs.queue_url, null)
}

output "upload_function_name" {
  description = "Lambda upload handler function name"
  value       = try(module.lambda.upload_function_name, null)
}

output "analysis_function_name" {
  description = "Lambda analysis handler function name"
  value       = try(module.lambda.analysis_function_name, null)
}
