variable "domain_name" {
  description = "Name of the OpenSearch domain"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where OpenSearch will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for OpenSearch deployment"
  type        = list(string)
}

variable "instance_type" {
  description = "Instance type for OpenSearch nodes"
  type        = string
  default     = "t3.medium.search"
}

variable "instance_count" {
  description = "Number of OpenSearch data nodes"
  type        = number
  default     = 2
}

variable "ebs_volume_size" {
  description = "Size of EBS volume for OpenSearch data nodes in GB"
  type        = number
  default     = 20
}

variable "engine_version" {
  description = "OpenSearch engine version"
  type        = string
  default     = "OpenSearch_2.11"
}

variable "lambda_security_group_id" {
  description = "Security group ID of Lambda functions (from shared_infrastructure module)"
  type        = string
}

variable "lambda_execution_role_arn" {
  description = "ARN of Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "lambda_execution_role_name" {
  description = "Name of Lambda execution role (from shared_infrastructure module)"
  type        = string
}

variable "cloudwatch_log_arn" {
  description = "ARN of CloudWatch log group for OpenSearch logs (from main.tf)"
  type        = string
}
