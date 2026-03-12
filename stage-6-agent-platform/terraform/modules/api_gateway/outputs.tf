output "api_id" {
  description = "API Gateway ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_arn" {
  description = "API Gateway ARN"
  value       = aws_api_gateway_rest_api.main.arn
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_rest_api.main.endpoint
}

output "invoke_url" {
  description = "API Gateway invoke URL with stage"
  value       = "${aws_api_gateway_rest_api.main.endpoint}/${aws_api_gateway_stage.main.stage_name}"
}

output "deployment_id" {
  description = "Deployment ID"
  value       = aws_api_gateway_deployment.main.id
}

output "stage_name" {
  description = "Stage name"
  value       = aws_api_gateway_stage.main.stage_name
}

output "api_url" {
  description = "Full API URL (with custom domain if configured)"
  value = var.domain_name != null ? "https://${var.domain_name}/api" : "${aws_api_gateway_rest_api.main.endpoint}/${aws_api_gateway_stage.main.stage_name}"
}

output "vpc_link_id" {
  description = "VPC Link ID"
  value       = aws_api_gateway_vpc_link.ecs.id
}

output "authorizer_id" {
  description = "Authorizer ID"
  value       = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : null
}

output "log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.api_gateway.arn
}

output "domain_name" {
  description = "Custom domain name"
  value       = var.domain_name != null ? aws_api_gateway_domain_name.custom[0].domain_name : null
}
