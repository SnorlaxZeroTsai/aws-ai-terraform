# 並行實作多階段設計文檔

**日期:** 2026-03-11
**狀態:** 已批准
**目標:** 使用 sub-agent-driven-development 技能並行實作 Stages 2-6

---

## 1. 概述

### 1.1 目標

使用多個 sub-agents 並行實作 AWS AI Terraform 學習路線圖的 Stages 2-6，同時確保：
- 各 Stage 之間的正確依賴關係
- 共享資源的有效管理
- 敏感資訊不洩漏到 GitHub
- 程式碼品質和文檔完整性

### 1.2 策略

採用 **方法 A：循序 Sub-Agent 分派**

```
Phase 1: Sub-Agent 1 (Stage 2) + Sub-Agent 2 (Stage 3)
     ↓
Phase 2: Sub-Agent 3 (Stage 4) + Sub-Agent 4 (Stage 5)
     ↓
Phase 3: 主 Agent (Stage 6)
```

---

## 2. 專案結構設計

### 2.1 目錄結構

```
aws-ai-terraform/
├── stage-1-terraform-foundation/     ✅ 已完成
├── stage-2-ai-chatbot/               🚧 Phase 1
├── stage-3-document-analysis/        🚧 Phase 1
├── stage-4-rag-knowledge-base/       🚧 Phase 2
├── stage-5-autonomous-agent/         🚧 Phase 2
├── stage-6-agent-platform/           🚧 Phase 3
├── shared-modules/                   📦 共享資源
│   ├── vpc/                          (從 Stage 1 提取)
│   ├── security/                     (從 Stage 1 提取)
│   └── monitoring/                   (新建)
└── scripts/
    ├── validate-all.sh               (跨 Stage 驗證)
    └── deploy-all.sh                 (順序部署腳本)
```

### 2.2 Git 策略

```bash
# Phase 1
git checkout -b phase-1-stages-2-3
# ... 開發 ...
git commit -m "Complete Phase 1: Stages 2-3"
git checkout main && git merge phase-1-stages-2-3

# Phase 2
git checkout -b phase-2-stages-4-5
# ... 開發 ...
git commit -m "Complete Phase 2: Stages 4-5"
git checkout main && git merge phase-2-stages-4-5

# Phase 3
git checkout -b phase-3-integration
# ... 開發 ...
git commit -m "Complete Phase 3: Platform Integration"
git checkout main && git merge phase-3-integration
```

---

## 3. Sub-Agent 工作流程

### 3.1 Phase 1 工作流程

```
主 Agent
    │
    ├─→ Sub-Agent 1 (Stage 2: AI Chatbot)
    │       ├─ 接收: stage-2-ai-chatbot 實作計劃
    │       ├─ 執行:
    │       │   ├─ 創建 terraform/ 目錄結構
    │       │   ├─ 實作 Lambda + API Gateway + Bedrock
    │       │   ├─ 編寫 Python chat handler
    │       │   ├─ 添加測試腳本
    │       │   └─ 撰寫文檔
    │       └─ 輸出: 完成的 stage-2-ai-chatbot/
    │
    └─→ Sub-Agent 2 (Stage 3: Document Analysis)
            ├─ 接收: stage-3-document-analysis 實作計劃
            ├─ 執行:
            │   ├─ 創建 terraform/ 目錄結構
            │   ├─ 實作 S3 + Textract + DynamoDB
            │   ├─ 編寫 Python 處理器
            │   ├─ 添加測試腳本
            │   └─ 撰寫文檔
            └─ 輸出: 完成的 stage-3-document-analysis/

主 Agent 等待 → 驗證 → 合併 → 啟動 Phase 2
```

### 3.2 Sub-Agent 交付物標準

```
stage-N-{name}/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/          (完備的模組)
├── src/
│   ├── handlers/         (Lambda/應用程式碼)
│   ├── services/         (業務邏輯)
│   └── utils/            (工具函數)
├── tests/
│   └── *_test.py         (測試腳本)
├── docs/
│   ├── design.md         (架構決策)
│   └── ARCHITECTURE.md   (技術細節)
├── README.md             (使用指南)
└── requirements.txt      (Python 依賴)
```

---

## 4. 資源共享和依賴管理

### 4.1 共享資源策略

```hcl
# Stage 2 和 Stage 3 引用 Stage 1 的輸出
data "terraform_remote_state" "stage1" {
  backend = "local"
  config = {
    path = "../stage-1-terraform-foundation/terraform/terraform.tfstate"
  }
}

# 使用共享的 VPC
module "vpc_resources" {
  source = "../../shared-modules/vpc"
  vpc_id         = data.terraform_remote_state.stage1.outputs.vpc_id
  public_subnets = data.terraform_remote_state.stage1.outputs.public_subnet_ids
  private_subnets = data.terraform_remote_state.stage1.outputs.private_subnet_ids
}
```

### 4.2 命名慣例

| 資源類型 | 命名格式 | 範例 |
|---------|---------|------|
| 標籤 | `stage<N>-<resource>-<purpose>` | `stage2-lambda-chat-handler` |
| Security Groups | `stage<N>-sg-<service>` | `stage2-sg-lambda` |
| IAM Roles | `stage<N>-role-<service>` | `stage2-role-lambda-execution` |
| Lambda Functions | `stage<N>-lambda-<function>` | `stage2-lambda-chat` |

### 4.3 依賴關係

| Phase | Stages | 依賴 |
|-------|--------|------|
| Phase 1 | 2, 3 | Stage 1 |
| Phase 2 | 4 | Stage 1 + Stage 2 |
| Phase 2 | 5 | Stage 1 + Stage 2 + Stage 3 |
| Phase 3 | 6 | 所有之前階段 |

---

## 5. 驗證和測試

### 5.1 Phase 完成驗證清單

```yaml
結構檢查:
  - [ ] 目錄存在且完整
  - [ ] 必要檔案存在 (README.md, design.md, ARCHITECTURE.md)

Terraform 驗證:
  - [ ] terraform fmt -check 通過
  - [ ] terraform validate 通過
  - [ ] terraform plan 無錯誤

程式碼驗證:
  - [ ] Python 語法正確
  - [ ] requirements.txt 完整
  - [ ] 無硬編碼敏感資訊

文檔驗證:
  - [ ] README.md 包含部署步驟
  - [ ] design.md 包含架構決策
  - [ ] ARCHITECTURE.md 包含技術細節
```

### 5.2 驗證腳本

```bash
# scripts/validate-phase.sh
#!/bin/bash
validate_phase() {
    local phase=$1
    shift
    local stages=($@)

    echo "=== Validating Phase $phase ==="

    for stage in "${stages[@]}"; do
        echo "Checking $stage..."
        cd "$stage/terraform" || exit 1
        terraform fmt -check
        terraform validate
        cd - > /dev/null
    done

    echo "✅ Phase $phase validation complete"
}
```

### 5.3 錯誤處理策略

```
Sub-Agent 失敗處理:
  1. Sub-Agent 返回詳細錯誤報告
  2. 主 Agent 檢查錯誤類型:
     - 語法錯誤 → 修復後重新派發
     - 設計問題 → 暫停，請求用戶指示
     - 依賴問題 → 檢查共享資源配置
  3. 記錄失敗到 memory 文件
  4. 繼續其他 Sub-Agents（不阻塞）
```

---

## 6. 安全和敏感資訊保護

### 6.1 .gitignore 配置

```gitignore
# Terraform state
*.tfstate
*.tfstate.*
*.tfbackup
.terraform.tfstate.lock.info

# Python
__pycache__/
*.py[cod]
*$py.class

# AWS credentials
*.pem
*.key
.aws/

# 環境變數檔案
.env
.env.local
terraform.tfvars
```

### 6.2 變數管理策略

```hcl
# variables.tf - 只定義變數
variable "bedrock_api_key" {
  type        = string
  description = "Bedrock API key"
  sensitive   = true
}

# terraform.tfvars.template - 範例（提交到 Git）
bedrock_api_key = "YOUR_API_KEY_HERE"

# terraform.tfvars - 實際值（不提交）
bedrock_api_key = "sk-ant-api03-..."
```

### 6.3 Secrets Manager 集成

```hcl
resource "aws_secretsmanager_secret" "bedrock_key" {
  name = "stage2-bedrock-api-key"
}

resource "aws_iam_role_policy" "secrets_access" {
  name = "secrets-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["secretsmanager:GetSecretValue"]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.bedrock_key.arn
      }
    ]
  })
}
```

### 6.4 提交前檢查

```bash
# scripts/pre-commit-check.sh
#!/bin/bash
echo "=== 檢查敏感資訊 ==="

# 檢查 .tfstate
if git diff --cached --name-only | grep -q '\.tfstate$'; then
    echo "❌ 錯誤：嘗試提交 .tfstate 檔案！"
    exit 1
fi

# 檢查 terraform.tfvars
if git diff --cached --name-only | grep -q 'terraform\.tfvars$'; then
    echo "❌ 錯誤：terraform.tfvars 不應該提交！"
    exit 1
fi

# 檢查 API keys
if git diff --cached | grep -q 'sk-ant-[a-zA-Z0-9-]\{40,\}'; then
    echo "❌ 警告：可能包含 API key！"
    exit 1
fi

echo "✅ 敏感資訊檢查通過"
```

---

## 7. Stage 依賴關係圖

```
                    Stage 1: Foundation
                    (VPC, EC2, IAM)
                            │
            ┌───────────────┴───────────────┐
            │                               │
    Stage 2: AI Chatbot            Stage 3: Document Analysis
    (Lambda + Bedrock)             (S3 + Textract)
            │                               │
            │           ┌───────────────────┘
            │           │
    Stage 4: RAG          Stage 5: Agent
    (依賴 Stage 2)          (依賴 Stages 2,3)
            │                               │
            └───────────────┬───────────────┘
                            │
                    Stage 6: Platform
                    (整合所有 Stages)
```

---

## 8. 實作順序

| Phase | Stages | Sub-Agents | 預估時間 |
|-------|--------|-----------|----------|
| 1 | 2, 3 | 2 並行 | 3-4 週 |
| 2 | 4, 5 | 2 並行 | 3-4 週 |
| 3 | 6 | 主 Agent | 4-6 週 |

---

## 9. 成功標準

- ✅ 所有 Terraform 檔案可應用
- ✅ 所有文檔完整且一致
- ✅ 無安全警告（密碼、API key 硬編碼）
- ✅ Git 可提交（無敏感資訊）
- ✅ 各 Stage 可獨立部署
- ✅ 依賴關係正確處理

---

**設計批准:** 2026-03-11
**下一步:** 使用 subagent-driven-development 技能開始 Phase 1 實作
