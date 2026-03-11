output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.this.dashboard_name
}

output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.this.dashboard_name}"
}

output "lambda_error_alarm_arn" {
  description = "ARN of the Lambda error alarm"
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.lambda_errors[0].arn : null
}

output "lambda_duration_alarm_arn" {
  description = "ARN of the Lambda duration alarm"
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.lambda_duration[0].arn : null
}

output "api_gateway_alarm_arn" {
  description = "ARN of the API Gateway 5XX alarm"
  value       = var.enable_alarms ? aws_cloudwatch_metric_alarm.api_gateway_5xx[0].arn : null
}
