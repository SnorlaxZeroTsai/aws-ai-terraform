# Lambda Execution Role
resource "aws_iam_role" "lambda_execution" {
  name = "stage4-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "stage4-lambda-${var.environment}"
    Environment = var.environment
    Stage       = "4"
    Purpose     = "lambda-execution"
  }
}

# Lambda Security Group
resource "aws_security_group" "lambda" {
  name        = "stage4-lambda-${var.environment}"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "stage4-lambda-${var.environment}"
    Environment = var.environment
    Stage       = "4"
    Purpose     = "lambda-functions"
  }
}

# Basic Lambda Execution Role Policy for VPC access
resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# CloudWatch Logs Policy Attachment
resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Bedrock Access Policy
resource "aws_iam_role_policy" "bedrock_access" {
  name = "bedrock-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      Resource = "*"
    }]
  })
}

# S3 Access Policy
resource "aws_iam_role_policy" "s3_access" {
  name = "s3-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ]
      Resource = "${var.documents_bucket_arn}/*"
    }]
  })
}
