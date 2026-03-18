# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "log"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          logs = [
            {
              logGroupName  = "/aws/lambda/${var.lambda_function_name}"
              title         = "Lambda Logs"
              view          = "Table"
              region        = data.aws_region.current.name
              stat          = "Count"
              stacked       = false
              query         = "fields @timestamp, @message\n| sort @timestamp desc\n| limit 100"
            }
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 6
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", [{ "name" = "FunctionName", "value" = var.lambda_function_name }], { "stat" : "Sum" }],
            [".", "Errors", ".", { "stat" : "Sum" }],
            [".", "Throttles", ".", { "stat" : "Sum" }],
            [".", "Duration", ".", { "stat" : "Average" }],
            [".", "ConcurrentExecutions", ".", { "stat" : "Average" }]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "Lambda Metrics"
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 6
        width  = 6
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", [{ "name" = "ApiId", "value" : var.api_gateway_id }], { "stat" : "Sum" }],
            [".", "4XXError", ".", { "stat" : "Sum" }],
            [".", "5XXError", ".", { "stat" : "Sum" }],
            [".", "IntegrationLatency", ".", { "stat" : "Average" }],
            [".", "Latency", ".", { "stat" : "Average" }]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "API Gateway Metrics"
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            [{
              expression = "errors/(invocations) * 100",
              label      = "Error Rate (%)",
              id         = "e1"
            }],
            [{"expression" = "m1/1000", "label" = "Duration (s)", "id" = "m1" }],
            ["AWS/Lambda", "Invocations", [{ "name" = "FunctionName", "value" = var.lambda_function_name }], { "id" = "m1", "visible" = false }],
            ["AWS/Lambda", "Errors", ".", { "id" = "m2", "visible" = "false" }]
          ]
          period = 300
          region = data.aws_region.current.name
          title  = "Lambda Error Rate"
          view   = "timeSeries"
        }
      }
    ]
  })
}

# Lambda Error Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count             = var.enable_alarms ? 1 : 0
  alarm_name        = "${var.lambda_function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name       = "Errors"
  namespace         = "AWS/Lambda"
  period            = "300"
  statistic         = "Sum"
  threshold         = 5
  alarm_description = "This alarm monitors Lambda function errors"
  alarm_actions     = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    FunctionName = var.lambda_function_name
  }
}

# Lambda Duration Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count             = var.enable_alarms ? 1 : 0
  alarm_name        = "${var.lambda_function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name       = "Duration"
  namespace         = "AWS/Lambda"
  period            = "300"
  statistic         = "Average"
  threshold         = var.latency_threshold_ms
  alarm_description = "This alarm monitors Lambda function duration"
  alarm_actions     = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    FunctionName = var.lambda_function_name
  }
}

# API Gateway 5XX Error Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  count             = var.enable_alarms ? 1 : 0
  alarm_name        = "${var.api_gateway_id}-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name       = "5XXError"
  namespace         = "AWS/ApiGateway"
  period            = "300"
  statistic         = "Sum"
  threshold         = 10
  alarm_description = "This alarm monitors API Gateway 5XX errors"
  alarm_actions     = var.alarm_sns_topic_arn != null ? [var.alarm_sns_topic_arn] : []

  dimensions = {
    ApiId = var.api_gateway_id
  }
}

# Data source for AWS region
data "aws_region" "current" {}
