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

# IAM Module
module "iam" {
  source = "./modules/iam"

  name = "stage1"

  tags = {
    Stage = "1-foundation"
  }
}

# Security Module
module "security" {
  source = "./modules/security"

  name   = "stage1"
  vpc_id = module.vpc.vpc_id

  ssh_allowed_cidr = var.ssh_allowed_cidr != null ? [var.ssh_allowed_cidr] : ["0.0.0.0/0"]
  app_port         = 8080

  tags = {
    Stage = "1-foundation"
  }
}

# EC2 Module
module "ec2" {
  source = "./modules/ec2"

  name                     = "stage1"
  instance_type            = var.ec2_instance_type
  public_subnet_ids        = module.vpc.public_subnet_ids
  public_security_group_id = module.security.public_security_group_id
  instance_profile_name    = module.iam.instance_profile_name
  ssh_key_name             = var.ssh_key_name

  tags = {
    Stage = "1-foundation"
  }
}

# Placeholder for networking components
