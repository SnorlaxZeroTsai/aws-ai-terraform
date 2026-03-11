output "step_function_arn" {
  description = "ARN of the Step Functions state machine"
  value       = try(aws_sfn_state_machine.agent_workflow[0].arn, null)
}

output "step_function_name" {
  description = "Name of the Step Functions state machine"
  value       = try(aws_sfn_state_machine.agent_workflow[0].name, null)
}

output "agent_core_lambda_arn" {
  description = "ARN of the agent core Lambda function"
  value       = try(aws_lambda_function.agent_core[0].arn, null)
}

output "agent_core_lambda_name" {
  description = "Name of the agent core Lambda function"
  value       = try(aws_lambda_function.agent_core[0].function_name, null)
}

output "tool_executor_lambda_arn" {
  description = "ARN of the tool executor Lambda function"
  value       = try(aws_lambda_function.tool_executor[0].arn, null)
}

output "reasoning_lambda_arn" {
  description = "ARN of the reasoning engine Lambda function"
  value       = try(aws_lambda_function.reasoning_engine[0].arn, null)
}

output "conversation_memory_table_name" {
  description = "Name of the conversation memory DynamoDB table"
  value       = try(aws_dynamodb_table.conversation_memory[0].name, null)
}

output "episodic_memory_table_name" {
  description = "Name of the episodic memory DynamoDB table"
  value       = try(aws_dynamodb_table.episodic_memory[0].name, null)
}

output "semantic_memory_table_name" {
  description = "Name of the semantic memory DynamoDB table"
  value       = try(aws_dynamodb_table.semantic_memory[0].name, null)
}

output "tool_definitions_bucket" {
  description = "S3 bucket for tool definitions"
  value       = try(aws_s3_bucket.tool_definitions[0].id, null)
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda functions"
  value       = try(aws_cloudwatch_log_group.agent_logs[0].name, null)
}

output "vpc_id" {
  description = "VPC ID from Stage 1"
  value       = try(data.terraform_remote_state.stage1.outputs.vpc_id, null)
}

output "private_subnet_ids" {
  description = "Private subnet IDs from Stage 1"
  value       = try(data.terraform_remote_state.stage1.outputs.private_subnet_ids, null)
}

output "agent_api_endpoint" {
  description = "API endpoint to invoke the agent"
  value       = try(aws_apigatewayv2_api.agent_api[0].api_endpoint, null)
}
