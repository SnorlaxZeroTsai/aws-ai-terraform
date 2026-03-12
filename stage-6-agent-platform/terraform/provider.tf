terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "ai-platform-terraform-state"
    key            = "stage-6/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "ai-learning-roadmap"
      Stage     = "6-agent-platform"
      ManagedBy = "Terraform"
    }
  }
}

# Get outputs from Stage 1 (VPC Foundation)
data "terraform_remote_state" "stage1" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-1/terraform.tfstate"
    region = "us-east-1"
  }
}

# Get outputs from Stage 2 (AI Chatbot)
data "terraform_remote_state" "stage2" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-2/terraform.tfstate"
    region = "us-east-1"
  }
}

# Get outputs from Stage 3 (Document Analysis)
data "terraform_remote_state" "stage3" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-3/terraform.tfstate"
    region = "us-east-1"
  }
}

# Get outputs from Stage 4 (RAG Knowledge Base)
data "terraform_remote_state" "stage4" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-4/terraform.tfstate"
    region = "us-east-1"
  }
}

# Get outputs from Stage 5 (Autonomous Agent)
data "terraform_remote_state" "stage5" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-5/terraform.tfstate"
    region = "us-east-1"
  }
}

# Get current AWS region
data "aws_region" "current" {}

# Get current AWS account ID
data "aws_caller_identity" "current" {}
