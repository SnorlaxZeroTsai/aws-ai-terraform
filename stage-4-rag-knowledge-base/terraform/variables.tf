variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod, etc.)"
  type        = string
  default     = "dev"
}

variable "stage1_state_path" {
  description = "Path to Stage 1 terraform.tfstate file for VPC references"
  type        = string
  default     = "../../stage-1-terraform-foundation/terraform/terraform.tfstate"
}

# OpenSearch Configuration
variable "opensearch_domain_name" {
  description = "Name of the OpenSearch domain"
  type        = string
  default     = "stage4-rag"
}

variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch nodes"
  type        = string
  default     = "t3.medium.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch data nodes"
  type        = number
  default     = 2
}

variable "opensearch_ebs_volume_size" {
  description = "Size of EBS volume for OpenSearch data nodes in GB"
  type        = number
  default     = 20
}

variable "opensearch_engine_version" {
  description = "OpenSearch engine version"
  type        = string
  default     = "OpenSearch_2.11"
}

# S3 Configuration
variable "documents_bucket_name" {
  description = "Name of the S3 bucket for document storage"
  type        = string
  default     = "stage4-documents"
}

# Lambda Configuration
variable "index_lambda_memory_size" {
  description = "Memory size for index Lambda function in MB"
  type        = number
  default     = 512
}

variable "index_lambda_timeout" {
  description = "Timeout for index Lambda function in seconds"
  type        = number
  default     = 300
}

variable "search_lambda_memory_size" {
  description = "Memory size for search Lambda function in MB"
  type        = number
  default     = 256
}

variable "search_lambda_timeout" {
  description = "Timeout for search Lambda function in seconds"
  type        = number
  default     = 60
}

# Bedrock Configuration
variable "bedrock_embedding_model" {
  description = "Bedrock model ID for embeddings"
  type        = string
  default     = "amazon.titan-embed-text-v1"
}

variable "bedrock_llm_model" {
  description = "Bedrock model ID for LLM generation"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

# RAG Configuration
variable "vector_dimension" {
  description = "Dimension of the embedding vectors"
  type        = number
  default     = 1536
}

variable "chunk_size" {
  description = "Default chunk size for document splitting"
  type        = number
  default     = 1000
}

variable "chunk_overlap" {
  description = "Default chunk overlap for document splitting"
  type        = number
  default     = 200
}

variable "max_results" {
  description = "Maximum number of chunks to retrieve for RAG"
  type        = number
  default     = 5
}
