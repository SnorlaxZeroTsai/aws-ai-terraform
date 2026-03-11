# Public Security Group
resource "aws_security_group" "public" {
  name_prefix = "${var.name}-public-"
  description = "Security group for public-facing resources"
  vpc_id      = var.vpc_id

  # SSH from allowed CIDR
  ingress {
    description = "SSH from allowed CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidr
  }

  # HTTP from anywhere
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS from anywhere
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# Private Security Group
resource "aws_security_group" "private" {
  name_prefix = "${var.name}-private-"
  description = "Security group for private resources"
  vpc_id      = var.vpc_id

  # SSH from public security group only
  ingress {
    description     = "SSH from public security group"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.public.id]
  }

  # Application port from self (internal communication)
  ingress {
    description = "Application port from self"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    self        = true
  }

  # HTTPS outbound only
  egress {
    description = "HTTPS outbound only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}
