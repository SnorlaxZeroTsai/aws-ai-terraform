# Terraform Configuration for Stage 4: RAG Knowledge Base
# This module creates a complete RAG system using OpenSearch, Bedrock, Lambda, and S3

# Retrieve Stage 1 VPC configuration
data "terraform_remote_state" "stage1" {
  backend = "local"

  config = {
    path = var.stage1_state_path
  }
}

# Shared Infrastructure - IAM and Security Group
module "shared_infrastructure" {
  source = "./modules/shared_infrastructure"

  environment = var.environment
  vpc_id      = data.terraform_remote_state.stage1.outputs.vpc_id
}

# Bedrock Module
module "bedrock" {
  source = "./modules/bedrock"

  environment        = var.environment
  embedding_model_id = var.bedrock_embedding_model
  llm_model_id       = var.bedrock_llm_model
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  environment                = var.environment
  vpc_id                     = data.terraform_remote_state.stage1.outputs.vpc_id
  private_subnet_ids         = data.terraform_remote_state.stage1.outputs.private_subnet_ids
  opensearch_domain_endpoint = module.opensearch.domain_endpoint
  documents_bucket_arn       = module.s3.bucket_arn
  bedrock_embedding_model    = var.bedrock_embedding_model
  bedrock_llm_model          = var.bedrock_llm_model
  chunk_size                 = var.chunk_size
  chunk_overlap              = var.chunk_overlap
  vector_dimension           = var.vector_dimension
  max_results                = var.max_results
  index_lambda_timeout       = var.index_lambda_timeout
  index_lambda_memory_size   = var.index_lambda_memory_size
  search_lambda_timeout      = var.search_lambda_timeout
  search_lambda_memory_size  = var.search_lambda_memory_size

  # From shared_infrastructure
  lambda_execution_role_arn     = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name    = module.shared_infrastructure.lambda_execution_role_name
  lambda_security_group_id      = module.shared_infrastructure.lambda_security_group_id
}

# CloudWatch Log Group for OpenSearch
resource "aws_cloudwatch_log_group" "opensearch" {
  name              = "/aws/opensearch/${var.opensearch_domain_name}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-opensearch-logs-${var.environment}"
    Stage = "4"
  }
}

# OpenSearch Module
module "opensearch" {
  source = "./modules/opensearch"

  domain_name             = var.opensearch_domain_name
  environment             = var.environment
  vpc_id                  = data.terraform_remote_state.stage1.outputs.vpc_id
  subnet_ids              = data.terraform_remote_state.stage1.outputs.private_subnet_ids
  instance_type           = var.opensearch_instance_type
  instance_count          = var.opensearch_instance_count
  ebs_volume_size         = var.opensearch_ebs_volume_size
  engine_version          = var.opensearch_engine_version

  # From shared_infrastructure
  lambda_security_group_id     = module.shared_infrastructure.lambda_security_group_id
  lambda_execution_role_arn    = module.shared_infrastructure.lambda_execution_role_arn
  lambda_execution_role_name   = module.shared_infrastructure.lambda_execution_role_name

  # From main.tf resource
  cloudwatch_log_arn           = aws_cloudwatch_log_group.opensearch.arn
}

# S3 Module
module "s3" {
  source = "./modules/s3"

  bucket_name             = var.documents_bucket_name
  environment             = var.environment
  index_lambda_arn        = module.lambda.index_function_arn
  index_lambda_function_name = module.lambda.index_function_name
}
