output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.this.id
}

output "api_arn" {
  description = "ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.this.arn
}

output "api_endpoint" {
  description = "Base URL of the API Gateway"
  value       = aws_api_gateway_rest_api.this.endpoint
}

output "execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.this.execution_arn
}

output "invoke_url" {
  description = "Invoke URL of the API Gateway (including stage)"
  value       = "${aws_api_gateway_rest_api.this.endpoint}/${aws_api_gateway_stage.this.stage_name}"
}

output "deployment_id" {
  description = "Deployment ID"
  value       = aws_api_gateway_deployment.this.id
}

output "stage_name" {
  description = "Stage name"
  value       = aws_api_gateway_stage.this.stage_name
}
