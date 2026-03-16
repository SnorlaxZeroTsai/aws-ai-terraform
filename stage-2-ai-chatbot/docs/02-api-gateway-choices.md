# API 層設計：API Gateway 的選擇

**學習目標：** 理解 API 層的設計決策，知道如何選擇合適的 API 方案

---

## 為什麼需要 API Gateway？

### 直接暴露 Lambda 的問題

```
❌ 直接暴露 Lambda URL：

[用戶]
    ↓
[Lambda Function URL]
    ↓
[問題]

問題：
1. 沒有驗證機制
2. 沒有速率限制
3. 沒有請求轉換
4. 沒有監控整合
5. 難以管理版本
6. CORS 配置複雜
```

### 使用 API Gateway 的好處

```
✅ 使用 API Gateway：

[用戶]
    ↓
[API Gateway]
    ├─ 身份驗證
    ├─ 速率限制
    ├─ 請求驗證
    ├─ 路由規則
    ├─ 版本管理
    └─ 監控整合
    ↓
[Lambda Function]

好處：
1. 統一的 API 入口
2. 內建安全功能
3. 請求/響應轉換
4. 自動擴展
5. 詳細的監控
```

---

## API Gateway 的三種類型

### 對比總覽

| 特性 | REST API | HTTP API | WebSocket API |
|------|----------|----------|---------------|
| **價格** | $3.50/M requests | $1.00/M requests | $0.25/分鐘 + $0.0025/K messages |
| **功能** | 最完整 | 基礎功能 | 實時通訊 |
| **設定** | 複雜 | 簡單 | 中等 |
| **延遲** | 較高 | 較低 | 較低 |
| **使用場景** | 複雜 API | 簡單 API | 實時通訊 |

---

### 選項 1：REST API（傳統選擇）

**AWS API Gateway v1**

```
[特點]
├─ 功能最完整
├─ 設定較複雜
├─ 價格較高
└─ 成熟穩定
```

**功能：**
```
✅ API Key 驗證
✅ AWS IAM 驗證
✅ Cognito OAuth2
✅ Lambda Authorizer
✅ 請求驗證（JSON Schema）
✅ 請求/響應轉換（VTL）
✅ 速率限制
✅ 快取設定
✅ CORS 支援
✅ 階段管理（dev, test, prod）
✅ Canary 發布
```

**成本：**
```
固定成本：
- $3.50 per million requests

資料傳輸：
- $0.09 per GB

範例：100 萬請求/月
→ $3.50 + $0.09 = $3.59/月
```

**優點：**
- ✅ 功能最完整
- ✅ 高度可客製化
- ✅ 支援複雜的整合
- ✅ 豐富的監控

**缺點：**
- ❌ 價格較高
- ❌ 設定複雜
- ❌ 延遲較高（~50-100ms）
- ❌ VTL 語法難學

**適用場景：**
```
✅ 需要複雜驗證邏輯
✅ 需要請求轉換
✅ 需要階段管理
✅ 企業級 API
❌ 簡單的 Lambda 代理
❌ 成本敏感的專案
```

---

### 選項 2：HTTP API（現代選擇）

**AWS API Gateway v2**

```
[特點]
├─ 功能精簡
├─ 設定簡單
├─ 價格較低
└─ 延遲較低
```

**功能：**
```
✅ JWT Authorizer
✅ Lambda Authorizer
✅ IAM 驗證
✅ CORS 支援
✅ 自動部署
✅ 標準 HTTP 狀態碼

❌ 不支援：
- API Key 驗證
- 請求驗證
- VTL 轉換
- 快取設定
- 階段管理
```

**成本：**
```
固定成本：
- $1.00 per million requests

資料傳輸：
- $0.09 per GB

範例：100 萬請求/月
→ $1.00 + $0.09 = $1.09/月

節省：$3.59 - $1.09 = $2.50/月（70% 節省）
```

**優點：**
- ✅ 便宜 70%
- ✅ 設定簡單
- ✅ 延遲較低（~30-50ms）
- ✅ 支援 JWT（標準）

**缺點：**
- ❌ 功能較少
- ❌ 不支援階段管理
- ❌ 不支援請求轉換
- ❌ 不支援快取

**適用場景：**
```
✅ 簡單的 Lambda 代理
✅ JWT 驗證
✅ 成本敏感
✅ 微服務架構
❌ 需要複雜驗證
❌ 需要請求轉換
```

---

### 選項 3：WebSocket API

```
[特點]
├─ 雙向通訊
├─ 實時更新
├─ 連線狀態管理
└─ 按分鐘計費
```

**功能：**
```
✅ 雙向通訊
✅ 路由訊息 ($default, $connect, $disconnect)
✅ 自動重連
✅ 廣播訊息
```

**成本：**
```
固定成本：
- $0.25 per connection minutes
- $0.0025 per thousand messages

範例：100 個連線，每個連線 30 分鐘/天
→ 100 × 30 分 × 30 天 = 90,000 分
→ 90,000 × $0.25 / 1000 = $22.5/月

訊息：100 連線 × 1000 訊息/天
→ 100 × 1000 × 30 = 3M 訊息
→ 3,000,000 × $0.0025 / 1000 = $7.5/月

總計：$30/月
```

**適用場景：**
```
✅ 聊天應用
✅ 即時通知
✅ 協作編輯
✅ 遊戲
✅ 股票報價
❌ 簡單的 HTTP API
```

---

### 選項 4：Lambda Function URL（無需 Gateway）

```
[特點]
├─ 最簡單
├─ 最便宜
├─ 無額外設定
└─ 功能有限
```

**功能：**
```
✅ 直接的 HTTPS 端點
✅ CORS 支援
✅ 無額外成本

❌ 不支援：
- 驗證（需在 Lambda 內處理）
- 速率限制（需在 Lambda 內處理）
- 請求轉換
```

**成本：**
```
Lambda 費用之外：
→ $0.00（無額外費用）

範例：100 萬請求/月
→ $0.00（無 API Gateway 費用）
```

**優點：**
- ✅ 完全免費
- ✅ 最簡單
- ✅ 延遲最低（~10-20ms）
- ✅ 適合內部服務

**缺點：**
- ❌ 沒有內建驗證
- ❌ 沒有速率限制
- ❌ 功能有限
- ❌ 需要自實作安全功能

**適用場景：**
```
✅ 內部 API
✅ 快速原型
✅ 簡單的 Webhook
✅ 開發/測試環境
❌ 生產環境（除非你知道風險）
```

---

## 完整對比

### 成本對比（100 萬請求/月）

| 方案 | 月成本 | vs 最便宜 |
|------|--------|-----------|
| **Lambda Function URL** | $0.00 | 基準 |
| **HTTP API** | $1.09 | +$1.09 |
| **REST API** | $3.59 | +$3.59 |
| **WebSocket** | $30+ | +$30+ |

### 功能對比

| 功能 | Function URL | HTTP API | REST API | WebSocket |
|------|--------------|----------|----------|-----------|
| **基本路由** | ✅ | ✅ | ✅ | ✅ |
| **JWT 驗證** | ❌ | ✅ | ✅ | ❌ |
| **Cognito** | ❌ | ✅ | ✅ | ❌ |
| **API Key** | ❌ | ❌ | ✅ | ❌ |
| **速率限制** | ❌ | ❌ | ✅ | ❌ |
| **請求驗證** | ❌ | ❌ | ✅ | ❌ |
| **VTL 轉換** | ❌ | ❌ | ✅ | ❌ |
| **快取** | ❌ | ❌ | ✅ | ❌ |
| **階段管理** | ❌ | ❌ | ✅ | ❌ |
| **雙向通訊** | ❌ | ❌ | ❌ | ✅ |
| **延遲** | 低 (~20ms) | 低 (~30ms) | 中 (~50ms) | 低 (~30ms) |

---

## 決策框架

### 決策樹

```
開始
  ↓
[需要雙向通訊？]
├─ Yes → WebSocket API
└─ No → 繼續
    [需要複雜驗證/轉換？]
    ├─ Yes → REST API
    └─ No → 繼續
        [需要標準 JWT 驗證？]
        ├─ Yes → HTTP API
        └─ No → 繼續
            [是生產環境？]
            ├─ Yes → HTTP API
            └─ No (開發/測試) → Function URL
```

### 場景導向選擇

**場景 1：簡單的 AI Chatbot API**
```
需求：
→ POST /chat
→ JWT 驗證
→ 簡單的請求/響應

推薦：HTTP API
→ 便宜
→ 簡單
→ 支援 JWT
→ 適合生產環境
```

**場景 2：企業級 API**
```
需求：
→ 複雜的驗證邏輯
→ API Key 管理
→ 請求驗證
→ 多階段部署
→ Canary 發布

推薦：REST API
→ 功能最完整
→ 企業級功能
→ 成熟穩定
```

**場景 3：即時聊天應用**
```
需求：
→ 雙向通訊
→ 實時更新
→ 連線管理

推薦：WebSocket API
→ 專為雙向通訊設計
→ 自動連線管理
→ 廣播訊息
```

**場景 4：快速原型/內部服務**
```
需求：
→ 快速部署
→ 無額外成本
→ 簡單的驗證

推薦：Lambda Function URL
→ 完全免費
→ 最簡單
→ 適合測試
```

---

## 實作範例

### HTTP API（Stage 2 選擇）

**Terraform 配置：**
```hcl
resource "aws_apigatewayv2_api" "chatbot" {
  name          = "chatbot-api"
  protocol_type = "HTTP"
  description   = "AI Chatbot API"

  tags = {
    Environment = var.environment
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.chatbot.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn

    format = jsonencode({
      requestId               = "$context.requestId"
      ip                      = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      httpMethod              = "$context.httpMethod"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      protocol                = "$context.protocol"
      responseLength          = "$context.responseLength"
    })
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id           = aws_apigatewayv2_api.chatbot.id
  integration_type = "AWS_PROXY"

  connection_type           = "INTERNET"
  description              = "Lambda integration"
  integration_method       = "POST"
  integration_uri          = aws_lambda_function.chatbot.invoke_arn

  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "chat" {
  api_id    = aws_apigatewayv2_api.chatbot.id
  route_key = "POST /chat"

  target = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}
```

**成本：**
```
100 萬請求/月 → $1.09
加上 Lambda 執行費 → 總計 ~$20/月
```

---

## 進階主題

### CORS 配置

**為什麼需要 CORS？**
```
[前端：example.com]
    ↓ 跨域請求
[API：api.example.com]

瀏覽器阻擋：
❌ CORS 錯誤

解決：
✅ API Gateway CORS 設定
```

**HTTP API CORS 配置：**
```hcl
resource "aws_apigatewayv2_api" "chatbot" {
  # ... 其他設定

  cors_configuration {
    allow_origins     = ["https://example.com"]
    allow_methods     = ["POST", "OPTIONS"]
    allow_headers     = ["Content-Type", "Authorization"]
    expose_headers    = ["Content-Type"]
    max_age           = 300
  }
}
```

### JWT Authorizer

**配置：**
```hcl
resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.chatbot.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = ["my-api-audience"]
    issuer   = "https://auth.example.com"
  }
}

resource "aws_apigatewayv2_route" "protected" {
  api_id    = aws_apigatewayv2_api.chatbot.id
  route_key = "POST /protected"

  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
}
```

### 速率限制（使用 Throttling）

**REST API 支援：**
```hcl
resource "aws_api_gateway_method_settings" "chat" {
  rest_api_id   = aws_api_gateway_rest_api.chatbot.id
  resource_path = "${aws_api_gateway_resource.chat.path}/*"
  http_method   = aws_api_gateway_method.chat.http_method

  settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
}
```

**HTTP API：需在 Lambda 內實作**
```python
import time
from functools import wraps

# 簡單的記憶體快取（生產環境應用 Redis）
rate_limit_store = {}

def rate_limit(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(event, context):
            # 從 event 取得 client IP
            client_ip = event['requestContext']['http']['sourceIp']

            now = int(time.time())
            window_start = now - window

            # 清除舊記錄
            if client_ip in rate_limit_store:
                rate_limit_store[client_ip] = [
                    t for t in rate_limit_store[client_ip]
                    if t > window_start
                ]
            else:
                rate_limit_store[client_ip] = []

            # 檢查是否超過限制
            if len(rate_limit_store[client_ip]) >= max_requests:
                return {
                    'statusCode': 429,
                    'body': json.dumps({'error': 'Rate limit exceeded'})
                }

            # 記錄此次請求
            rate_limit_store[client_ip].append(now)

            return f(event, context)
        return decorated_function
    return decorator
```

---

## 常見錯誤

### 錯誤 1：過度設計

```
❌ 簡單 API 用 REST API
→ 不需要的複雜功能
→ 付 3 倍價格
→ 設定時間長

✅ 簡單 API 用 HTTP API
→ 功能夠用
→ 價格合理
→ 設定簡單
```

### 錯誤 2：忽略 CORS

```
❌ 本地開發正常，上線 CORS 錯誤
→ 忘記設定 CORS
→ 前端無法呼叫

✅ 開發時就設定 CORS
→ 測試跨域請求
→ 生產環境正常
```

### 錯誤 3：不設定日誌

```
❌ API 問題無法追蹤
→ 沒有存取日誌
→ 除錯困難

✅ 啟用 CloudWatch 日誌
→ 記錄所有請求
→ 便於除錯
```

### 錯誤 4：忘記成本監控

```
❌ API 費用驚喜
→ 1000 萬請求
→ $35 帳單（REST API）

✅ 定期檢查使用量
→ 設定告警
→ 控制成本
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能說明 REST API vs HTTP API 的差別嗎？
- [ ] 我知道什麼時候該用 WebSocket 嗎？
- [ ] 我理解 Lambda Function URL 的限制嗎？

**成本考量：**
- [ ] 我能計算不同 API Gateway 方案的成本嗎？
- [ ] 我知道什麼情況下 Function URL 最適合嗎？
- [ ] 我能比較四種方案的價格嗎？

**實作能力：**
- [ ] 我能配置 HTTP API 的 CORS 嗎？
- [ ] 我知道如何設定 JWT Authorizer 嗎？
- [ ] 我能實作速率限制嗎？

**決策能力：**
- [ ] 我能根據需求選擇合適的 API 方案嗎？
- [ ] 我知道什麼時候該升級到 REST API 嗎？
- [ ] 我能設計 API 的演進路徑嗎？

---

## 下一章

現在你理解了 API 層的設計。接下來我們會深入：

1. **Bedrock 整合** → 如何整合 AI 模型？
2. **密鑰管理** → 如何安全地儲存 API Key？
3. **監控與可觀測性** → 如何追蹤 API 效能？
4. **錯誤處理模式** → 如何設計健壯的 API？

**準備好了嗎？** 讓我們繼續探索 AI 應用的架構。
