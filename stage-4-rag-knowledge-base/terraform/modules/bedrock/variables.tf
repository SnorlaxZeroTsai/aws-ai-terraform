variable "environment" {
  description = "Environment name"
  type        = string
}

variable "embedding_model_id" {
  description = "Bedrock model ID for embeddings"
  type        = string
  default     = "amazon.titan-embed-text-v1"
}

variable "llm_model_id" {
  description = "Bedrock model ID for LLM generation"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}
