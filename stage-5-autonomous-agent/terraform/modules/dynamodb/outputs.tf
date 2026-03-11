output "conversation_table_name" {
  description = "Conversation memory table name"
  value       = aws_dynamodb_table.conversation_memory.name
}

output "episodic_table_name" {
  description = "Episodic memory table name"
  value       = aws_dynamodb_table.episodic_memory.name
}

output "semantic_table_table_name" {
  description = "Semantic memory table name"
  value       = aws_dynamodb_table.semantic_memory.name
}

output "tool_results_table_name" {
  description = "Tool results table name"
  value       = aws_dynamodb_table.tool_results.name
}
