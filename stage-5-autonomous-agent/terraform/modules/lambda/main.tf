# Lambda Module for Agent Functions

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_role" {
  name               = "${var.project_name}-lambda-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = var.tags
}

# IAM Policy for Lambda execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Bedrock access
resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.project_name}-bedrock-access-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:*:::foundation-model/*"
      }
    ]
  })
}

# IAM Policy for DynamoDB access
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.project_name}-dynamodb-access-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/${var.conversation_table}",
          "arn:aws:dynamodb:*:*:table/${var.episodic_table}",
          "arn:aws:dynamodb:*:*:table/${var.semantic_table}",
          "arn:aws:dynamodb:*:*:table/${var.tool_results_table}"
        ]
      }
    ]
  })
}

# IAM Policy for S3 access
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_name}-s3-access-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.tool_bucket}",
          "arn:aws:s3:::${var.tool_bucket}/*"
        ]
      }
    ]
  })
}

# IAM Policy for Step Functions access
resource "aws_iam_role_policy" "stepfunctions_access" {
  name = "${var.project_name}-stepfunctions-access-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = "arn:aws:states:*:*:stateMachine:*"
      }
    ]
  })
}

# VPC access policy (if VPC provided)
resource "aws_iam_role_policy" "vpc_access" {
  count = var.vpc_id != null ? 1 : 0
  name  = "${var.project_name}-vpc-access-${var.environment}"
  role  = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Agent Core Lambda Function
resource "aws_lambda_function" "agent_core" {
  function_name    = "${var.project_name}-agent-core-${var.environment}"
  description      = "Core agent orchestration and ReAct loop"
  role            = aws_iam_role.lambda_role.arn
  runtime         = "python3.11"
  handler         = "agent.core.lambda_handler"
  timeout         = var.timeout
  memory_size     = var.memory_size
  source_code_hash = data.archive_file.agent_core_zip.output_base64sha256

  filename         = data.archive_file.agent_core_zip.output_path

  environment {
    variables = {
      BEDROCK_MODEL_ID      = var.bedrock_model_id
      CONVERSATION_TABLE    = var.conversation_table
      EPISODIC_TABLE        = var.episodic_table
      SEMANTIC_TABLE        = var.semantic_table
      TOOL_RESULTS_TABLE    = var.tool_results_table
      TOOL_BUCKET           = var.tool_bucket
      AWS_REGION            = var.aws_region
      MAX_ITERATIONS        = var.max_iterations
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_id != null ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = [aws_security_group.lambda_sg[0].id]
    }
  }

  tags = var.tags

  depends_on = [aws_cloudwatch_log_group.agent_logs]
}

# Tool Executor Lambda Function
resource "aws_lambda_function" "tool_executor" {
  function_name    = "${var.project_name}-tool-executor-${var.environment}"
  description      = "Execute agent tools and return results"
  role            = aws_iam_role.lambda_role.arn
  runtime         = "python3.11"
  handler         = "tools.executor.lambda_handler"
  timeout         = var.timeout
  memory_size     = var.memory_size
  source_code_hash = data.archive_file.tool_executor_zip.output_base64sha256

  filename         = data.archive_file.tool_executor_zip.output_path

  environment {
    variables = {
      TOOL_RESULTS_TABLE    = var.tool_results_table
      TOOL_BUCKET           = var.tool_bucket
      AWS_REGION            = var.aws_region
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_id != null ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = [aws_security_group.lambda_sg[0].id]
    }
  }

  tags = var.tags
}

# Reasoning Engine Lambda Function
resource "aws_lambda_function" "reasoning_engine" {
  function_name    = "${var.project_name}-reasoning-engine-${var.environment}"
  description      = "LLM-based reasoning engine for agent decisions"
  role            = aws_iam_role.lambda_role.arn
  runtime         = "python3.11"
  handler         = "agent.reasoning.lambda_handler"
  timeout         = var.timeout
  memory_size     = var.memory_size
  source_code_hash = data.archive_file.reasoning_zip.output_base64sha256

  filename         = data.archive_file.reasoning_zip.output_path

  environment {
    variables = {
      BEDROCK_MODEL_ID      = var.bedrock_model_id
      CONVERSATION_TABLE    = var.conversation_table
      EPISODIC_TABLE        = var.episodic_table
      AWS_REGION            = var.aws_region
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_id != null ? [1] : []
    content {
      subnet_ids         = var.subnet_ids
      security_group_ids = [aws_security_group.lambda_sg[0].id]
    }
  }

  tags = var.tags
}

# Security Group for Lambda (if VPC provided)
resource "aws_security_group" "lambda_sg" {
  count       = var.vpc_id != null ? 1 : 0
  name        = "${var.project_name}-lambda-sg-${var.environment}"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "agent_logs" {
  name              = "/aws/lambda/${var.project_name}-agent-core"
  retention_in_days = 7

  tags = var.tags
}

# Archive files for Lambda (placeholder - will be replaced by actual code)
data "archive_file" "agent_core_zip" {
  type        = "zip"
  output_path = "${path.module}/agent_core.zip"

  source {
    content = "# Placeholder for agent core code"
    filename = "agent/core.py"
  }
}

data "archive_file" "tool_executor_zip" {
  type        = "zip"
  output_path = "${path.module}/tool_executor.zip"

  source {
    content = "# Placeholder for tool executor code"
    filename = "tools/executor.py"
  }
}

data "archive_file" "reasoning_zip" {
  type        = "zip"
  output_path = "${path.module}/reasoning.zip"

  source {
    content = "# Placeholder for reasoning engine code"
    filename = "agent/reasoning.py"
  }
}
