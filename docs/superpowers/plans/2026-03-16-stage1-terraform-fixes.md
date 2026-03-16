# Stage 1 Terraform Fixes Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 Stage 1 Terraform 代码中的 6 个问题，使其能够在 AWS 上正常运行

**架构:** 保持现有模块化架构不变，修复资源引用、更新 AMI、添加安全警告和保护状态文件

**技术栈:** Terraform >= 1.0, AWS Provider ~5.0, Git

---

## Chunk 1: 修复 outputs.tf 资源引用（单元 1）

### Task 1: 修复 VPC 输出引用

**Files:**
- Modify: `stage-1-terraform-foundation/terraform/outputs.tf:1-9`

- [ ] **Step 1: 修复 vpc_id 输出**

将 `aws_vpc.main.id` 修改为 `module.vpc.vpc_id`：

```terraform
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}
```

- [ ] **Step 2: 修复 public_subnet_ids 输出**

将 `aws_subnet.public[*].id` 修改为 `module.vpc.public_subnet_ids`：

```terraform
output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}
```

- [ ] **Step 3: 修复 private_subnet_ids 输出**

将 `aws_subnet.private[*].id` 修改为 `module.vpc.private_subnet_ids`：

```terraform
output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}
```

- [ ] **Step 4: 验证语法**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

预期输出: `Success! The configuration is valid.`

- [ ] **Step 5: 验证执行计划**

```bash
terraform plan
```

预期输出: 无错误，显示正确的模块输出引用

- [ ] **Step 6: 提交更改**

```bash
cd /home/zero/aws-ai-terraform
git add stage-1-terraform-foundation/terraform/outputs.tf
git commit -m "fix: correct outputs.tf to use module references instead of direct resource access"
```

---

### Task 2: 修复 EC2 输出引用

**Files:**
- Modify: `stage-1-terraform-foundation/terraform/outputs.tf:16-24`

- [ ] **Step 1: 验证 EC2 输出引用**

检查 `ec2_public_ip` 和 `ec2_instance_id` 是否已经正确使用模块引用：

```terraform
output "ec2_public_ip" {
  description = "Test EC2 public IP"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "Test EC2 instance ID"
  value       = module.ec2.public_instance_id
}
```

- [ ] **Step 2: 如果需要，修复引用**

如果上述输出不是模块引用，按 Task 1 的方式修复。

- [ ] **Step 3: 验证语法**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

- [ ] **Step 4: 提交更改（如果有）**

```bash
cd /home/zero/aws-ai-terraform
git add stage-1-terraform-foundation/terraform/outputs.tf
git commit -m "fix: correct EC2 outputs to use module references"
```

---

## Chunk 2: 修复 key_name 默认值（单元 2）

### Task 3: 修复根变量 key_name 默认值

**Files:**
- Modify: `stage-1-terraform-foundation/terraform/variables.tf:37-41`

- [ ] **Step 1: 修改 ssh_key_name 变量**

将默认值从空字符串改为 null，并更新描述：

```terraform
variable "ssh_key_name" {
  description = "Name of SSH key pair for EC2 instances (null = no key pair)"
  type        = string
  default     = null
}
```

- [ ] **Step 2: 验证语法**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

- [ ] **Step 3: 提交更改**

```bash
cd /home/zero/aws-ai-terraform
git add stage-1-terraform-foundation/terraform/variables.tf
git commit -m "fix: change ssh_key_name default from empty string to null"
```

---

### Task 4: 修复 EC2 模块 key_name 默认值

**Files:**
- Modify: `stage-1-terraform-foundation/terraform/modules/ec2/variables.tf:27-31`

- [ ] **Step 1: 修改 EC2 模块 ssh_key_name 变量**

将默认值从空字符串改为 null：

```terraform
variable "ssh_key_name" {
  description = "SSH key pair name"
  type        = string
  default     = null
}
```

- [ ] **Step 2: 验证语法**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

- [ ] **Step 3: 提交更改**

```bash
cd /home/zero/aws-ai-terraform
git add stage-1-terraform-foundation/terraform/modules/ec2/variables.tf
git commit -m "fix: change EC2 module ssh_key_name default to null"
```

---

## Chunk 3: 更新 AMI 为 Amazon Linux 2023（单元 3）

### Task 5: 更新 AMI 数据源

**Files:**
- Modify: `stage-1-terraform-foundation/terraform/modules/ec2/main.tf:1-15`

- [ ] **Step 1: 更新 data 源名称和过滤条件**

将 `amazon_linux_2` 更新为 `amazon_linux_2023`，并修改过滤条件：

```terraform
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
```

- [ ] **Step 2: 更新实例资源引用**

找到 `aws_instance.public_test` 资源，将 `ami` 字段更新为引用新的 data 源：

```terraform
resource "aws_instance" "public_test" {
  count         = var.create_public_instance ? 1 : 0
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = var.instance_type
  # ... 其余保持不变
}
```

- [ ] **Step 3: 验证语法**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

- [ ] **Step 4: 验证 AMI 查询**

```bash
terraform plan | grep -A 2 "ami"
```

预期输出: 应显示匹配 `al2023-ami-2023.*` 模式的 AMI

- [ ] **Step 5: 提交更改**

```bash
cd /home/zero/aws-ai-terraform
git add stage-1-terraform-foundation/terraform/modules/ec2/main.tf
git commit -m "feat: update AMI from Amazon Linux 2 to Amazon Linux 2023"
```

---

## Chunk 4: 添加 SSH 安全警告（单元 4）

### Task 6: 更新 SSH 变量描述

**Files:**
- Modify: `stage-1-terraform-foundation/terraform/variables.tf:43-47`

- [ ] **Step 1: 更新 ssh_allowed_cidr 变量描述**

添加安全警告到描述中：

```terraform
variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access (default allows ANYWHERE - NOT recommended for production, use only for learning/testing)"
  type        = string
  default     = null
}
```

- [ ] **Step 2: 验证描述更新**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

- [ ] **Step 3: 提交更改**

```bash
cd /home/zero/aws-ai-terraform
git add stage-1-terraform-foundation/terraform/variables.tf
git commit -m "docs: add security warning to ssh_allowed_cidr variable description"
```

---

## Chunk 5: 创建 .gitignore 保护（单元 5）

### Task 7: 添加 Terraform 状态文件保护

**Files:**
- Modify: `.gitignore` (append)

- [ ] **Step 1: 检查 .gitignore 是否存在**

```bash
cd /home/zero/aws-ai-terraform
ls -la .gitignore
```

- [ ] **Step 2: 检查现有内容**

```bash
cat .gitignore
```

- [ ] **Step 3: 追加 Terraform 规则**

如果规则不存在，在文件末尾追加以下内容：

```bash
# Terraform files
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
terraform.tfstate.backup
```

可以使用命令：
```bash
cat >> .gitignore << 'EOF'

# Terraform files
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
terraform.tfstate.backup
EOF
```

或使用编辑器手动添加。

- [ ] **Step 4: 验证 .gitignore**

```bash
git status
```

预期输出: 不应显示 `.terraform/` 或 `*.tfstate` 文件为未跟踪

- [ ] **Step 5: 提交更改**

```bash
cd /home/zero/aws-ai-terraform
git add .gitignore
git commit -m "chore: add Terraform state files to .gitignore"
```

---

## Chunk 6: 最终验证

### Task 8: 完整验证测试

**Files:**
- Test: All modified files

- [ ] **Step 1: 完整语法验证**

```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```

预期输出: `Success! The configuration is valid.`

- [ ] **Step 2: 完整执行计划**

```bash
terraform plan -out=tfplan
```

预期输出:
- 无错误
- 显示所有将创建的资源
- AMI 显示为 al2023-ami-2023.*
- Outputs 显示正确的模块引用

- [ ] **Step 3: 检查所有单元的修复**

验证以下修复是否在 plan 输出中正确反映：
1. ✅ VPC 和子网输出使用模块引用
2. ✅ key_name 默认为 null
3. ✅ AMI 为 Amazon Linux 2023
4. ✅ SSH 警告在描述中（通过查看代码）

- [ ] **Step 4: (可选) 实际部署测试**

如果 AWS 凭证已配置且希望在 AWS 上测试：

```bash
terraform apply tfplan
```

部署后验证：
```bash
# 检查 outputs
terraform output vpc_id
terraform output ec2_public_ip

# 检查 EC2 实例
INSTANCE_ID=$(terraform output ec2_instance_id | tr -d '"')
aws ec2 describe-instances --instance-ids $INSTANCE_ID

# 验证 AMI 名称
IMAGE_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].ImageId' --output text)
aws ec2 describe-images --image-ids $IMAGE_ID --query 'Images[0].Name' --output text
# 预期: 包含 al2023-ami-2023
```

- [ ] **Step 5: (可选) 清理测试资源**

```bash
terraform destroy
```

- [ ] **Step 6: 最终提交（如果有额外调整）**

```bash
cd /home/zero/aws-ai-terraform
git add .
git commit -m "chore: final adjustments after validation"
```

---

## 验证清单

完成所有任务后，验证以下清单：

- [ ] `terraform validate` 通过无错误
- [ ] `terraform plan` 成功生成执行计划
- [ ] 所有 5 个修复单元独立验证通过
- [ ] `.gitignore` 防止状态文件被跟踪
- [ ] 代码已提交到 git

## 下一步

完成本计划后：
1. 创建 `Stage 2-6 Terraform 一致性审查` 规范
2. 使用相同的修复模式检查其他 Stage
3. 保持架构一致性
