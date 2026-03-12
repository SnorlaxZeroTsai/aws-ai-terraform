# API Gateway Outputs
output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.api_id
}

output "api_gateway_endpoint" {
  description = "Base URL of the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "api_gateway_invoke_url" {
  description = "Invoke URL of the API Gateway (including stage)"
  value       = module.api_gateway.invoke_url
}

output "api_gateway_url" {
  description = "Full API Gateway URL with custom domain (if configured)"
  value       = module.api_gateway.api_url
}

# ECS Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs.cluster_arn
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs.service_name
}

output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = module.ecs.task_definition_arn
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  value       = module.ecs.security_group_id
}

# ECR Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecs.repository_url
}

output "ecr_repository_name" {
  description = "Name of the ECR repository"
  value       = module.ecs.repository_name
}

# Lambda Outputs
output "auth_function_name" {
  description = "Name of the authentication Lambda function"
  value       = try(module.lambda.auth_function_name, null)
}

output "auth_function_arn" {
  description = "ARN of the authentication Lambda function"
  value       = try(module.lambda.auth_function_arn, null)
}

# X-Ray Outputs
output "xray_enabled" {
  description = "Whether X-Ray tracing is enabled"
  value       = var.enable_xray
}

# CloudWatch Outputs
output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = module.cloudwatch.dashboard_name
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = module.cloudwatch.dashboard_url
}

output "cloudwatch_log_group_apis" {
  description = "CloudWatch log group for API Gateway"
  value       = module.cloudwatch.log_group_apis
}

output "cloudwatch_log_group_ecs" {
  description = "CloudWatch log group for ECS"
  value       = module.cloudwatch.log_group_ecs
}

# Alarm Outputs
output "alarm_high_error_rate_arn" {
  description = "ARN of the high error rate alarm"
  value       = try(module.cloudwatch.alarm_high_error_rate_arn, null)
}

output "alarm_high_latency_arn" {
  description = "ARN of the high latency alarm"
  value       = try(module.cloudwatch.alarm_high_latency_arn, null)
}

output "alarm_low_task_count_arn" {
  description = "ARN of the low task count alarm"
  value       = try(module.cloudwatch.alarm_low_task_count_arn, null)
}

# Integration Outputs (from previous stages)
output "stage2_chatbot_lambda_arn" {
  description = "ARN of Stage 2 chatbot Lambda"
  value       = try(data.terraform_remote_state.stage2.outputs.lambda_function_arn, null)
}

output "stage2_api_gateway_url" {
  description = "URL of Stage 2 API Gateway"
  value       = try(data.terraform_remote_state.stage2.outputs.api_gateway_invoke_url, null)
}

output "stage3_sqs_queue_url" {
  description = "URL of Stage 3 SQS queue"
  value       = try(data.terraform_remote_state.stage3.outputs.sqs_queue_url, null)
}

output "stage3_s3_bucket_name" {
  description = "Name of Stage 3 S3 bucket"
  value       = try(data.terraform_remote_state.stage3.outputs.s3_bucket_name, null)
}

output "stage4_opensearch_endpoint" {
  description = "Endpoint of Stage 4 OpenSearch domain"
  value       = try(data.terraform_remote_state.stage4.outputs.opensearch_domain_endpoint, null)
}

output "stage4_search_lambda_arn" {
  description = "ARN of Stage 4 search Lambda"
  value       = try(data.terraform_remote_state.stage4.outputs.search_lambda_function_arn, null)
}

output "stage5_step_function_arn" {
  description = "ARN of Stage 5 Step Function"
  value       = try(data.terraform_remote_state.stage5.outputs.step_function_arn, null)
}

output "stage5_agent_core_lambda_arn" {
  description = "ARN of Stage 5 agent core Lambda"
  value       = try(data.terraform_remote_state.stage5.outputs.agent_core_lambda_arn, null)
}

# Combined Outputs
output "platform_health_endpoint" {
  description = "Health check endpoint URL"
  value       = "${module.api_gateway.invoke_url}/health"
}

output "platform_agents_endpoint" {
  description = "List agents endpoint URL"
  value       = "${module.api_gateway.invoke_url}/agents"
}

output "platform_chatbot_endpoint" {
  description = "Chatbot endpoint URL"
  value       = "${module.api_gateway.invoke_url}/v1/chat"
}

output "platform_rag_endpoint" {
  description = "RAG endpoint URL"
  value       = "${module.api_gateway.invoke_url}/v1/rag"
}

output "platform_agent_endpoint" {
  description = "Autonomous agent endpoint URL"
  value       = "${module.api_gateway.invoke_url}/v1/agent"
}

output "platform_document_endpoint" {
  description = "Document analysis endpoint URL"
  value       = "${module.api_gateway.invoke_url}/v1/document"
}

# Utility Outputs
output "deployment_commands" {
  description = "Useful commands for deployment and testing"
  value = {
    health_check = "curl ${module.api_gateway.invoke_url}/health"
    list_agents  = "curl ${module.api_gateway.invoke_url}/agents"
    test_chat    = "curl -X POST ${module.api_gateway.invoke_url}/v1/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello!\"}'"
  }
}
