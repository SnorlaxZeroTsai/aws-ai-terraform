# 密鑰管理：安全地儲存敏感資訊

**學習目標：** 理解如何安全地管理 API Key、密碼等敏感資訊，避免安全漏洞

---

## 為什麼需要密鑰管理？

### 場景：你在程式碼中硬編碼 API Key

**錯誤示範�：**
```python
# ❌ 絕對不要這樣做
API_KEY = "sk-ant-api03-abc123def456..."

def call_bedrock():
    boto3.client(
        service_name='bedrock-runtime',
        aws_access_key_id=API_KEY,  # 暴露在程式碼中
        region_name='us-east-1'
    )
```

**問題：**
```
1. 程式碼上傳到 GitHub
   → API Key 暴露給全世界
   → 任何人都可以使用你的帳戶
   → 可能造成數千美元的損失

2. 程式碼被分享
   → 團隊成員都能看到
   → 難以撤銷
   → 無法追蹤誰在使用

3. 程式碼被竊取
   → 黑客獲得存取權
   → 資料外洩
   → 系統被破壞
```

**真實案例：**
```
2023 年：
→ 某開發者在 GitHub 上意外洩露 AWS Key
→ 2 小時內被掃描到
→ 黑客部署挖礦程式
→ $5,000 的帳單

解決：
→ 立即撤銷 Key
→ 聯繫 AWS 支援
→ 爭議退費
→ 耗費數天處理
```

---

## 密鑰管理的三種方案

### 對比總覽

| 方案 | 安全性 | 成本 | 管理負擔 | 輪換 | 適用場景 |
|------|--------|------|----------|------|----------|
| **環境變數** | 低 | $0 | 低 | 手動 | 開發/測試 |
| **Parameter Store** | 中 | 低 | 中 | 手動 | 小型專案 |
| **Secrets Manager** | 高 | 中 | 低 | 自動 | 生產環境 |

---

### 方案 1：環境變數（最簡單，最不安全）

**實作：**
```bash
# .env 檔案（不要提交到 Git）
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-1-20240229-v1:0
API_KEY=sk-ant-api03-...
```

```python
# Python 程式碼
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')
```

**優點：**
- ✅ 最簡單
- ✅ 免費
- ✅ 適合本地開發

**缺點：**
- ❌ 不安全（可能在日誌中暴露）
- ❌ 無法自動輪換
- ❌ 無法追蹤存取
- ❌ 容易意外提交到 Git

**最佳實踐：**
```bash
# .gitignore
.env
.env.local
.env.*.local

# 提交範例檔案
cp .env .env.example
# 手動移除敏感資訊
git add .env.example
```

---

### 方案 2：Parameter Store（中間選擇）

**什麼是 Parameter Store？**
```
[AWS Systems Manager Manager]
    ↓
[Parameter Store]
    ├─ String (純文字)
    ├─ SecureString (加密)
    └─ StringList (清單)

特點：
→ 免費（標準參數）
→ KMS 加密（進階參數）
→ 版本控制
→ IAM 整合
```

**成本：**
```
標準參數：
→ 免費
→ 無限制數量
→ 適合：設定值、配置

進階參數（加密）：
→ $0.05 per 10,000 API calls
→ 適合：密碼、API Key
```

**實作範例：**
```hcl
# Terraform
resource "aws_ssm_parameter" "bedrock_model_id" {
  name  = "/chatbot/bedrock/model-id"
  type  = "String"
  value = "anthropic.claude-3-sonnet-1-20240229-v1:0"

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "api_key" {
  name        = "/chatbot/api/key"
  type        = "SecureString"
  value       = var.api_key
  key_id      = aws_kms_key.secrets.arn

  tags = {
    Environment = var.environment
  }
}
```

```python
# Python 程式碼
import boto3

ssm = boto3.client('ssm')

def get_parameter(name):
    response = ssm.get_parameter(
        Name=name,
        WithDecryption=True
    )
    return response['Parameter']['Value']

model_id = get_parameter('/chatbot/bedrock/model-id')
api_key = get_parameter('/chatbot/api/key')
```

**優點：**
- ✅ 免費（標準參數）
- ✅ 版本控制
- ✅ IAM 整合
- ✅ 簡單易用

**缺點：**
- ❌ 無自動輪換
- ❌ 進階參數要付費
- ❌ 無法設定輪換計劃

**適用場景：**
```
✅ 設定值（不需要輪換）
✅ 開發/測試環境
✅ 小型專案
❌ 生產環境的密碼（應該用 Secrets Manager）
```

---

### 方案 3：Secrets Manager（我們的選擇）

**什麼是 Secrets Manager？**
```
[AWS Secrets Manager]
    ├─ 專門為密鑰設計
    ├─ 自動輪換
    ├─ 精細的 IAM 權限
    └─ 審計日誌

特點：
→ 自動輪換密鑰
→ 無縫整合 RDS、Redshift 等
→ 強制加密
→ 詳細的審計日誌
```

**成本：**
```
固定成本：
→ $0.40 per secret per month

變動成本：
→ $0.05 per 10,000 API calls

範例：10 個 secrets
→ 固定：10 × $0.40 = $4/月
→ API 呼叫：100K calls = $0.50
→ 總計：~$4.50/月
```

**實作範例：**
```hcl
# Terraform
resource "aws_secretsmanager_secret" "bedrock_credentials" {
  name = "chatbot/bedrock-credentials"

  description = "Bedrock API credentials for chatbot"

  tags = {
    Environment = var.environment
    Application = "chatbot"
  }
}

resource "aws_secretsmanager_secret_version" "bedrock_credentials" {
  secret_id = aws_secretsmanager_secret.bedrock_credentials.id
  secret_string = jsonencode({
    model_id    = "anthropic.claude-3-sonnet-1-20240229-v1:0"
    api_key     = var.bedrock_api_key
    region      = var.aws_region
  })
}

# 自動輪換（選用）
resource "aws_secretsmanager_secret_rotation" "bedrock_credentials" {
  secret_id           = aws_secretsmanager_secret.bedrock_credentials.id
  rotation_lambda_arn = aws_lambda_function.rotation.arn

  rotation_rules {
    automatically_after_days = 30
  }
}
```

```python
# Python 程式碼
import boto3
import json

secrets_manager = boto3.client('secretsmanager')

def get_secret(secret_name):
    try:
        response = secrets_manager.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e

    if 'SecretString' in response:
        return json.loads(response['SecretString'])
    else:
        return response['SecretBinary']

# 使用
secrets = get_secret('chatbot/bedrock-credentials')
model_id = secrets['model_id']
api_key = secrets['api_key']
```

**優點：**
- ✅ 自動輪換
- ✅ 專為密鑰設計
- ✅ 無縫整合 AWS 服務
- ✅ 詳細的審計日誌
- ✅ 強制加密

**缺點：**
- ❌ 要付費（$0.40/secret/月）
- ❌ 可能過度工程（對小型專案）

**適用場景：**
```
✅ 生產環境
✅ 需要自動輪換
✅ 需要審計日誌
✅ 企業級應用
```

---

## 自動輪換

### 為什麼需要自動輪換？

**手動輪換的問題：**
```
1. 容易忘記
   → 「下次一定會換」
   → 結果從來沒換過

2. 中斷服務
   → 換 Key 時必須重啟服務
   → 造成停機

3. 容易出錯
   → 更新步驟複雜
   → 可能配置錯誤
```

**自動輪換的好處：**
```
✅ 定期自動更換
✅ 無需停機
✅ 無需人工介入
✅ 減少風險
```

### 輪換策略

**策略 1：立即輪換**
```
舊 Secret → 立即失效
新 Secret → 立即生效

優點：
✅ 舊 Key 立即無效

缺點：
❌ 可能中斷服務
❌ 需要所有應用立即更新
```

**策略 2：雙 Secret 輪換**
```
時間軸：
T-30 天：建立新 Secret（待命）
T-0：    應用開始使用新 Secret
T+30 天：刪除舊 Secret

優點：
✅ 無服務中斷
✅ 有時間回滾

缺點：
❌ 需要支援兩個 Secret
```

**策略 3：階段輪換（推薦）**
```
1. 建立新 Secret（SecretNew）
2. 測試應用可以使用 SecretNew
3. 切換應用到 SecretNew
4. 等待一段時間（確保正常）
5. 刪除舊 Secret（SecretOld）

AWS Secrets Manager 自動支援
```

### 實作自動輪換

**Lambda 輪換函數：**
```python
import json
import boto3
import secrets

def lambda_handler(event, context):
    secret_name = event['SecretId']
    step = event['Step']

    if step == 'createSecret':
        # 1. 建立新密碼
        new_password = generate_password()

        # 2. 暫時儲存（還不切換）
        secret = get_secret(secret_name)
        secret['pending_password'] = new_password
        put_secret(secret_name, secret)

    elif step == 'setSecret':
        # 3. 更新外部服務的密碼
        secret = get_secret(secret_name)
        update_external_service_password(
            username=secret['username'],
            new_password=secret['pending_password']
        )

    elif step == 'testSecret':
        # 4. 測試新密碼是否有效
        secret = get_secret(secret_name)
        test_login(
            username=secret['username'],
            password=secret['pending_password']
        )

    elif step == 'finishSecret':
        # 5. 完成輪換
        secret = get_secret(secret_name)
        secret['password'] = secret['pending_password']
        del secret['pending_password']
        put_secret(secret_name, secret)

def generate_password(length=32):
    """產生安全密碼"""
    return secrets.token_urlsafe(length)
```

---

## IAM 權限管理

### 最小權限原則

**錯誤示範�：**
```hcl
# ❌ 給予過多權限
resource "aws_iam_role_policy_attachment" "lambda_secrets" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
```

**正確示範：**
```hcl
# ✅ 只給予必要的權限
resource "aws_iam_role_policy" "lambda_secrets" {
  name = "secrets-manager-access"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:chatbot/*"
      }
    ]
  })
}
```

### 權限分層

**開發環境：**
```hcl
# 可以讀取和寫入（方便開發）
actions = [
  "secretsmanager:GetSecretValue",
  "secretsmanager:PutSecretValue",
  "secretsmanager:DescribeSecret"
]
```

**生產環境：**
```hcl
# 只能讀取（保護生產）
actions = [
  "secretsmanager:GetSecretValue",
  "secretsmanager:DescribeSecret"
]
```

---

## 審計與監控

### CloudTrail 整合

**自動記錄：**
```
[誰存取了 Secret]
→ 時間戳記
→ 用戶身份
→ 存取的 Secret
→ 結果（成功/失敗）
→ IP 位址
```

**啟用日誌：**
```hcl
resource "aws_cloudtrail" "secrets_audit" {
  name                          = "secrets-manager-audit"
  s3_bucket_name                = aws_s3_bucket.audit_logs.bucket
  include_global_service_events  = false

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::SecretsManager::Secret"
      values = ["arn:aws:secretsmanager:*:*:secret:*"]
    }
  }
}
```

### 存取異常檢測

**設定告警：**
```python
# 檢測異常存取模式
def detect_anomalous_access(secret_arn):
    """
    異常情況：
    1. 短時間內大量存取
    2. 不平常的時間（凌晨 3 點）
    3. 不尋常的 IP
    4. 失敗嘗試增加
    """
    # 取得存取日誌
    logs = get_access_logs(secret_arn)

    # 分析
    if has_unusual_pattern(logs):
        send_alert(
            subject="異常 Secret 存取",
            details=logs
        )
```

---

## 最佳實踐檢核清單

### 開發階段

- [ ] 永遠不要把敏感資訊提交到 Git
- [ ] 使用 .gitignore 排除 .env 檔案
- [ ] 使用環境變數進行本地開發
- [ ] 為生產環境使用 Parameter Store 或 Secrets Manager

### 部署階段

- [ ] 使用 IAM 角色（不要在程式碼中包含憑證）
- [ ] 遵循最小權限原則
- [ ] 為不同環境使用不同的 Secrets
- [ ] 啟用 CloudTrail 審計

### 運行階段

- [ ] 設定自動輪換（生產環境）
- [ ] 定期審查存取權限
- [ ] 監控異常存取
- [ ] 測試災難恢復（Secret 刪除後的重建）

---

## 常見錯誤

### 錯誤 1：在日誌中印出 Secret

```python
# ❌ 錯誤
logger.info(f"Using API key: {api_key}")

# ✅ 正確
logger.info("Using API key: ****-****-****-1234")
```

### 錯誤 2：共享 Secret

```
❌ 所有服務用同一個 Secret
→ 難以追蹤洩露源
→ 撤銷影響所有服務

✅ 每個服務獨立 Secret
→ 精細控制
→ 容易撤銷
```

### 錯誤 3：不輪換

```
❌ 從不更換 Secret
→ 風險累積
→ 洩露影響更大

✅ 定期輪換（30-90 天）
→ 降低風險
→ 符合合規
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能說明為什麼需要密鑰管理嗎？
- [ ] 我知道三種方案的差別嗎？
- [ ] 我理解自動輪換的重要性嗎？

**實作能力：**
- [ ] 我能使用 Secrets Manager 嗎？
- [ ] 我知道如何設定 IAM 權限嗎？
- [ ] 我能實作自動輪換嗎？

**安全意識：**
- [ ] 我知道最小權限原則嗎？
- [ ] 我能避免在日誌中洩露 Secret 嗎？
- [ ] 我知道如何審計 Secret 存取嗎？

---

## 下一章

現在你理解了密鑰管理。接下來我們會深入：

1. **監控與可觀測性** → 如何追蹤 Lambda 效能？
2. **錯誤處理模式** → 如何設計健壯的系統？
3. **效能優化** → 如何提升 Lambda 回應速度？
4. **測試策略** → 如何測試 Serverless 應用？

**準備好了嗎？** 讓我們繼續探索 AI 應用的最佳實踐。
