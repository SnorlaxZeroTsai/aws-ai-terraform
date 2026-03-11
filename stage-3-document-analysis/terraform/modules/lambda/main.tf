# IAM Role for Lambda functions
resource "aws_iam_role" "lambda" {
  name = "${var.upload_function_name}-role"

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

  tags = var.tags
}

# IAM Policy for Lambda execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for S3 access
resource "aws_iam_role_policy" "s3_access" {
  name = "s3-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:HeadObject",
        ]
        Resource = "${var.s3_bucket_arn}/*"
      }
    ]
  })
}

# IAM Policy for DynamoDB access
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*",
        ]
      }
    ]
  })
}

# IAM Policy for SQS access
resource "aws_iam_role_policy" "sqs_access" {
  name = "sqs-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = var.sqs_queue_arn
      }
    ]
  })
}

# IAM Policy for SNS access
resource "aws_iam_role_policy" "sns_access" {
  name = "sns-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
        ]
        Resource = var.sns_topic_arn
      }
    ]
  })
}

# IAM Policy for Textract access
resource "aws_iam_role_policy" "textract_access" {
  name = "textract-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:StartDocumentAnalysis",
          "textract:GetDocumentAnalysis",
        ]
        Resource = "*"
      }
    ]
  })
}

# Upload Handler Lambda Function
resource "aws_lambda_function" "upload_handler" {
  filename         = data.archive_file.upload_handler.output_path
  function_name    = var.upload_function_name
  role            = aws_iam_role.lambda.arn
  handler         = "upload_handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  source_code_hash = data.archive_file.upload_handler.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      SQS_QUEUE_URL  = var.sqs_queue_url
    }
  }

  tags = var.tags

  depends_on = [
    aws_iam_role_policy.s3_access,
    aws_iam_role_policy.dynamodb_access,
    aws_iam_role_policy.sqs_access,
  ]
}

# Analysis Handler Lambda Function
resource "aws_lambda_function" "analysis_handler" {
  filename         = data.archive_file.analysis_handler.output_path
  function_name    = var.analysis_function_name
  role            = aws_iam_role.lambda.arn
  handler         = "analysis_handler.lambda_handler"
  runtime         = "python3.11"
  timeout         = 300  # 5 minutes for Textract processing
  memory_size     = 512

  source_code_hash = data.archive_file.analysis_handler.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE  = var.dynamodb_table_name
      SNS_TOPIC_ARN   = var.sns_topic_arn
      TEXTRACT_FEATURES = join(",", [
        for f in var.textract_features : f.name if f.enabled
      ])
    }
  }

  tags = var.tags

  depends_on = [
    aws_iam_role_policy.dynamodb_access,
    aws_iam_role_policy.sqs_access,
    aws_iam_role_policy.sns_access,
    aws_iam_role_policy.textract_access,
  ]
}

# S3 Event Trigger for Upload Handler
resource "aws_s3_bucket_notification" "upload_trigger" {
  bucket = var.s3_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.upload_handler.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "uploads/"
    filter_suffix       = ".pdf"
  }

  depends_on = [
    aws_lambda_permission.s3_upload_trigger,
  ]
}

# Lambda permission for S3 to invoke upload handler
resource "aws_lambda_permission" "s3_upload_trigger" {
  statement_id  = "AllowS3Invocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_bucket_arn
}

# SQS Trigger for Analysis Handler
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.analysis_handler.function_name
  batch_size       = 1
  enabled          = true
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "upload_handler" {
  name              = "/aws/lambda/${var.upload_function_name}"
  retention_in_days = 7

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "analysis_handler" {
  name              = "/aws/lambda/${var.analysis_function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Archive files for Lambda deployment packages
data "archive_file" "upload_handler" {
  type        = "zip"
  source_dir  = "${path.module}/../../src/handlers"
  output_path = "${path.module}/upload_handler.zip"

  depends_on = [
    null_resource.upload_handler_package,
  ]
}

# Null resource to prepare the Lambda package
resource "null_resource" "upload_handler_package" {
  triggers = {
    source_hash = sha256(join("", [
      "${file("${path.module}/../../src/handlers/upload_handler.py")}",
      "${file("${path.module}/../../src/models/document.py")}",
      "${file("${path.module}/../../src/services/textract_service.py")}",
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../../src
      pip install -r ../requirements.txt -t handlers/
      cp -r models handlers/
      cp -r services handlers/
    EOT
  }
}

data "archive_file" "analysis_handler" {
  type        = "zip"
  source_dir  = "${path.module}/../../src/handlers"
  output_path = "${path.module}/analysis_handler.zip"

  depends_on = [
    null_resource.analysis_handler_package,
  ]
}

# Null resource to prepare the Lambda package
resource "null_resource" "analysis_handler_package" {
  triggers = {
    source_hash = sha256(join("", [
      "${file("${path.module}/../../src/handlers/analysis_handler.py")}",
      "${file("${path.module}/../../src/models/document.py")}",
      "${file("${path.module}/../../src/services/textract_service.py")}",
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../../src
      pip install -r ../requirements.txt -t handlers/
      cp -r models handlers/
      cp -r services handlers/
    EOT
  }
}
