# Security Group for OpenSearch
resource "aws_security_group" "opensearch" {
  name        = "stage4-opensearch-${var.environment}"
  description = "Security group for OpenSearch domain"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTPS from VPC"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [var.lambda_security_group_id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "stage4-opensearch-${var.environment}"
    Stage   = "4"
    Purpose = "opensearch-domain"
  }
}

# OpenSearch Domain
resource "aws_opensearch_domain" "main" {
  domain_name    = var.domain_name
  engine_version = var.engine_version

  cluster_config {
    instance_type           = var.instance_type
    instance_count          = var.instance_count
    dedicated_master_enabled = false
    zone_awareness_enabled  = var.instance_count > 1
  }

  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.opensearch.id]
  }

  ebs_options {
    ebs_enabled {
      volume_size = var.ebs_volume_size
      volume_type = "gp2"
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "es:*"
        Effect    = "Allow"
        Principal = { AWS = var.lambda_execution_role_arn }
        Resource  = "${var.domain_arn}/*"
      }
    ]
  })

  encryption_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https = true
    tls_version   = "TLS_1.2"
  }

  advanced_security_options {
    enabled                        = false
    internal_user_database_enabled = false
  }

  log_publishing_options {
    cloudwatch_log_log_arn     = var.cloudwatch_log_arn
    log_type                   = "ES_APPLICATION_LOGS"
    enabled                    = true
  }

  tags = {
    Name        = "${var.domain_name}-${var.environment}"
    Stage       = "4"
    Environment = var.environment
    Purpose     = "rag-vector-store"
  }

  depends_on = [aws_cloudwatch_log_group.opensearch]
}

# CloudWatch Log Group for OpenSearch
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/${var.domain_name}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-opensearch-logs-${var.environment}"
    Stage = "4"
  }
}

# IAM Role for Lambda to Access OpenSearch
resource "aws_iam_role_policy_attachment" "lambda_opensearch_access" {
  role       = var.lambda_execution_role_name
  policy_arn = aws_iam_policy.opensearch_access.arn
}

resource "aws_iam_policy" "opensearch_access" {
  name        = "stage4-opensearch-access-${var.environment}"
  description = "Policy for Lambda to access OpenSearch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "es:ESHttpDelete",
          "es:ESHttpGet",
          "es:ESHttpHead",
          "es:ESHttpPost",
          "es:ESHttpPut"
        ]
        Resource = "${aws_opensearch_domain.main.arn}/*"
      }
    ]
  })
}
