# X-Ray is enabled at the service level (API Gateway, Lambda, ECS)
# This module provides additional X-Ray resources

resource "aws_iam_role" "xray" {
  count = var.create_xray_resources ? 1 : 0
  name  = "${var.platform_name}-xray-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "xray.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy" "xray" {
  count = var.create_xray_resources ? 1 : 0
  name  = "${var.platform_name}-xray-policy"
  role  = aws_iam_role.xray[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_xray_sampling_rule" "main" {
  count = var.create_xray_resources ? 1 : 0

  rule_name      = "${var.platform_name}-sampling-rule"
  priority       = 100
  version        = 1
  reservoir_size = 10
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  service_type   = "*"
  resource_arn   = "*"
  method         = "*"

  tags = var.common_tags
}

# Encrypted X-Ray encryption config
resource "aws_xray_encryption_config" "main" {
  count = var.create_xray_resources && var.kms_key_arn != null ? 1 : 0
  type  = "KMS"
  key_id = var.kms_key_arn
}
