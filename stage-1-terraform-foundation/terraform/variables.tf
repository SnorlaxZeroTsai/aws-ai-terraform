variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnet egress"
  type        = bool
  default     = true
}

variable "ec2_instance_type" {
  description = "EC2 instance type for compute resources"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "Name of SSH key pair for EC2 instances"
  type        = string
  default     = ""
}
