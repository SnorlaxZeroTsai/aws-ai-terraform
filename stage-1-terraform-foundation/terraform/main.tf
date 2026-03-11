# Main Terraform configuration
# This file will be populated with actual resource definitions in subsequent tasks

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  name               = "stage1"
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  enable_nat_gateway = var.enable_nat_gateway

  tags = {
    Stage = "1-foundation"
  }
}

# Placeholder for EC2 instances
# Placeholder for networking components
