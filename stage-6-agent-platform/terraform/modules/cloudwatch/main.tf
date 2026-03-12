# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.platform_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/APIGateway", "Count", "ApiName", var.api_gateway_name, "Region", var.aws_region],
            [".", "5XXError", ".", ".", ".", "."],
            [".", "4XXError", ".", ".", ".", "."],
            [".", "Latency", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "API Gateway Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."],
            [".", "RunningTaskCount", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Metrics"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6

        properties = {
          logs = [
            {
              logGroup  = aws_cloudwatch_log_group.platform.name
              region    = var.aws_region
              title     = "Platform Logs"
              view      = "Table"
            }
          ]
        }
      }
    ]
  })
}

# Platform log group
resource "aws_cloudwatch_log_group" "platform" {
  name              = "/aws/${var.platform_name}"
  retention_in_days = var.log_retention_days

  tags = var.common_tags
}

# API Gateway Alarms
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.platform_name}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/APIGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.api_5xx_threshold
  alarm_description   = "Alert when API Gateway returns too many 5XX errors"
  alarm_actions       = var.enable_sns ? [aws_sns_topic.alarms[0].arn] : []

  dimensions = {
    ApiName = var.api_gateway_name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.platform_name}-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Latency"
  namespace           = "AWS/APIGateway"
  period              = "300"
  statistic           = "Average"
  threshold           = var.api_latency_threshold
  alarm_description   = "Alert when API Gateway latency is high"
  alarm_actions       = var.enable_sns ? [aws_sns_topic.alarms[0].arn] : []

  dimensions = {
    ApiName = var.api_gateway_name
  }

  tags = var.common_tags
}

# ECS Alarms
resource "aws_cloudwatch_metric_alarm" "ecs_cpu" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.platform_name}-ecs-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.ecs_cpu_threshold
  alarm_description   = "Alert when ECS CPU is high"
  alarm_actions       = var.enable_sns ? [aws_sns_topic.alarms[0].arn] : []

  dimensions = {
    ServiceName = var.ecs_service_name
    ClusterName = var.ecs_cluster_name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.platform_name}-ecs-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = var.ecs_memory_threshold
  alarm_description   = "Alert when ECS memory is high"
  alarm_actions       = var.enable_sns ? [aws_sns_topic.alarms[0].arn] : []

  dimensions = {
    ServiceName = var.ecs_service_name
    ClusterName = var.ecs_cluster_name
  }

  tags = var.common_tags
}

# SNS Topic for alarms
resource "aws_sns_topic" "alarms" {
  count = var.enable_alarms && var.enable_sns ? 1 : 0
  name   = "${var.platform_name}-alarms"

  tags = var.common_tags
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.enable_alarms && var.enable_sns && var.alarm_email != null ? 1 : 0
  topic_arn = aws_sns_topic.alarms[0].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
