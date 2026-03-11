output "embedding_model_id" {
  description = "Bedrock embedding model ID"
  value       = data.aws_bedrock_foundation_model.titan_embeddings.model_id
}

output "llm_model_id" {
  description = "Bedrock LLM model ID"
  value       = data.aws_bedrock_foundation_model.claude.model_id
}

output "models_enabled" {
  description = "Map of enabled Bedrock models"
  value       = local.models_enabled
}

output "embedding_model_arn" {
  description = "Bedrock embedding model ARN"
  value       = data.aws_bedrock_foundation_model.titan_embeddings.arn
}

output "llm_model_arn" {
  description = "Bedrock LLM model ARN"
  value       = data.aws_bedrock_foundation_model.claude.arn
}
