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
