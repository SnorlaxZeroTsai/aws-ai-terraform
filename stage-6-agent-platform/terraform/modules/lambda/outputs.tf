output "function_names" {
  description = "Lambda function names"
  value       = aws_lambda_function.functions[*].function_name
}

output "function_arns" {
  description = "Lambda function ARNs"
  value       = aws_lambda_function.functions[*].arn
}

output "invoke_arns" {
  description = "Lambda invoke ARNs"
  value       = aws_lambda_function.functions[*].invoke_arn
}

output "role_arn" {
  description = "Lambda IAM role ARN"
  value       = try(aws_iam_role.lambda[0].arn, null)
}
