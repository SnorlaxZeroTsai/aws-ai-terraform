output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "ec2_public_ip" {
  description = "Test EC2 public IP"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "Test EC2 instance ID"
  value       = module.ec2.public_instance_id
}
