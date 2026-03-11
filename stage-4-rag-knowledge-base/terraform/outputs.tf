# VPC Outputs (from Stage 1)
output "vpc_id" {
  description = "VPC ID from Stage 1"
  value       = data.terraform_remote_state.stage1.outputs.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs from Stage 1"
  value       = data.terraform_remote_state.stage1.outputs.private_subnet_ids
}

# OpenSearch Outputs
output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = module.opensearch.domain_arn
}

output "opensearch_security_group_id" {
  description = "OpenSearch security group ID"
  value       = module.opensearch.security_group_id
}

# S3 Outputs
output "documents_bucket_name" {
  description = "S3 bucket name for documents"
  value       = module.s3.bucket_name
}

output "documents_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3.bucket_arn
}

# Lambda Outputs
output "index_lambda_function_name" {
  description = "Index Lambda function name"
  value       = module.lambda.index_function_name
}

output "index_lambda_function_arn" {
  description = "Index Lambda function ARN"
  value       = module.lambda.index_function_arn
}

output "search_lambda_function_name" {
  description = "Search Lambda function name"
  value       = module.lambda.search_function_name
}

output "search_lambda_function_arn" {
  description = "Search Lambda function ARN"
  value       = module.lambda.search_function_arn
}

# API Gateway Outputs
output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = module.lambda.api_gateway_url
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = module.lambda.api_gateway_id
}

# Bedrock Outputs
output "bedrock_enabled" {
  description = "Bedrock models enabled"
  value       = module.bedrock.models_enabled
}
