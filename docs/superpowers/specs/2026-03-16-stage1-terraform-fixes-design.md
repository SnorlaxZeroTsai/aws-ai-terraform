# Stage 1 Terraform 修复设计

**日期:** 2026-03-16
**状态:** 设计阶段
**范围:** Stage 1 修复

## 前置条件与假设

**环境要求：**
- AWS CLI 已配置且凭证有效
- Terraform >= 1.0 已安装
- 无现有 Terraform 状态需要迁移
- 无正在运行的 AWS 资源需要迁移

**假设：**
- 这是个人学习/测试环境
- 用户有基本 Terraform 操作经验
- 不需要向后兼容现有部署

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

### 修复单元组织

修复工作分为 5 个独立单元，每个单元可独立验证：

#### 单元 1: 修复 outputs.tf 资源引用
- **目的:** 修复根级 outputs 中的错误资源引用
- **影响文件:** `terraform/outputs.tf`
- **优先级:** 🔴 严重（阻塞 terraform plan）
- **输入:** 模块输出值
- **输出:** 正确的 outputs 引用
- **验证:** `terraform plan` 成功执行

#### 单元 2: 修复 key_name 默认值
- **目的:** 防止空字符串导致 AWS API 错误
- **影响文件:**
  - `terraform/variables.tf`
  - `terraform/modules/ec2/variables.tf`
- **优先级:** 🟡 中等（可能导致 EC2 创建失败）
- **输入:** 无
- **输出:** 修正后的默认值 null
- **验证:** `terraform validate` 通过

#### 单元 3: 更新 AMI 为 Amazon Linux 2023
- **目的:** 使用最新支持的 AMI，避免 EOL 问题
- **影响文件:** `terraform/modules/ec2/main.tf`
- **优先级:** 🟠 低（当前仍可工作）
- **输入:** AWS AMI 查询
- **输出:** AL2023 AMI ID
- **验证:** `terraform plan` 显示正确 AMI

#### 单元 4: 添加 SSH 安全警告
- **目的:** 提醒用户默认 SSH 配置的安全风险
- **影响文件:** `terraform/variables.tf`
- **优先级:** 🔵 低（文档改进）
- **输入:** 无
- **输出:** 更新的描述文本
- **验证:** 代码审查确认警告存在

#### 单元 5: 创建 .gitignore 保护
- **目的:** 防止状态文件被提交到 git
- **影响文件:** `.gitignore`（新建或追加）
- **优先级:** 🔵 低（防护性措施）
- **输入:** 无
- **输出:** 包含 terraform 规则的 .gitignore
- **验证:** 状态文件被忽略

### 文件修改清单

| 文件 | 修改内容 | 影响单元 |
|------|----------|----------|
| `terraform/outputs.tf` | 修复资源引用 | 单元 1 |
| `terraform/variables.tf` | 添加警告，修复 key_name | 单元 2, 4 |
| `terraform/modules/ec2/main.tf` | 更新 AMI 为 AL2023 | 单元 3 |
| `terraform/modules/ec2/variables.tf` | 修复 key_name 默认值 | 单元 2 |
| `.gitignore` | 添加状态文件保护 | 单元 5 |

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

**检查文件是否存在:** 项目根目录已存在 `.gitignore`

**操作:** 在现有 `.gitignore` 文件末尾追加以下内容（如果规则不存在）：

```
# Terraform files
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
terraform.tfstate.backup
```

**验证:** 确保 `terraform.tfstate` 等文件不被 git 跟踪

## 验证计划

修复完成后按顺序执行以下验证：

### 1. 语法验证
```bash
cd stage-1-terraform-foundation/terraform
terraform validate
```
**期望输出:** `Success! The configuration is valid.`

### 2. 计划验证
```bash
terraform plan
```
**期望输出:**
- 无错误
- 显示将创建的资源列表
- AMI 显示为 al2023-ami-2023.*

### 3. 状态文件保护验证
```bash
cat .gitignore | grep -E "tfstate|terraform"
```
**期望输出:** 应包含 `*.tfstate` 等规则

### 4. 实际部署验证（可选）
```bash
terraform apply
# 等待资源创建完成
```

**部署后验证:**
```bash
# 检查 outputs
terraform output vpc_id
terraform output ec2_public_ip

# 检查 EC2 实例（如果创建）
aws ec2 describe-instances --instance-ids $(terraform output ec2_instance_id | tr -d '"')

# 验证 AMI 类型
aws ec2 describe-images --image-ids $(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].ImageId' --output text) --query 'Images[0].Name' --output text
# 期望输出包含: al2023-ami-2023
```

### 5. 清理验证（如果部署）
```bash
terraform destroy
```
**期望输出:** 资源成功删除，无残留

## Stage 2-6 检查计划

**注意:** Stage 2-6 检查是独立的后续工作，不在本规范范围内。完成本规范实施后，应创建单独的后续规范：`Stage 2-6 Terraform 一致性审查`。

**检查清单（供后续规范使用）：**

| 检查项 | Stage 2 | Stage 3 | Stage 4 | Stage 5 | Stage 6 |
|--------|---------|---------|---------|---------|---------|
| outputs.tf 引用错误 | ? | ? | ? | ? | ? |
| AMI 查询方式 | ? | ? | ? | ? | ? |
| key_name 默认值 | ? | ? | ? | ? | ? |

**后续规范应定义：**
- 检查方法（手动 vs 自动化脚本）
- 发现问题的处理流程
- 是否需要独立规范或合并修复
- 与 Stage 1 的依赖关系

## 错误场景处理

| 场景 | 处理方式 | 备注 |
|------|----------|------|
| AMI 查找失败 | terraform plan 会失败，用户需手动验证区域可用性 | 检查 AWS 区域是否有 AL2023 |
| SSH key 不存在 | terraform apply 会失败，需创建 key pair 或设为 null | AWS 控制台创建 key pair |
| 语法错误 | terraform validate 会捕获 | 修复后重新验证 |
| 状态文件损坏 | 备份当前状态，可能需要重建 | 清空状态重新 apply |

## 回滚计划

如果修复导致问题：

1. **代码回滚:** `git checkout <previous-commit>`
2. **状态回滚:** `terraform rollback` 或删除 `.tfstate` 重新开始
3. **资源清理:** 如果部分资源已创建，手动在 AWS 控制台删除或使用 `terraform destroy`

**回滚触发条件：**
- terraform apply 失败且无法修复
- 创建的资源与预期不符
- 成本异常（如创建了意外的昂贵资源）

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
