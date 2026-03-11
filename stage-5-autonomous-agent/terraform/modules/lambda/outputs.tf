output "agent_core_lambda_arn" {
  description = "ARN of the agent core Lambda function"
  value       = aws_lambda_function.agent_core.arn
}

output "agent_core_lambda_name" {
  description = "Name of the agent core Lambda function"
  value       = aws_lambda_function.agent_core.function_name
}

output "tool_executor_lambda_arn" {
  description = "ARN of the tool executor Lambda function"
  value       = aws_lambda_function.tool_executor.arn
}

output "tool_executor_lambda_name" {
  description = "Name of the tool executor Lambda function"
  value       = aws_lambda_function.tool_executor.function_name
}

output "reasoning_engine_lambda_arn" {
  description = "ARN of the reasoning engine Lambda function"
  value       = aws_lambda_function.reasoning_engine.arn
}

output "reasoning_engine_lambda_name" {
  description = "Name of the reasoning engine Lambda function"
  value       = aws_lambda_function.reasoning_engine.function_name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}
