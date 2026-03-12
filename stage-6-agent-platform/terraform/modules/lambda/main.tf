# Create IAM role for Lambda functions
resource "aws_iam_role" "lambda" {
  count = length(var.functions) > 0 ? 1 : 0
  name  = "${var.platform_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  count      = length(var.functions) > 0 ? 1 : 0
  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  count      = length(var.functions) > 0 && var.vpc_config != null ? 1 : 0
  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count      = length(var.functions) > 0 && var.enable_xray ? 1 : 0
  role       = aws_iam_role.lambda[0].name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Create Lambda functions
resource "aws_lambda_function" "functions" {
  count = length(var.functions)

  function_name = "${var.platform_name}-${var.functions[count.index].name}"
  description   = var.functions[count.index].description
  handler       = var.functions[count.index].handler
  runtime       = var.functions[count.index].runtime
  timeout       = var.functions[count.index].timeout
  memory_size   = var.functions[count.index].memory_size
  role          = aws_iam_role.lambda[0].arn

  s3_bucket = var.functions[count.index].s3_bucket
  s3_key    = var.functions[count.index].s3_key

  environment {
    variables = merge(
      {
        PLATFORM_NAME = var.platform_name
        ENVIRONMENT   = var.environment
        AWS_REGION    = var.aws_region
      },
      var.functions[count.index].environment
    )
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  tags = merge(
    var.common_tags,
    {
      Function = var.functions[count.index].name
    }
  )

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_vpc,
    aws_cloudwatch_log_group.lambda
  ]
}

# Create CloudWatch log groups
resource "aws_cloudwatch_log_group" "lambda" {
  count             = length(var.functions)
  name              = "/aws/lambda/${var.platform_name}-${var.functions[count.index].name}"
  retention_in_days = var.log_retention_days

  tags = var.common_tags
}
