output "queue_url" {
  description = "SQS queue URL"
  value       = try(aws_sqs_queue.this[0].id, null)
}

output "queue_arn" {
  description = "SQS queue ARN"
  value       = try(aws_sqs_queue.this[0].arn, null)
}

output "queue_name" {
  description = "SQS queue name"
  value       = try(aws_sqs_queue.this[0].name, null)
}

output "dlq_url" {
  description = "DLQ URL"
  value       = try(aws_sqs_queue.dlq[0].id, null)
}

output "dlq_arn" {
  description = "DLQ ARN"
  value       = try(aws_sqs_queue.dlq[0].arn, null)
}

output "topic_arn" {
  description = "SNS topic ARN"
  value       = try(aws_sns_topic.this[0].arn, null)
}

output "topic_name" {
  description = "SNS topic name"
  value       = try(aws_sns_topic.this[0].name, null)
}
