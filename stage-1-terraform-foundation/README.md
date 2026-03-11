# Stage 1: Terraform Foundation

## Learning Objectives

By completing this stage, you will learn how to:

- Set up a professional Terraform project structure for AWS infrastructure
- Configure Terraform providers and backends
- Define and manage Terraform variables and outputs
- Implement proper Git workflow with .gitignore
- Create comprehensive infrastructure documentation
- Follow Terraform and AWS best practices
- Estimate infrastructure costs

## Prerequisites

### Tools Required
- **Terraform** (>= 1.0): [Install Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- **AWS CLI** (>= 2.0): [Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- **Git**: [Install Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- **Python** (>= 3.9): [Install Guide](https://www.python.org/downloads/)

### AWS Credentials
Configure AWS credentials before running Terraform:
```bash
aws configure
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Knowledge Assumptions
- Basic understanding of cloud computing concepts
- Familiarity with command-line interfaces
- Basic knowledge of networking (VPC, subnets, security groups)

## Architecture Overview

### Infrastructure Components

This stage creates the foundational AWS infrastructure:

```
┌─────────────────────────────────────────────────┐
│                   VPC (10.0.0.0/16)              │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │  Public Subnet (10.0.1.0/24)           │     │
│  │  - EC2 Instance (t3.micro)             │     │
│  │  - Internet Gateway                    │     │
│  │  - Public IP                           │     │
│  └────────────────────────────────────────┘     │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │  Private Subnet (10.0.2.0/24)          │     │
│  │  - EC2 Instance (t3.micro)             │     │
│  │  - NAT Gateway                         │     │
│  │  - Private IP only                     │     │
│  └────────────────────────────────────────┘     │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Security Model
- **Public Subnet**: Direct internet access via Internet Gateway
- **Private Subnet**: Outbound-only internet access via NAT Gateway
- **Network ACLs**: Default AWS rules
- **Security Groups**: Configured for minimal required access

## Design Decisions

### Terraform Configuration
- **Terraform Version**: 1.x for latest features and stability
- **AWS Provider**: 5.x for current AWS resource support
- **Backend**: Local backend for simplicity (will migrate to remote in later stages)
- **Default Tags**: All resources tagged for cost allocation and identification

### Network Design
- **VPC CIDR**: 10.0.0.0/16 (65,536 addresses) - sufficient for development
- **Public Subnet**: 10.0.1.0/24 (256 addresses) - for publicly accessible resources
- **Private Subnet**: 10.0.2.0/24 (256 addresses) - for protected resources
- **Multi-AZ**: Deployed across 2 availability zones for high availability

### Instance Sizing
- **EC2 Type**: t3.micro (1 vCPU, 1 GB RAM) - minimal cost for learning
- **SSH Access**: Key-based authentication for secure access

## Deployment Steps

### 1. Initialize Terraform
```bash
cd terraform
terraform init
```

### 2. Review Configuration
```bash
terraform plan
```

### 3. Deploy Infrastructure
```bash
terraform apply
```

### 4. Verify Deployment
```bash
terraform output
```

### 5. Access EC2 Instances
```bash
# Public instance (requires SSH key)
ssh -i /path/to/key.pem ubuntu@<public-ip>

# Private instance (requires bastion/jump host)
# Will be implemented in later stages
```

### 6. Clean Up (when done)
```bash
terraform destroy
```

## Cost Estimate

### Monthly Cost Breakdown (us-east-1)

| Resource | Quantity | Hourly Cost | Monthly Cost |
|----------|----------|-------------|--------------|
| VPC | 1 | $0.00 | $0.00 |
| Public Subnet | 1 | $0.00 | $0.00 |
| Private Subnet | 1 | $0.00 | $0.00 |
| Internet Gateway | 1 | $0.00 | $0.00 |
| NAT Gateway | 1 | $0.045 | ~$32.40 |
| EC2 t3.micro | 2 | $0.0104 | ~$15.00 |
| Data Transfer | Minimal | Variable | ~$1.00 |

**Total Estimated Monthly Cost: ~$48-50**

### Cost Optimization Tips
- Turn off NAT Gateway when not in use (saves ~$32/month)
- Use t3.micro instances for development
- Monitor costs using AWS Cost Explorer
- Set up billing alerts
- Clean up resources promptly when done learning

## Testing

### Manual Testing
```bash
# Run tests from the tests directory
cd tests
# Test scripts will be added in subsequent tasks
```

### Verification Checklist
- [ ] VPC created with correct CIDR
- [ ] Public and private subnets created
- [ ] Internet Gateway attached
- [ ] NAT Gateway created (if enabled)
- [ ] EC2 instances running
- [ ] Security groups configured
- [ ] Outputs display correct values

## Variables

### Required Variables (with defaults)
- `aws_region`: us-east-1
- `environment`: dev
- `vpc_cidr`: 10.0.0.0/16
- `availability_zones`: ["us-east-1a", "us-east-1b"]
- `enable_nat_gateway`: true
- `ec2_instance_type`: t3.micro
- `ssh_key_name`: "" (empty default)

### Customizing Variables

Create a `terraform.tfvars` file:
```hcl
aws_region          = "us-west-2"
environment         = "dev"
vpc_cidr           = "10.1.0.0/16"
availability_zones  = ["us-west-2a", "us-west-2b"]
enable_nat_gateway  = true
ec2_instance_type   = "t3.micro"
ssh_key_name        = "my-key-pair"
```

## Outputs

After deployment, the following outputs are available:
- `vpc_id`: VPC identifier
- `public_subnet_ids`: List of public subnet IDs
- `private_subnet_ids`: List of private subnet IDs
- `ec2_public_ip`: Public IP address of public EC2 instance
- `ec2_private_ip`: Private IP address of private EC2 instance

## Next Steps

### Immediate Next Steps (Stage 1)
1. Implement VPC and networking components
2. Create EC2 instances with proper security groups
3. Add SSH key management
4. Implement testing framework

### Future Stages
- **Stage 2**: Add AI model serving infrastructure
- **Stage 3**: Implement CI/CD pipeline
- **Stage 4**: Add monitoring and logging
- **Stage 5**: Implement security hardening
- **Stage 6**: Optimize for production

## Troubleshooting

### Common Issues

**Issue**: Terraform can't find AWS credentials
**Solution**: Verify AWS credentials are configured: `aws configure list`

**Issue**: EC2 instances fail to launch
**Solution**: Check SSH key exists in the region, verify instance type is available

**Issue**: NAT Gateway creation fails
**Solution**: Verify you have sufficient Elastic IP quota in your account

**Issue**: Can't connect to EC2 instance
**Solution**: Verify security group allows SSH (port 22) from your IP

## Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS VPC User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/)
- [AWS EC2 User Guide](https://docs.aws.amazon.com/ec2/latest/userguide/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

## License

This project is part of a learning journey to become a cloud AI application architect.
