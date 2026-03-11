output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "ec2_public_ip" {
  description = "Test EC2 public IP"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "Test EC2 instance ID"
  value       = module.ec2.public_instance_id
}
