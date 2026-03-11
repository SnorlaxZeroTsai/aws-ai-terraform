output "index_function_name" {
  description = "Name of the index Lambda function"
  value       = aws_lambda_function.index.function_name
}

output "index_function_arn" {
  description = "ARN of the index Lambda function"
  value       = aws_lambda_function.index.arn
}

output "search_function_name" {
  description = "Name of the search Lambda function"
  value       = aws_lambda_function.search.function_name
}

output "search_function_arn" {
  description = "ARN of the search Lambda function"
  value       = aws_lambda_function.search.arn
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.name
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = aws_security_group.lambda.id
}
