output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "log_group_platform" {
  description = "Platform log group"
  value       = aws_cloudwatch_log_group.platform.name
}

output "alarm_high_error_rate_arn" {
  description = "High error rate alarm ARN"
  value       = try(aws_cloudwatch_metric_alarm.api_5xx[0].arn, null)
}

output "alarm_high_latency_arn" {
  description = "High latency alarm ARN"
  value       = try(aws_cloudwatch_metric_alarm.api_latency[0].arn, null)
}

output "alarm_low_task_count_arn" {
  description = "Low task count alarm ARN"
  value       = try(aws_cloudwatch_metric_alarm.ecs_cpu[0].arn, null)
}
