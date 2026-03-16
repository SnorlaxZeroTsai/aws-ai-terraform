# Stage 1 Terraform 修复设计

**日期:** 2026-03-16
**状态:** 设计阶段
**范围:** Stage 1 修复 + Stage 2-6 检查

## 问题概述

Stage 1 Terraform 代码存在 6 个主要问题，导致无法在 AWS 上正常运行：

1. **outputs.tf 引用不存在的资源** 🔴 严重 - terraform plan/apply 会失败
2. **key_name 默认值为空字符串** 🟡 中等 - 可能导致 EC2 创建失败
3. **SSH 默认允许全网段** 🟡 中等 - 安全风险
4. **Backend 本地存储** 🟠 低 - 无法团队协作（个人环境可接受）
5. **AMI 查询不精确** 🟠 低 - 使用过时的 Amazon Linux 2
6. **缺少版本锁定** 🔵 低 - 依赖版本不确定性

## 设计约束

- **使用环境:** 个人学习/测试
- **协作需求:** 单人使用，无需团队协作
- **安全要求:** 保持 SSH 便利性，添加警告提示
- **修复原则:** 最小化改动，保持现有架构

## 修复方案：方案 A - 最小化修复

### 文件修改清单

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `terraform/outputs.tf` | 修复资源引用 | 🔴 严重 |
| `terraform/variables.tf` | 添加警告，修复 key_name | 🟡 中等 |
| `terraform/modules/ec2/main.tf` | 更新 AMI 为 AL2023 | 🟠 低 |
| `terraform/modules/ec2/variables.tf` | 修复 key_name 默认值 | 🟡 中等 |
| `.gitignore` | 添加状态文件保护 | 🔵 低 |

### 具体修改

#### 1. terraform/outputs.tf

修复模块引用错误：

```terraform
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "ec2_public_ip" {
  description = "Test EC2 public IP"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "Test EC2 instance ID"
  value       = module.ec2.public_instance_id
}
```

#### 2. terraform/variables.tf

添加安全警告并修复 key_name：

```terraform
variable "ssh_key_name" {
  description = "Name of SSH key pair for EC2 instances (null = no key pair)"
  type        = string
  default     = null
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access (default allows ANYWHERE - NOT recommended for production, use only for learning/testing)"
  type        = string
  default     = null
}
```

#### 3. terraform/modules/ec2/main.tf

更新 AMI 为 Amazon Linux 2023：

```terraform
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

resource "aws_instance" "public_test" {
  count         = var.create_public_instance ? 1 : 0
  ami           = data.aws_ami.amazon_linux_2023.id
  # ... 其余保持不变
}
```

#### 4. terraform/modules/ec2/variables.tf

```terraform
variable "ssh_key_name" {
  description = "SSH key pair name"
  type        = string
  default     = null  # 修复：从 "" 改为 null
}
```

#### 5. .gitignore

添加状态文件保护：

```
# Terraform files
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
terraform.tfstate.backup
```

## 验证计划

修复完成后执行以下验证：

```bash
# 1. 初始化 Terraform
cd stage-1-terraform-foundation/terraform
terraform init

# 2. 验证代码语法
terraform validate

# 3. 查看执行计划
terraform plan

# 4. (可选) 实际部署
terraform apply
```

## Stage 2-6 检查计划

完成 Stage 1 修复后，检查其他 Stage 是否有相同问题：

| 检查项 | Stage 2 | Stage 3 | Stage 4 | Stage 5 | Stage 6 |
|--------|---------|---------|---------|---------|---------|
| outputs.tf 引用错误 | ✓ | ✓ | ✓ | ✓ | ✓ |
| AMI 查询方式 | ✓ | ✓ | ✓ | ✓ | ✓ |
| key_name 默认值 | ✓ | ✓ | ✓ | ✓ | ✓ |

**修复策略：**
- 发现相同问题，应用相同修复模式
- 保持架构一致性

## 未修复项（有意保留）

以下项目根据"个人学习/测试"的约束有意保留：

1. **本地 Backend** - 单人使用无需远程状态管理
2. **SSH 0.0.0.0/0** - 保持便利性，添加警告提示
3. **缺少状态锁定** - 个人环境不需要

## 成功标准

修复完成后的验收标准：

1. ✅ `terraform validate` 通过无错误
2. ✅ `terraform plan` 成功生成执行计划
3. ✅ `terraform apply` 能成功创建资源
4. ✅ Stage 2-6 检查完成，发现的问题已修复
