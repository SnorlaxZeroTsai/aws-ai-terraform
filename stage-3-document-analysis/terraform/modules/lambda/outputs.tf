output "upload_function_name" {
  description = "Upload handler function name"
  value       = aws_lambda_function.upload_handler.function_name
}

output "upload_function_arn" {
  description = "Upload handler function ARN"
  value       = aws_lambda_function.upload_handler.arn
}

output "analysis_function_name" {
  description = "Analysis handler function name"
  value       = aws_lambda_function.analysis_handler.function_name
}

output "analysis_function_arn" {
  description = "Analysis handler function ARN"
  value       = aws_lambda_function.analysis_handler.arn
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda.arn
}
