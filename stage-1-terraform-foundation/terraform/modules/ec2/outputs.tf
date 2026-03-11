output "public_instance_id" {
  description = "Public EC2 instance ID"
  value       = try(aws_instance.public_test[0].id, null)
}

output "public_ip" {
  description = "Public IP address"
  value       = try(aws_instance.public_test[0].public_ip, null)
}

output "private_ip" {
  description = "Private IP address"
  value       = try(aws_instance.public_test[0].private_ip, null)
}
