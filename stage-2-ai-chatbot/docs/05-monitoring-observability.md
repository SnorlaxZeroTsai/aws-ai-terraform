# 監控與可觀測性：看見系統的狀態

**學習目標：** 理解如何監控 Serverless 應用，快速發現和診斷問題

---

## 為什麼需要監控？

### 場景：你的 API 上線了

**沒有監控的後果：**
```
[用戶抱怨]：「API 很慢！」
    ↓
[你]：「奇怪，我看看日誌」
    ↓
[問題]：
→ 日誌在哪裡？
→ 什麼時候開始的？
→ 影響多少用戶？
→ 是 Bedrock 的問題嗎？
→ 還是 Lambda 的問題？
    ↓
[結果]
→ 花費數小時找問題
→ 用戶流失
→ 無法量化影響
```

**有監控的情況：**
```
[CloudWatch 告警]：「Lambda 錯誤率 > 5%」
    ↓
[你檢查 Dashboard]
→ Lambda 錯誤率：12%（2 分鐘前開始）
→ 影響用戶：約 50 人
→ 問題：Bedrock API 超時
    ↓
[快速診斷和修復]
→ 5 分鐘內識別問題
→ 立即通知團隊
→ 快速修復
```

---

## 可觀測性的三個支柱

### 1. Logs（日誌）

**什麼是日誌？**
```
日誌 = 事件記錄
→ 什麼時候發生的？
→ 做了什麼？
→ 結果如何？

範例：
2024-03-16 10:30:45 [INFO] 處理請求 /chat
2024-03-16 10:30:46 [INFO] 呼叫 Bedrock API
2024-03-16 10:30:48 [INFO] 收到回應，耗時 2.3 秒
```

**日誌的重要性：**
```
✅ 除錯的第一步
✅ 審計追蹤
✅ 合規要求
✅ 效能分析
```

### 2. Metrics（指標）

**什麼是指標？**
```
指標 = 數值化的數據
→ 可視化
→ 可告警
→ 可趨勢分析

範例：
→ Lambda 調用次數：1,000/小時
→ 平均延遲：2.5 秒
→ 錯誤率：0.5%
```

**指標的重要性：**
```
✅ 系統健康檢查
✅ 容量規劃
✅ 效能監控
✅ 成本追蹤
```

### 3. Traces（追蹤）

**什麼是追蹤？**
```
追蹤 = 請求的完整路徑
→ 端對端可視化
→ 找出瓶頸
→ 跨服務診斷

範例：
[用戶請求]
  ↓ (50ms)
[API Gateway]
  ↓ (200ms)
[Lambda]
  ↓ (2000ms)
[Bedrock API]
  ↓ (50ms)
[回應用戶]

總耗時：2.3 秒
瓶頸：Bedrock API（佔 87%）
```

**追蹤的重要性：**
```
✅ 找出效能瓶頸
✅ 跨服務診斷
✅ 優化決策依據
```

---

## CloudWatch 設定

### 1. CloudWatch Logs

**自動收集 Lambda 日誌：**
```python
import logging
from aws_lambda_powertools import logger

logger = logger.get_logger()

def lambda_handler(event, context):
    logger.info("開始處理請求")

    try:
        # 你的業務邏輯
        result = process_request(event)

        logger.info("請求處理成功", extra={
            "result": result,
            "processing_time": result['duration']
        })

        return result

    except Exception as e:
        logger.error("請求處理失敗", extra={
            "error": str(e),
            "event": event
        })
        raise
```

**日誌保留：**
```hcl
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  # 開發環境：7 天
  # 生產環境：30 天或更長
}
```

**日誌成本：**
```
價格：$0.50 per GB ingested

範例：100 萬請求/月
→ 每個請求日誌：2KB
→ 總計：2GB
→ 成本：2 × $0.50 = $1/月

優化：
→ 開發環境：較低日誌級別（INFO）
→ 生產環境：ERROR 級別（除錯時開 DEBUG）
```

### 2. CloudWatch Metrics

**Lambda 自動指標：**
```
Invocations（調用次數）
→ 總調用次數
→ 成功/失敗次數

Errors（錯誤）
→ 執行錯誤次數

Duration（執行時間）
→ 平均、最小、最大執行時間

Throttles（限流）
→ 被限流的次數

IteratorAge（串流延遲）
→ 事件在 Lambda 之前等待的時間
```

**自訂指標：**
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name, value, unit='Count'):
    """發送自訂指標到 CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='Chatbot/Business',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.now()
        }]
    )

# 使用範例
put_custom_metric('UserMessages', 1)
put_custom_metric('BedrockTokens', 1500, 'Count')
put_custom_metric('ResponseTime', 2.3, 'Seconds')
```

### 3. CloudWatch Alarms

**設定告警：**
```hcl
# Lambda 錯誤率告警
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "chatbot-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.chatbot.function_name
  }
}

# Lambda 延遲告警
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "chatbot-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000"  # 10 秒
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.chatbot.function_name
  }
}
```

**告警最佳實踐：**
```
✅ 設定合理的閾值
   → 太敏感：誤報多
   → 太寬鬆：漏報問題

✅ 設定適當的評估週期
   → 短週期（1 分鐘）：快速反應
   → 長週期（15 分鐘）：減少誤報

✅ 設定多個評估期
   → 連續 2 次超過閾值才告警
   → 避免暫時性尖峰
```

### 4. CloudWatch Dashboard

**建立 Dashboard：**
```hcl
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "chatbot-metrics"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
            [".", "Errors", {"stat": "Sum"}],
            [".", "Duration", {"stat": "Average"}],
            [".", "ConcurrentExecutions", {"stat": "Average"}]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Metrics"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", {"stat": "Sum"}],
            [".", "5XXError", {"stat": "Sum"}],
            [".", "4XXError", {"stat": "Sum"}],
            [".", "Latency", {"stat": "Average"}]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Gateway Metrics"
        }
      }
    ]
  })
}
```

**Dashboard 應包含：**
```
Lambda 指標：
→ 調用次數
→ 錯誤率
→ 延遲
→ 並行執行數

API Gateway 指標：
→ 請求數
→ 4XX/5XX 錯誤
→ 延遲

Bedrock 指標：
→ Token 使用量
→ API 延遲
→ 錯誤率

成本指標：
→ 預估成本
→ 請求趨勢
```

---

## X-Ray 追蹤

### 啟用 X-Ray

**Terraform 配置：**
```hcl
# 啟用 X-Ray 追蹤
resource "aws_lambda_function" "chatbot" {
  # ... 其他設定

  tracing_config {
    mode = "Active"  # 或 "PassThrough"
  }
}

# X-Ray IAM 權限
resource "aws_iam_role_policy_attachment" "xray" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
```

**程式碼整合：**
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# 啟用 X-Ray 自動追蹤
patch_all()

def lambda_handler(event, context):
    # X-Ray 自動記錄：
    # - AWS SDK 呼叫（DynamoDB, S3, Bedrock 等）
    # - HTTP 呼叫
    # - 函數執行時間

    result = call_bedrock_api(prompt)

    return result
```

### X-Ray 提供的資訊

**服務圖：**
```
[Client]
    ↓ (50ms)
[API Gateway]
    ↓ (200ms)
[Lambda Function]
    ├─→ (50ms) [Secrets Manager]
    └─→ (2000ms) [Bedrock]
          ↓ (100ms)
        [S3 - Optional]

總耗時：2.35 秒
```

**異常偵測：**
```
X-Ray 自動標記：
→ Fault（錯誤）
→ Error（例外）
→ Throttle（限流）

範例：
→ Bedrock API 回傳 500
→ X-Ray 自動標記為 Fault
→ Dashboard 高亮顯示
```

---

## 日誌最佳實踐

### 1. 結構化日誌

**傳統日誌（難解析）：**
```python
# ❌ 不好的做法
logger.info("User john requested chat with model claude-3-sonnet and got 1500 tokens in 2.3 seconds")
```

**結構化日誌（易解析）：**
```python
# ✅ 好的做法
logger.info("Chat request completed", extra={
    "user_id": "john",
    "model": "claude-3-sonnet",
    "input_tokens": 500,
    "output_tokens": 1500,
    "duration_ms": 2300,
    "request_id": context.request_id
})
```

**好處：**
```
✅ CloudWatch Insights 可以搜尋
✅ 可以建立統計圖表
✅ 易於分析
```

### 2. 日誌級別

**使用正確的級別：**
```python
logger.debug("詳細的除錯資訊")
# → 開發時使用，生產關閉

logger.info("正常的業務流程")
# → 重要的業務事件

logger.warning("潛在問題")
# → 不影響功能但需要注意

logger.error("錯誤但可恢復")
# → 功能受影響但可繼續

logger.critical("嚴重錯誤")
# → 服務無法繼續
```

### 3. 相關 ID（Correlation ID）

**追蹤請求：**
```python
import uuid

def lambda_handler(event, context):
    # 使用 Lambda request_id 或生成新的
    correlation_id = context.request_id or str(uuid.uuid4())

    logger.info("Processing request", extra={
        "correlation_id": correlation_id
    })

    # 所有日誌都包含 correlation_id
    # → 方便追蹤完整的請求路徑

    try:
        result = process_request(event)
        logger.info("Request completed", extra={
            "correlation_id": correlation_id
        })
        return result
    except Exception as e:
        logger.error("Request failed", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })
        raise
```

---

## 監控策略

### SLA 定義

**服務層級協議：**
```
可用性：
→ 目標：99.9% (每月停機 < 43 分鐘)
→ 測量：(總時間 - 停機時間) / 總時間

延遲：
→ 目標：P95 < 5 秒
→ 測量：95% 的請求在 5 秒內完成

錯誤率：
→ 目標：< 0.1%
→ 測量：錯誤請求 / 總請求
```

### SLO 監控

**錯誤預算告警：**
```python
def calculate_error_budget():
    """
    99.9% 可用性 = 0.1% 錯誤預算

    每月秒數：30 × 24 × 60 × 60 = 2,592,000
    錯誤預算：2,592,000 × 0.001 = 2,592 秒
    """
    error_budget_seconds = 2592
    downtime_this_month = get_downtime_seconds()

    remaining_budget = error_budget_seconds - downtime_this_month

    if remaining_budget < 0:
        alert_team("SLA 違規！")

    return remaining_budget
```

### 合成監控（Synthetic Monitoring）

**主動測試：**
```python
def synthetic_check():
    """定期測試 API 健康狀態"""
    try:
        response = test_api_endpoint()

        if response['status'] != 'ok':
            alert_endpoint_down(response)

        if response['latency'] > 5000:
            alert_slow_response(response)

    except Exception as e:
        alert_endpoint_unreachable(e)

# 使用 CloudWatch Events 規則每 5 分鐘執行
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能解釋可觀測性的三個支柱嗎？
- [ ] 我知道 Logs、Metrics、Traces 的差別嗎？
- [ ] 我理解監控的重要性嗎？

**實作能力：**
- [ ] 我能設定 CloudWatch Alarms 嗎？
- [ ] 我能建立 Dashboard 嗎？
- [ ] 我能啟用 X-Ray 追蹤嗎？

**最佳實踐：**
- [ ] 我知道如何寫結構化日誌嗎？
- [ ] 我理解日誌級別的使用嗎？
- [ ] 我能設定合理的告警閾值嗎？

**監控策略：**
- [ ] 我能定義 SLA 和 SLO 嗎？
- [ ] 我知道如何追蹤錯誤預算嗎？
- [ ] 我能實作合成監控嗎？

---

## 下一章

現在你理解了監控與可觀測性。接下來我們會深入：

1. **錯誤處理模式** → 如何設計健壯的系統？
2. **效能優化** → 如何提升 Lambda 回應速度？
3. **測試策略** → 如何測試 Serverless 應用？
4. **成本監控** → 如何追蹤和控制成本？

**準備好了嗎？** 讓我們繼續探索 AI 應用的最佳實踐。
