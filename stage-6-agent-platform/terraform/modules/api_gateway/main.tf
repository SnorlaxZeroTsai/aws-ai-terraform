# Create REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = var.api_name
  description = "AI Agent Platform Unified API"
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.platform_name}-api"
    }
  )
}

# Create API Gateway resources
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "health"
}

resource "aws_api_gateway_resource" "agents" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "agents"
}

resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "token" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "token"
}

resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "v1"
}

resource "aws_api_gateway_resource" "chat" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "chat"
}

resource "aws_api_gateway_resource" "rag" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "rag"
}

resource "aws_api_gateway_resource" "agent" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "agent"
}

resource "aws_api_gateway_resource" "document" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "document"
}

resource "aws_api_gateway_resource" "status" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "status"
}

resource "aws_api_gateway_resource" "job_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.status.id
  path_part   = "{job_id}"
}

# Create Lambda authorizer if using JWT
resource "aws_api_gateway_authorizer" "jwt" {
  count         = var.auth_type == "jwt" ? 1 : 0
  name          = "${var.platform_name}-jwt-authorizer"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  type          = "REQUEST"
  authorizer_uri = var.authorizer_lambda_invoke_arn

  identity_sources = ["method.request.header.Authorization"]

  authorizer_credentials = var.authorizer_role_arn
}

# Create Lambda permissions
resource "aws_lambda_permission" "api_gateway" {
  count         = length(var.lambda_integrations)
  statement_id  = "AllowAPIGatewayInvoke-${element(var.lambda_integrations, count.index).function_name}"
  action        = "lambda:InvokeFunction"
  function_name = element(var.lambda_integrations, count.index).function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# Create VPC Link for ECS integration
resource "aws_api_gateway_vpc_link" "ecs" {
  name        = "${var.platform_name}-ecs-link"
  description = "VPC Link for ECS Orchestrator"
  target_arns = var.load_balancer_arns

  tags = local.common_tags
}

# Create methods and integrations
# Health check - no auth
resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "health_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "GET"

  uri = "${var.orchestrator_url}/health"
}

resource "aws_api_gateway_method_response" "health_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "health_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.health.id
  http_method = aws_api_gateway_method.health_get.http_method
  status_code = aws_api_gateway_method_response.health_200.status_code

  depends_on = [
    aws_api_gateway_integration.health_get
  ]
}

# List agents - with auth
resource "aws_api_gateway_method" "agents_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.agents.id
  http_method   = "GET"
  authorization = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : "NONE"
}

resource "aws_api_gateway_integration" "agents_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.agents.id
  http_method = aws_api_gateway_method.agents_get.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "GET"

  uri = "${var.orchestrator_url}/agents"
}

# Chat endpoint - with auth
resource "aws_api_gateway_method" "chat_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.chat.id
  http_method   = "POST"
  authorization = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : "NONE"
}

resource "aws_api_gateway_integration" "chat_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.chat.id
  http_method = aws_api_gateway_method.chat_post.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "POST"

  uri = "${var.orchestrator_url}/v1/chat"

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/json'"
  }
}

# RAG endpoint - with auth
resource "aws_api_gateway_method" "rag_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.rag.id
  http_method   = "POST"
  authorization = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : "NONE"
}

resource "aws_api_gateway_integration" "rag_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.rag.id
  http_method = aws_api_gateway_method.rag_post.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "POST"

  uri = "${var.orchestrator_url}/v1/rag"
}

# Autonomous agent endpoint - with auth
resource "aws_api_gateway_method" "agent_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.agent.id
  http_method   = "POST"
  authorization = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : "NONE"
}

resource "aws_api_gateway_integration" "agent_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.agent.id
  http_method = aws_api_gateway_method.agent_post.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "POST"

  uri = "${var.orchestrator_url}/v1/agent"
}

# Document endpoint - with auth
resource "aws_api_gateway_method" "document_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.document.id
  http_method   = "POST"
  authorization = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : "NONE"
}

resource "aws_api_gateway_integration" "document_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.document.id
  http_method = aws_api_gateway_method.document_post.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "POST"

  uri = "${var.orchestrator_url}/v1/document"
}

# Job status endpoint - with auth
resource "aws_api_gateway_method" "status_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.job_id.id
  http_method   = "GET"
  authorization = var.auth_type == "jwt" ? aws_api_gateway_authorizer.jwt[0].id : "NONE"
}

resource "aws_api_gateway_integration" "status_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.job_id.id
  http_method = aws_api_gateway_method.status_get.http_method

  type                    = "HTTP_PROXY"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.ecs.id
  integration_http_method = "GET"

  uri = "${var.orchestrator_url}/v1/status/{job_id}"
}

# Create deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.health.id,
      aws_api_gateway_resource.agents.id,
      aws_api_gateway_resource.v1.id,
      aws_api_gateway_integration.health_get.id,
      aws_api_gateway_integration.agents_get.id,
      aws_api_gateway_integration.chat_post.id,
      aws_api_gateway_integration.rag_post.id,
      aws_api_gateway_integration.agent_post.id,
      aws_api_gateway_integration.document_post.id,
      aws_api_gateway_integration.status_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Create stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name

  # Access logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format         = jsonencode({
      requestId       = "$context.requestId"
      ip              = "$context.identity.sourceIp"
      caller          = "$context.identity.caller"
      user            = "$context.identity.user"
      requestTime     = "$context.requestTime"
      httpMethod      = "$context.httpMethod"
      resourcePath    = "$context.resourcePath"
      status          = "$context.status"
      protocol        = "$context.protocol"
      responseLength  = "$context.responseLength"
      integrationLatency = "$context.integrationLatency"
    })
  }

  # Throttling
  throttling_burst_limit = var.throttling_burst_limit
  throttling_rate_limit  = var.throttling_rate_limit

  # X-Ray tracing
  xray_tracing_enabled = var.enable_xray

  tags = merge(
    local.common_tags,
    {
      Stage = var.stage_name
    }
  )
}

# CloudWatch log group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.platform_name}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# Custom domain (optional)
resource "aws_api_gateway_domain_name" "custom" {
  count = var.domain_name != null ? 1 : 0

  domain_name              = var.domain_name
  certificate_arn          = var.certificate_arn
  regional_certificate_arn = var.certificate_arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

resource "aws_api_gateway_base_path_mapping" "custom" {
  count = var.domain_name != null ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  domain_name = aws_api_gateway_domain_name.custom[0].domain_name

  base_path = "api"
}

# API Gateway account settings for logging
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = var.cloudwatch_role_arn

  depends_on = [
    aws_api_gateway_rest_api.main
  ]
}
