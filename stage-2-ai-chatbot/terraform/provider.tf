terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "./terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "AWS AI Terraform Learning Roadmap"
      Stage       = "2"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}
