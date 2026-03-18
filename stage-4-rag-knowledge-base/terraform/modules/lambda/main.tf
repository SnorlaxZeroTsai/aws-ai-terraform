# Index Lambda Function
resource "aws_lambda_function" "index" {
  function_name    = "stage4-lambda-index-${var.environment}"
  description      = "Lambda function for indexing documents into OpenSearch"
  runtime          = "python3.11"
  handler          = "index_handler.handler"
  role             = var.lambda_execution_role_arn
  timeout          = var.index_lambda_timeout
  memory_size      = var.index_lambda_memory_size
  source_code_hash = data.archive_file.index_lambda.output_base64sha256
  filename         = data.archive_file.index_lambda.output_path

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  environment {
    variables = {
      OPENSEARCH_DOMAIN_ENDPOINT = var.opensearch_domain_endpoint
      BEDROCK_EMBEDDING_MODEL    = var.bedrock_embedding_model
      BEDROCK_LLM_MODEL          = var.bedrock_llm_model
      CHUNK_SIZE                 = var.chunk_size
      CHUNK_OVERLAP              = var.chunk_overlap
      VECTOR_DIMENSION           = var.vector_dimension
      LOG_LEVEL                  = "INFO"
    }
  }

  tags = {
    Name    = "stage4-lambda-index-${var.environment}"
    Stage   = "4"
    Purpose = "document-indexing"
  }

  depends_on = [
    aws_cloudwatch_log_group.index_lambda
  ]
}

# CloudWatch Log Group for Index Lambda
resource "aws_cloudwatch_log_group" "index_lambda" {
  name              = "/aws/lambda/stage4-lambda-index-${var.environment}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-index-lambda-logs-${var.environment}"
    Stage = "4"
  }
}

# Search Lambda Function
resource "aws_lambda_function" "search" {
  function_name    = "stage4-lambda-search-${var.environment}"
  description      = "Lambda function for RAG search queries"
  runtime          = "python3.11"
  handler          = "search_handler.handler"
  role             = var.lambda_execution_role_arn
  timeout          = var.search_lambda_timeout
  memory_size      = var.search_lambda_memory_size
  source_code_hash = data.archive_file.search_lambda.output_base64sha256
  filename         = data.archive_file.search_lambda.output_path

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  environment {
    variables = {
      OPENSEARCH_DOMAIN_ENDPOINT = var.opensearch_domain_endpoint
      BEDROCK_EMBEDDING_MODEL    = var.bedrock_embedding_model
      BEDROCK_LLM_MODEL          = var.bedrock_llm_model
      MAX_RESULTS                = var.max_results
      VECTOR_DIMENSION           = var.vector_dimension
      LOG_LEVEL                  = "INFO"
    }
  }

  tags = {
    Name    = "stage4-lambda-search-${var.environment}"
    Stage   = "4"
    Purpose = "rag-search"
  }

  depends_on = [
    aws_cloudwatch_log_group.search_lambda
  ]
}

# CloudWatch Log Group for Search Lambda
resource "aws_cloudwatch_log_group" "search_lambda" {
  name              = "/aws/lambda/stage4-lambda-search-${var.environment}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-search-lambda-logs-${var.environment}"
    Stage = "4"
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "stage4-rag-api-${var.environment}"
  description = "API Gateway for RAG Knowledge Base"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name    = "stage4-rag-api-${var.environment}"
    Stage   = "4"
    Purpose = "rag-api"
  }
}

# API Gateway Resource for Search
resource "aws_api_gateway_resource" "search" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "search"
}

# API Gateway POST Method for Search
resource "aws_api_gateway_method" "search_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.search.id
  http_method   = "POST"
  authorization = "NONE"
}

# API Gateway Integration for Search
resource "aws_api_gateway_integration" "search_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.search.id
  http_method = aws_api_gateway_method.search_post.http_method

  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.search.invoke_arn
}

# API Gateway Permission for Lambda
resource "aws_lambda_permission" "search_api" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.search.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.search.id,
      aws_api_gateway_method.search_post.id,
      aws_api_gateway_integration.search_post.id
    ]))
  }

  depends_on = [
    aws_api_gateway_method.search_post,
    aws_api_gateway_integration.search_post
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  tags = {
    Stage = var.environment
  }
}

# Lambda Package Data Sources
data "archive_file" "index_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../src/handlers"
  output_path = "${path.module}/index_lambda.zip"
}

data "archive_file" "search_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../src/handlers"
  output_path = "${path.module}/search_lambda.zip"
}
