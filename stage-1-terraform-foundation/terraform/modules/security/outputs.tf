output "public_security_group_id" {
  description = "Public security group ID"
  value       = aws_security_group.public.id
}

output "private_security_group_id" {
  description = "Private security group ID"
  value       = aws_security_group.private.id
}
