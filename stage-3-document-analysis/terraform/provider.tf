terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "ai-learning-roadmap"
      Stage     = "3-document-analysis"
      ManagedBy = "Terraform"
    }
  }
}

# Note: Stage 1 VPC reference - will be used when Stage 1 is deployed
# data "terraform_remote_state" "foundation" {
#   backend = "local"
#   config = {
#     path = "../stage-1-terraform-foundation/terraform/terraform.tfstate"
#   }
# }
