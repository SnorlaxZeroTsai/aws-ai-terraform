# DynamoDB Table for Document Metadata
resource "aws_dynamodb_table" "this" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "document_id"
  range_key      = "uploaded_at"

  attribute {
    name = "document_id"
    type = "S"
  }

  attribute {
    name = "uploaded_at"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "filename"
    type = "S"
  }

  # Global Secondary Index for querying by status
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "uploaded_at"
    projection_type = "ALL"
  }

  # Global Secondary Index for querying by filename
  global_secondary_index {
    name            = "filename-index"
    hash_key        = "filename"
    range_key       = "uploaded_at"
    projection_type = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  tags = var.tags

  # Lifecycle: ignore changes to replica count (if adding global tables later)
  lifecycle {
    ignore_changes = [replicas]
  }
}

# DynamoDB Auto Scaling (optional for on-demand)
resource "aws_appautoscaling_target" "read_target" {
  count = var.enable_autoscaling ? 1 : 0

  max_capacity       = var.autoscaling_max_read_capacity
  min_capacity       = var.autoscaling_min_read_capacity
  resource_id        = "table/${aws_dynamodb_table.this.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

# CloudWatch Alarms for DynamoDB
resource "aws_cloudwatch_metric_alarm" "throttle_errors" {
  count = var.enable_alarms ? 1 : 0

  alarm_name          = "${var.table_name}-throttle-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"

  dimensions = {
    TableName = aws_dynamodb_table.this.name
  }

  alarm_actions = var.alarm_actions
}
