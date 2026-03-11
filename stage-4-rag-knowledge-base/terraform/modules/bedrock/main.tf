# Bedrock Model Access
# Note: This module doesn't create resources but ensures models are enabled
# Actual model access is enabled through AWS Console or AWS CLI

# Data source to check if Bedrock is available
data "aws_bedrock_foundation_model" "titan_embeddings" {
  model_id = var.embedding_model_id
}

data "aws_bedrock_foundation_model" "claude" {
  model_id = var.llm_model_id
}

# CloudWatch Log Group for Bedrock Logging
resource "aws_cloudwatch_log_group" "bedrock" {
  name              = "/aws/bedrock/${var.environment}"
  retention_in_days = 7

  tags = {
    Name  = "stage4-bedrock-logs-${var.environment}"
    Stage = "4"
  }
}

# Output for models enabled
locals {
  models_enabled = {
    embedding = data.aws_bedrock_foundation_model.titan_embeddings.model_id
    llm       = data.aws_bedrock_foundation_model.claude.model_id
  }
}
