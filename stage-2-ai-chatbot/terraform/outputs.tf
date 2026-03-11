# Lambda Outputs
output "lambda_function_name" {
  description = "Name of the chat Lambda function"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "ARN of the chat Lambda function"
  value       = module.lambda.function_arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the chat Lambda function"
  value       = module.lambda.invoke_arn
}

# API Gateway Outputs
output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.api_id
}

output "api_gateway_endpoint_url" {
  description = "Base URL of the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_invoke_url" {
  description = "Invoke URL of the API Gateway (including stage)"
  value       = module.api_gateway.invoke_url
}

output "chat_endpoint_url" {
  description = "Full URL of the chat endpoint"
  value       = "${module.api_gateway.invoke_url}/chat"
}

# Secrets Manager Outputs
output "secret_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = module.secrets_manager.secret_arn
}

output "secret_name" {
  description = "Name of the Secrets Manager secret"
  value       = module.secrets_manager.secret_name
}

# CloudWatch Outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.lambda.log_group_name
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = module.cloudwatch.dashboard_url
}

# Combined Outputs
output "api_test_command" {
  description = "Curl command to test the chat endpoint"
  value       = "curl -X POST ${module.api_gateway.invoke_url}/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello!\"}'"
}
