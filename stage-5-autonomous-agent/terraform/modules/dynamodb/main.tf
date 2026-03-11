# DynamoDB Module for Memory Storage

# Conversation Memory Table
resource "aws_dynamodb_table" "conversation_memory" {
  name             = "${var.project_name}-conversation-memory-${var.environment}"
  billing_mode     = var.read_capacity == -1 ? "PAY_PER_REQUEST" : "PROVISIONED"
  read_capacity    = var.read_capacity == -1 ? null : var.read_capacity
  write_capacity   = var.write_capacity == -1 ? null : var.write_capacity
  hash_key         = "session_id"
  range_key        = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "ttl"
    type = "N"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}

# Episodic Memory Table
resource "aws_dynamodb_table" "episodic_memory" {
  name             = "${var.project_name}-episodic-memory-${var.environment}"
  billing_mode     = var.read_capacity == -1 ? "PAY_PER_REQUEST" : "PROVISIONED"
  read_capacity    = var.read_capacity == -1 ? null : var.read_capacity
  write_capacity   = var.write_capacity == -1 ? null : var.write_capacity
  hash_key         = "episode_id"
  range_key        = "timestamp"

  attribute {
    name = "episode_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "ttl"
    type = "N"
  }

  global_secondary_index {
    name            = "session-index"
    hash_key        = "session_id"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}

# Semantic Memory Table
resource "aws_dynamodb_table" "semantic_memory" {
  name             = "${var.project_name}-semantic-memory-${var.environment}"
  billing_mode     = var.read_capacity == -1 ? "PAY_PER_REQUEST" : "PROVISIONED"
  read_capacity    = var.read_capacity == -1 ? null : var.read_capacity
  write_capacity   = var.write_capacity == -1 ? null : var.write_capacity
  hash_key         = "memory_id"

  attribute {
    name = "memory_id"
    type = "S"
  }

  attribute {
    name = "concept"
    type = "S"
  }

  global_secondary_index {
    name            = "concept-index"
    hash_key        = "concept"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}

# Tool Results Table
resource "aws_dynamodb_table" "tool_results" {
  name             = "${var.project_name}-tool-results-${var.environment}"
  billing_mode     = var.read_capacity == -1 ? "PAY_PER_REQUEST" : "PROVISIONED"
  read_capacity    = var.read_capacity == -1 ? null : var.read_capacity
  write_capacity   = var.write_capacity == -1 ? null : var.write_capacity
  hash_key         = "execution_id"
  range_key        = "timestamp"

  attribute {
    name = "execution_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "tool_name"
    type = "S"
  }

  global_secondary_index {
    name            = "tool-index"
    hash_key        = "tool_name"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = var.tags
}
