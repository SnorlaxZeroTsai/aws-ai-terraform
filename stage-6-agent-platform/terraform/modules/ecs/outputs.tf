output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.main.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.main.arn
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.orchestrator.arn
}

output "task_definition_family" {
  description = "Task definition family"
  value       = aws_ecs_task_definition.orchestrator.family
}

output "repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.orchestrator.repository_url
}

output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.orchestrator.name
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.ecs_tasks.id
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "execution_role_arn" {
  description = "Execution role ARN"
  value       = aws_iam_role.ecs_execution.arn
}

output "task_role_arn" {
  description = "Task role ARN"
  value       = aws_iam_role.ecs_task.arn
}
