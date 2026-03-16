# Stage 2-6 一致性指南

**版本:** 1.0
**日期:** 2026-03-16
**基于:** Stage 1 完成标准

---

## 目的

确保所有 Stage (2-6) 遵循与 Stage 1 相同的代码质量、文档标准和最佳实践。

---

## 核心原则

### 1. 代码质量标准

#### ✅ 必须遵守

| 标准 | 要求 | 检查方法 |
|------|------|----------|
| 模块引用 | outputs.tf 必须使用 `module.xxx` 引用，不直接引用资源 | 代码审查 |
| 变量默认值 | 可选参数使用 `null`，不使用空字符串 | 代码审查 |
| AMI 版本 | 使用 Amazon Linux 2023 或更新版本 | 代码审查 |
| 安全警告 | SSH/安全相关变量必须有明确警告 | 代码审查 |
| .gitignore | 每个 Stage 根目录必须有 .gitignore | 文件检查 |

#### ❌ 禁止模式

| 模式 | 原因 | 替代方案 |
|------|------|----------|
| `aws_vpc.main.id` in outputs | 资源通过模块创建 | `module.vpc.vpc_id` |
| `default = ""` | 空字符串会传递给 AWS | `default = null` |
| `amzn2-ami-*` AMI | Amazon Linux 2 已 EOL | `al2023-ami-2023.*` |
| 无 .gitignore | 状态文件可能泄露 | 添加标准 .gitignore |

---

## Stage 模板结构

### 标准目录结构

```
stage-N-<name>/
├── README.md                          # 必需：Stage 说明文档
├── terraform/
│   ├── provider.tf                    # 必需：Provider 配置
│   ├── main.tf                        # 必需：主配置
│   ├── variables.tf                   # 必需：变量定义
│   ├── outputs.tf                     # 必需：输出定义
│   ├── terraform.tfvars.example       # 必需：配置示例
│   └── modules/
│       └── <module-name>/
│           ├── main.tf
│           ├── variables.tf
│           ├── outputs.tf
│           └── README.md              # 推荐：模块文档
├── .gitignore                         # 必需：Git 忽略规则
└── docs/
    ├── design.md                      # 推荐：设计文档
    └── ARCHITECTURE.md                # 推荐：架构说明
```

### 必需文件模板

#### .gitignore（标准模板）

```gitignore
# Terraform files
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
terraform.tfstate.backup
*.tfstate.backup

# OS files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
```

#### terraform.tfvars.example（标准模板）

```hcl
# ============================================================================
# <Stage Name> Configuration Example
# ============================================================================
# Copy this file to terraform.tfvars and update with your values
# DO NOT commit terraform.tfvars to version control

# AWS Configuration
aws_region          = "us-east-1"
environment         = "dev"

# ... stage-specific variables
```

---

## 代码检查清单

### 每个 Stage 必须验证

- [ ] **outputs.tf 检查**
  - [ ] 所有输出使用 `module.xxx.output_name` 格式
  - [ ] 没有直接引用 `aws_resource.xxx.id`
  - [ ] 所有引用的模块输出存在

- [ ] **variables.tf 检查**
  - [ ] 可选参数默认值为 `null`（不是 `""`）
  - [ ] SSH/安全相关参数有安全警告
  - [ ] 变量描述清晰准确

- [ ] **main.tf 检查**
  - [ ] AMI 使用最新支持版本（AL2023+）
  - [ ] 模块源路径正确
  - [ ] 依赖关系正确配置

- [ ] **.gitignore 检查**
  - [ ] 文件存在于 Stage 根目录
  - [ ] 包含所有 Terraform 相关规则
  - [ ] 已提交到版本控制

- [ ] **文档检查**
  - [ ] README.md 已更新
  - [ ] terraform.tfvars.example 已创建
  - [ ] 必需的配置项有说明

---

## Stage 完成流程

### 1. 开发阶段

```bash
# 创建 Stage 分支
git checkout -b stage-N-<name>

# 开发代码
# ... 编写 Terraform 代码

# 本地验证
terraform init
terraform validate
terraform plan
```

### 2. 代码审查阶段

```bash
# 自我审查
- 检查 outputs.tf 引用
- 检查 variables.tf 默认值
- 检查 .gitignore 存在

# 提交代码
git add .
git commit -m "feat: stage-N-<name> implementation"
```

### 3. 验证阶段

```bash
# 运行检查清单
✓ outputs 引用检查
✓ variables 默认值检查
✓ .gitignore 检查
✓ 文档完整性检查
```

### 4. 完成阶段

```bash
# 创建完成检查清单
# 参考: docs/STAGE1_COMPLETION_CHECKLIST.md

# 合并到主分支
git checkout main
git merge stage-N-<name>

# 推送
git push origin main
```

---

## 常见问题修复

### 问题 1: outputs.tf 引用错误

**错误示例:**
```terraform
output "vpc_id" {
  value = aws_vpc.main.id  # ❌ 错误
}
```

**正确示例:**
```terraform
output "vpc_id" {
  value = module.vpc.vpc_id  # ✅ 正确
}
```

### 问题 2: 变量默认值错误

**错误示例:**
```terraform
variable "ssh_key_name" {
  default = ""  # ❌ 错误
}
```

**正确示例:**
```terraform
variable "ssh_key_name" {
  default = null  # ✅ 正确
}
```

### 问题 3: 缺少 .gitignore

**修复:**
```bash
# 在 Stage 根目录创建 .gitignore
cat > .gitignore << 'EOF'
# Terraform files
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
terraform.tfstate.backup
EOF
```

---

## 质量标准

### 代码质量指标

| 指标 | 标准 | 测量方法 |
|------|------|----------|
| 语法正确性 | 100% | `terraform validate` |
| 模块引用正确性 | 100% | 代码审查 |
| 文档完整性 | 100% | README + tfvars.example |
| 安全配置 | 100% | 警告文本 + .gitignore |

### 文档质量指标

| 文档 | 必需内容 |
|------|----------|
| README.md | 目的、架构、部署步骤、变量说明、输出说明 |
| terraform.tfvars.example | 所有变量 + 示例值 + 注释 |
| 模块 README.md | 模块目的、输入、输出、示例用法 |

---

## 工具和脚本

### 自动化检查脚本（可选）

```bash
#!/bin/bash
# stage-check.sh - 检查 Stage 是否符合标准

echo "检查 Stage 标准合规性..."

# 检查 .gitignore
if [ ! -f ".gitignore" ]; then
  echo "❌ 缺少 .gitignore"
  exit 1
fi

# 检查 terraform.tfvars.example
if [ ! -f "terraform/terraform.tfvars.example" ]; then
  echo "❌ 缺少 terraform.tfvars.example"
  exit 1
fi

# 检查错误的引用模式
if grep -r "aws_vpc\|aws_subnet\|aws_instance" terraform/outputs.tf; then
  echo "❌ outputs.tf 可能包含直接资源引用"
  exit 1
fi

# 检查空字符串默认值
if grep -r 'default = ""' terraform/variables.tf; then
  echo "⚠️  发现空字符串默认值，应该使用 null"
fi

echo "✅ Stage 检查通过"
```

---

## 参考资源

- [Stage 1 完成检查清单](STAGE1_COMPLETION_CHECKLIST.md)
- [Stage 1 设计规范](superpowers/specs/2026-03-16-stage1-terraform-fixes-design.md)
- [Terraform 最佳实践](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

---

**版本历史:**
- v1.0 (2026-03-16): 初始版本，基于 Stage 1 完成标准

**维护者:** Claude Sonnet 4.6
