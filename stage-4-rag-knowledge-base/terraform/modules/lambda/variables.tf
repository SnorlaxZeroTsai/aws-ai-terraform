variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  type        = string
}

variable "documents_bucket_arn" {
  description = "ARN of the documents S3 bucket"
  type        = string
}

variable "bedrock_embedding_model" {
  description = "Bedrock model ID for embeddings"
  type        = string
}

variable "bedrock_llm_model" {
  description = "Bedrock model ID for LLM"
  type        = string
}

variable "chunk_size" {
  description = "Default chunk size"
  type        = number
  default     = 1000
}

variable "chunk_overlap" {
  description = "Default chunk overlap"
  type        = number
  default     = 200
}

variable "vector_dimension" {
  description = "Dimension of embedding vectors"
  type        = number
  default     = 1536
}

variable "max_results" {
  description = "Maximum number of chunks to retrieve"
  type        = number
  default     = 5
}

variable "index_lambda_timeout" {
  description = "Timeout for index Lambda in seconds"
  type        = number
  default     = 300
}

variable "index_lambda_memory_size" {
  description = "Memory size for index Lambda in MB"
  type        = number
  default     = 512
}

variable "search_lambda_timeout" {
  description = "Timeout for search Lambda in seconds"
  type        = number
  default     = 60
}

variable "search_lambda_memory_size" {
  description = "Memory size for search Lambda in MB"
  type        = number
  default     = 256
}

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "lambda_execution_role_name" {
  description = "Name of the Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "lambda_security_group_id" {
  description = "Security group ID for Lambda functions (from shared_infrastructure module)"
  type        = string
}
