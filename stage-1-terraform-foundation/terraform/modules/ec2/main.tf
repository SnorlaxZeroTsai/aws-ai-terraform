# Get latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance in Public Subnet (for testing)
resource "aws_instance" "public_test" {
  count         = var.create_public_instance ? 1 : 0
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = var.instance_type

  subnet_id                   = var.public_subnet_ids[0]
  vpc_security_group_ids      = [var.public_security_group_id]
  iam_instance_profile        = var.instance_profile_name

  user_data = file("${path.module}/user_data.sh")

  # Enable public IP
  associate_public_ip_address = true

  # Use key pair if provided
  key_name = var.ssh_key_name

  tags = merge(
    var.tags,
    {
      Name  = "${var.name}-public-test"
      Type  = "test"
      Usage = "connectivity-testing"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}
