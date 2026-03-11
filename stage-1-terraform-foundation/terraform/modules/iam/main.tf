# Assume role policy for EC2
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# EC2 Instance Profile Role
resource "aws_iam_role" "ec2_instance" {
  name               = "${var.name}-ec2-instance-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = var.tags
}

# Policy: Allow EC2 to access SSM (for Session Manager)
data "aws_iam_policy_document" "ssm_access" {
  statement {
    effect = "Allow"

    actions = [
      "ssm:UpdateInstanceInformation",
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel",
      "ssm:GetConnectionStatus",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ssm_access" {
  name   = "${var.name}-ssm-access"
  role   = aws_iam_role.ec2_instance.id
  policy = data.aws_iam_policy_document.ssm_access.json
}

# Instance Profile
resource "aws_iam_instance_profile" "ec2_instance" {
  name = "${var.name}-ec2-instance-profile"
  role = aws_iam_role.ec2_instance.name
}
