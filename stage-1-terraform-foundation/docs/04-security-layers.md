# 安全分層設計

**學習目標：** 理解如何設置多層防禦（Defense in Depth），保護 AI 應用免受攻擊

---

## 回顧：為什麼需要多層防禦？

在之前的章節我們學到：
- 公有子網的資源可能被攻擊
- 即使應用被攻破，資料庫仍應保護
- **防禦深度 = 多層防禦**

---

## 防禦深度的核心概念

### 單層防禦的問題

```
[攻擊者] → [單一防線] → [你的資料]
            ↑
       [這層被突破 = 全軍覆沒]
```

**現實例子：**

| 攻擊類型 | 單層防禮 | 多層防禦 |
|----------|----------|----------|
| **SQL 注入** | 成功 → 資料外洩 | WAF 過濾 + 輸入驗證 |
| **DDoS** | 成功 → 服務中斷 | 自動擴展 + CDN |
| **密碼破解** | 成功 → 系統入侵 | 速率限制 + MFA |
| **零日攻擊** | 成功 → 完全控制 | 網路隔離 + 監控 |

---

### 多層防禦的架構

```
第 0 層：邊界防護
    ↓ (過濾明顯的惡意流量)
[WAF/Shield]

第 1 層：網路防護
    ↓ (子網級規則)
[Network ACL]

第 2 層：實例防護
    ↓ (實例級規則)
[Security Group]

第 3 層：作業系統
    ↓ (主機防火牆)
[iptables/Windows Firewall]

第 4 層：應用程式
    ↓ (驗證、授權)
[Application Security]

第 5 層：資料保護
    ↓ (加密、金鑰管理)
[Encryption/KMS]

第 6 層：監控與響應
    ↓ (日誌、告警)
[CloudTrail/GuardDuty]
```

---

## 第 0 層：邊界防護

### WAF (Web Application Firewall)

**用途：** 過濾 HTTP/HTTPS 流量的惡意內容

**防護的攻擊類型：**
- SQL 注入
- 跨站腳本（XSS）
- 命令注入
- 惡意檔案上傳
- 掃描探測

**在我們 AI 應用中的實例：**

```
[惡意用戶]
    ↓ 提交請求
payload = {
  "query": "'; DROP TABLE users; --"
}
    ↓
[WAF 檢測]
⚠️ SQL Injection 攻擊
請求被阻擋

→ 後端 API 從未被攻擊
```

**設置範例：**
```hcl
resource "aws_wafv2_ip_set" "allowlist" {
  name               = "allowed-ips"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"

  addresses {
    address = "YOUR.OFFICE.IP/32"
  }
}

resource "aws_wafv2_web_acl" "ai_app" {
  name        = "ai-app-firewall"
  scope       = "REGIONAL"
  description = "Firewall for AI application"

  default_action {
    allow {}
  }

  # SQL Injection 規則
  rule {
    name     = "sql-injection-rule"
    priority = 1

    override_action {
      block {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
        excluded_rules = []
      }
    }

    visibility_config {
      sampled_requests_enabled = false
      cloudwatch_metrics_enabled = true
    }
  }
}
```

---

### AWS Shield

**用途：** DDoS 防護

**特點：**
- ✅ 自動啟用（免費）
- ✅ 自動擴展
- ✅ 保護所有 AWS 資源

**防護層級：**
```
標準版（免費）：
→ 自動吸收常見的 DDoS 攻擊
→ 無需額外配置

進階版（付費）：
→ 處理更複雜的攻擊
→ 專家支援
→ 按使用付費
```

---

## 第 1 層：網路 ACL（Network ACL）

### 什麼是 Network ACL？

**Network ACL = 子網層級的防火牆**

**特點：**
- 無狀態（不追蹤連線）
- 子網內所有資源共享
- 規則數量有限（每 ACL 20 條規則）

### ACL vs Security Group

| 特性 | Network ACL | Security Group |
|------|--------------|----------------|
| **作用範圍** | 子網層級 | 實例層級 |
| **狀態** | 無狀態 | 有狀態 |
| **規則數** | 最多 20 條 | 無限制 |
| **評估順序** | 編號順序 | 優先順序 |
| **拒絕行為** | 丟棄封包 | 不回應 |

### 設計範例

**公有子網 ACL：**
```hcl
resource "aws_network_acl" "public" {
  vpc_id = aws_vpc.this.id
  subnet_ids = aws_subnet.public[*].id

  egress {
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
    protocol    = "-1"
  }

  ingress {
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
    protocol    = "tcp"
  }

  ingress {
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
    protocol    = "tcp"
  }

  tags = {
    Name = "public-subnet-acl"
  }
}
```

**私有子網 ACL：**
```hcl
resource "aws_network_acl" "private" {
  vpc_id = aws_vpc.this.id
  subnet_ids = aws_subnet.private[*].id

  # 允許來自公有子網的流量
  ingress {
    rule_no    = 100
    action     = "allow"
    cidr_block = "10.0.0.0/16"  # VPC CIDR
    from_port  = 0
    to_port    = 0
    protocol    = "-1"
  }

  egress {
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
    protocol    = "-1"
  }

  tags = {
    Name = "private-subnet-acl"
  }
}
```

---

## 第 2 層：Security Group（安全群組）

### Security Group 的作用

**有狀態防火牆：**
```
Security Group 記住連線狀態：

[A] (10.0.1.5) ←→ [B] (10.0.3.10)
    ↓ (連線已建立)
[A] 可傳送資料給 [B]

[C] (攻擊者) ←→ [B] (10.0.3.10)
    ↓ (沒有連線記錄)
[C] 的請求被拒絕
```

### 公有子網 Security Group

```hcl
resource "aws_security_group" "public_sg" {
  name        = "public-sg"
  description = "Security group for public-facing resources"
  vpc_id      = aws_vpc.this.id

  # HTTPS 來自任何人
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP (可選：重定向到 HTTPS)
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH 只從辦公室 IP
  ingress {
    description = "SSH from office only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidr != null ? [var.ssh_allowed_cidr] : ["0.0.0.0/0"]
  }

  # 所有出站流量
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}
```

### 私有應用子網 Security Group

```hcl
resource "aws_security_group" "private_app_sg" {
  name        = "private-app-sg"
  description = "Security group for application servers in private subnet"
  vpc_id      = aws_vpc.this.id

  # 應用端口，只接受來自公有子網的連線
  ingress {
    description = "Application port from public subnet"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    security_groups = [aws_security_group.public_sg.id]
  }

  # 只能跟同一層的其他應用通訊
  ingress {
    description = "Inter-application communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # HTTPS 出站（呼叫 AI API）
  egress {
    description = "HTTPS outbound only"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}
```

### 私有資料子網 Security Group

```hcl
resource "aws_security_group" "private_db_sg" {
  name        = "private-db-sg"
  description = "Security group for databases in private subnet"
  vpc_id      = aws_vpc.this.id

  # MySQL 只接受來自應用層的連線
  ingress {
    description = "MySQL from application layer"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    security_groups = [aws_security_group.private_app_sg.id]
  }

  # 所有出站流量（如果需要）
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}
```

---

## 第 3 層：作業系統層

### 主機防火牆

**AWS Linux 2 / Ubuntu:**

```bash
# 使用 iptables 或 firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

**實作建議：**
- 通常不需要（Security Group 夠用）
- 除非有特殊需求
- 增加複雜度，需謹慎

---

## 第 4 層：應用程式安全

### 身份驗證與授權

```
[用戶]
    ↓ (身份驗證)
[Cognito/OAuth2]
    ↓ (存取 Token)
[API Gateway]
    ↓ (驗證 Token)
[Lambda]
    ↓ (授權檢查)
[資源]
```

**實作範例：**
```python
import jwt
from functools import wraps

def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        try:
            payload = jwt.decode(token, SECRET_KEY)
            # 驗證用戶身份
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401

        return f(*args, **kwargs)
    return decorated_function

@app.route("/api/analyze")
@authenticate
def analyze():
    # 只有通過驗證的用戶才能執行
    pass
```

---

### 輸入驗證

```python
from pydantic import BaseModel, validator
from typing import List

class AnalyzeRequest(BaseModel):
    text: str
    model: str = "claude-3-5-sonnet-20240229"

    @validator('text')
    def validate_length(cls, v):
        if len(v) > 10000:
            raise ValueError('Text too long (max 10000 chars)')
        if len(v) < 10:
            raise ValueError('Text too short (min 10 chars)')
        return v

    @validator('model')
    def validate_model(cls, v):
        allowed = ['claude-3-5-sonnet-20240229', 'gpt-4']
        if v not in allowed:
            raise ValueError(f'Model must be one of {allowed}')
        return v
```

---

## 第 5 層：資料保護

### 加密

**靜態資料加密（S3、EBS）：**
```
[應用] → [敏感資料]
    ↓ (加密前)
[KMS Key]
    ↓ (加密儲存)
[S3/EBS]

好處：
✓ 即使儲存被入侵，資料也是加密的
✓ 符合合規要求（GDPR, HIPAA）
✓ KMS 管理金鑰
```

**實作範例：**
```hcl
resource "aws_kms_key" "encryption" {
  description             = "S3 encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "s3-encryption-key"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-ai-app-data"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default
      sse_algorithm = "AES256"
      kms_key_id = aws_kms_key.encryption.arn
    }
  }
}
```

---

### 金鑰管理

**Secrets Manager：**
```
[AWS Secrets Manager]
    ├─ OpenAI API Key
    ├─ Database Password
    └─ OAuth Tokens

好處：
✓ 自動輪換金鑰
✓ 審計金鑰使用
✓ 集中管理
```

**實作範例：**
```hcl
resource "aws_secretsmanager_secret" "openai_api_key" {
  name = "prod/openai-api-key"

  secret_string = var.openai_api_key

  rotation_rules {
    automatically_after_days = 30
  }

  tags = {
    Environment = "prod"
  }
}
```

---

## 第 6 層：監控與響應

### CloudTrail（API 呼叫記錄）

```
記錄所有 AWS API 呼叫：
→ 誰建立了哪個 EC2？
→ 誰刪除了哪個資料庫？
→ 誰修改了哪個 Security Group？

用途：
✓ 安全審計
✓ 合規要求
✓ 事件調查
```

### CloudWatch（監控日誌）

```
監控指標：
→ CPU 使用率
→ 記憶體使用量
→ 網路流量
→ 應用日誌

告警：
→ CPU > 80%
→ 錯誤率 > 1%
→ 延遲 > 500ms
```

### GuardDuty（威脅檢測）

```
自動發現：
→ 異常登入
→ 可疑 API 使用
→ 潛在漏洞
→ 加密貨幣挖礦
```

---

## 完整的安全架構範例

### AI 應用的多層防禦

```
[惡意用戶]
    ↓
[第 0 層：AWS Shield] ← 自動 DDoS 防護
    ↓
[第 1 層：WAF] ← SQL Injection、XSS 過濾
    ↓
[第 2 層：Network ACL] ← 子網級規則
    ↓
[第 3 層：Security Group] ← 實例級規則
    ↓
[第 4 層：應用層驗證] ← JWT、OAuth2
    ↓
[第 5 層：輸入驗證] ← Pydantic、參數檢查
    ↓
[第 6 層：加密] ← S3、KMS
    ↓
[第 7 層：監控] ← CloudWatch、GuardDuty
```

---

## 安全層級的選擇

### 簡單應用（開發）

```
最小層級：
[Security Group]
    ↓
[應用驗證]

→ 適合學習和小型專案
```

### 企業應用（生產）

```
完整層級：
[WAF] → [SG] → [應用驗證] → [加密] → [監控]
→ 必要的安全標準
```

---

## 常見錯誤

### 錯誤 1：過度依賴單層防護

```
❌ 只用 Security Group
→ 如果規則被誤設，全線暴露
→ 單點故障

✅ 多層防禦
→ 每層獨立保護
→ 一層失效不致命
```

### 錯誤 2：忽略監控

```
❌ 沒有監控
→ 攻擊發生了才知道
→ 無法及時響應

✅ 完整監控
→ CloudWatch 日誌
→ 設定告警
→ 主動發現問題
```

### 錯誤 3：過度複雜

```
❌ 太多層級
→ 管理負擔大
→ 延遲增加
→ 成本高

✅ 適度防禦
→ 根據風險選擇
→ 平衡安全與效能
```

---

## 檢核問題

**在繼續之前，請問自己：**

**防禦概念：**
- [ ] 我能解釋為什麼要多層防禦嗎？
- [ ] 我理解防禦深度的概念嗎？
- [ ] 我知道每層的作用是什麼嗎？

**實作技能：**
- [ ] 我能設置 WAF 嗎？
- [ ] 我能設定 Security Group 規則嗎？
- [ ] 我能實作應用層驗證嗎？

**安全意識：**
- [ ] 我知道常見的攻擊類型嗎？
- [ ] 我能評估不同安全措施的效益嗎？
- [ ] 我能平衡安全和效能嗎？

**實際應用：**
- [ ] 我能設計多層安全架構嗎？
- [ ] 我能根據需求選擇適當的防禦層級嗎？
- [ ] 我知道監控和響應的重要性嗎？

---

## 下一章

現在我們有了完整的安全策略。接下來我們會深入：

1. **成本優化策略** → 如何降低整體成本？
2. **替代架構方案** → 還有哪些設計選擇？
3. **完整實作指南** → 如何將這些安全措施實際應用？

**準備好了嗎？** 讓我們繼續完善網路基礎架構的設計。
