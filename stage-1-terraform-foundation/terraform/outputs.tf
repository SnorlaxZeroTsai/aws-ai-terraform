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
  description = "Public IP of the EC2 instance in public subnet"
  value       = aws_instance.public_instance.public_ip
}

output "ec2_private_ip" {
  description = "Private IP of the EC2 instance in private subnet"
  value       = aws_instance.private_instance.private_ip
}
