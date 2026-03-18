# SNS Topic for notifications
resource "aws_sns_topic" "this" {
  count = var.enabled ? 1 : 0

  name = var.topic_name

  tags = var.tags
}

# SNS Topic Subscription for Email
resource "aws_sns_topic_subscription" "email" {
  count = var.enabled && var.notification_email != null ? 1 : 0

  topic_arn = aws_sns_topic.this[0].arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# SQS Queue for document processing
resource "aws_sqs_queue" "this" {
  count = var.enabled ? 1 : 0

  name                      = var.queue_name
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds = var.receive_wait_time_seconds
  visibility_timeout_seconds = var.visibility_timeout_seconds

  # Dead Letter Queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq[0].arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  count = var.enabled ? 1 : 0

  name                      = "${var.queue_name}-dlq"
  message_retention_seconds = var.dlq_retention_seconds

  tags = var.tags
}

# SQS Queue Policy to allow S3 to send messages
resource "aws_sqs_queue_policy" "this" {
  count = var.enabled ? 1 : 0

  queue_url = aws_sqs_queue.this[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.this[0].arn

        Condition = {
          ArnLike = {
            "aws:SourceArn" = var.s3_bucket_arn
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.this[0].arn

        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# CloudWatch Alarms for SQS
resource "aws_cloudwatch_metric_alarm" "dlq_alert" {
  count = var.enabled && var.enable_alarms ? 1 : 0

  alarm_name          = "${var.queue_name}-dlq-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "0"

  dimensions = {
    QueueName = aws_sqs_queue.dlq[0].name
  }

  alarm_actions = var.alarm_actions
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
