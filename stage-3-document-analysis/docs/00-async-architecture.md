# 事件驅動架構：為什麼需要非同步處理？

**學習目標：** 理解同步 vs 非同步處理的取捨，掌握事件驅動架構的設計

---

## 回顧：Stage 2 的限制

在 Stage 2 我們建立了同步的 AI Chatbot：
```
[用戶請求]
    ↓
[API Gateway]
    ↓
[Lambda]
    ↓
[Bedrock API]
    ↓
[立即回應用戶]
```

**問題：**
- ❌ 處理時間必須 < 30 秒（API Gateway 限制）
- ❌ 無法處理長時間任務
- ❌ 用戶必須等待

---

## 場景：文件分析的需求

### 真實場景

```
[用戶上傳 100 頁 PDF]
    ↓
[需要分析]
→ 文字提取
→ 表格識別
→ 表單解析
    ↓
[處理時間：2-5 分鐘]
```

**如果用同步處理：**
```
❌ API Gateway 30 秒超時
❌ 用戶必須等待 5 分鐘
❌ 連線可能中斷
❌ 無法取消
❌ 資源浪費（等待期間佔用連線）
```

**解決方案：非同步處理**
```
✅ 用戶上傳後立即得到回應
✅ 在背景處理
✅ 處理完成後通知用戶
✅ 用戶可以關閉瀏覽器
✅ 可以檢查進度
```

---

## 同步 vs 非同步

### 完整對比

| 特性 | 同步處理 | 非同步處理 |
|------|---------|-----------|
| **用戶體驗** | 等待中 | 立即回應 |
| **處理時間** | 秒級 | 分鐘/小時級 |
| **可靠性** | 連線中斷 = 失敗 | 持久化佇列 |
| **擴展性** | 受限 | 高 |
| **複雜度** | 簡單 | 中等 |
| **成本** | 較低 | 較高 |
| **適用場景** | 快速回應 | 長時間任務 |

### 真實類比

**同步處理 = 餐廳點餐**
```
[你點餐]
    ↓
[廚師開始煮]
    ↓
[你等待]
    ↓
[餐點好了，立即享用]

優點：簡單、快速
缺點：必須等待
```

**非同步處理 = 外帶訂餐**
```
[你電話訂餐]
    ↓
[餐廳確認訂單]
    ↓
[你去做其他事]
    ↓
[餐點好了]
    ↓
[通知你取餐]

優點：不用等、可以做其他事
缺點：需要等待通知
```

---

## 非同步架構的三種模式

### 模式 1：輪詢（Polling）

```
[用戶上傳文件]
    ↓
[系統返回 document_id]
    ↓
[用戶定期查詢狀態]
→ GET /status/{document_id}
    ↓
[處理完成後返回結果]
```

**實作範例：**
```python
# 前端
def check_document_status(document_id):
    while True:
        status = api.get(f"/status/{document_id}")

        if status['state'] == 'COMPLETED':
            return status['result']
        elif status['state'] == 'FAILED':
            raise Exception(status['error'])

        # 等待 5 秒後再查詢
        time.sleep(5)
```

**優點：**
- ✅ 簡單
- ✅ 用戶控制頻率
- ✅ 無需額外基礎設施

**缺點：**
- ❌ 浪費資源（重複查詢）
- ❌ 延遲高（平均延遲 = 輪詢間隔 / 2）
- ❌ 伺服器負擔

### 模式 2：回調（Callback/Webhook）

```
[用戶上傳文件]
    ↓
[系統返回 document_id]
    ↓
[用戶提供 webhook URL]
    ↓
[處理完成後呼叫 webhook]
    ↓
[用戶系統接收通知]
```

**實作範例：**
```python
# 上傳時提供 webhook
api.post('/upload', json={
    'file': file_data,
    'webhook_url': 'https://your-app.com/callback'
})

# 用戶的 webhook 端點
@app.route('/callback', methods=['POST'])
def handle_callback():
    data = request.json
    document_id = data['document_id']
    status = data['status']
    result = data['result']

    # 處理完成的文件
    process_completed_document(document_id, result)
```

**優點：**
- ✅ 即時通知
- ✅ 無需輪詢
- ✅ 資源效率高

**缺點：**
- ❌ 需要公開端點
- ❌ 需要處理認證
- ❌ 重試邏輯複雜

### 模式 3：發布/訂閱（Pub/Sub）- 我們的選擇

```
[用戶上傳文件]
    ↓
[系統返回 document_id]
    ↓
[用戶訂閱 SNS 主題]
    ↓
[處理完成後發布到 SNS]
    ↓
[用戶接收通知]
```

**實作範例：**
```python
# 上傳
response = api.post('/upload', json={'file': file_data})
document_id = response['document_id']
subscription_arn = response['subscription_arn']

# 接收通知（通過 SQS 或 HTTP endpoint）
def process_notification(event):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])

        if message['document_id'] == document_id:
            if message['status'] == 'COMPLETED':
                # 下載結果
                download_result(message['result_url'])
            elif message['status'] == 'FAILED':
                # 處理錯誤
                handle_error(message['error'])
```

**優點：**
- ✅ 解耦（發送者和接收者無需直接連接）
- ✅ 多個訂閱者（可以通知多個系統）
- ✅ 可靠（AWS 自動重試）
- ✅ 靈活（可以訂閱/取消訂閱）

**缺點：**
- ❌ 複雜度較高
- ❌ 需要管理訂閱

---

## AWS 非同步服務選擇

### SQS vs SNS vs EventBridge

| 特性 | SQS | SNS | EventBridge |
|------|-----|-----|-------------|
| **模式** | 佇列 | 發布/訂閱 | 事件匯流排 |
| **順序保證** | FIFO | 先進先出 | 時間順序 |
| **持久化** | 是 | 否 | 是 |
| **重試** | 內建 | DLQ | 內建 |
| **過濾** | 無 | 訂閱者過濾 | 規則引擎 |
| **成本** | $0.40/M | $0.50/M | $1.00/M |
| **最佳用途** | 任務佇列 | 通知 | 事件路由 |

### 選擇決策樹

```
你的需求是什麼？

[需要確保順序處理？]
├─ Yes → SQS FIFO
└─ No → 繼續
    [需要通知多個接收者？]
    ├─ Yes → SNS
    └─ No → 繼續
        [需要事件路由和規則？]
        ├─ Yes → EventBridge
        └─ No → SQS 標準佇列
```

---

## Stage 3 架構設計

### 完整流程

```
[用戶上傳 PDF]
    ↓
[API Gateway]
    ↓
[Lambda: 上傳處理]
    ├─ 上傳到 S3
    ├─ 建立 DynamoDB 記錄
    ├─ 發送訊息到 SQS
    └─ 返回 document_id
    ↓
[SQS 佇列]
    ↓ (觸發)
[Lambda: 文字提取]
    ├─ 呼叫 Textract
    ├─ 提取文字和表格
    └─ 更新 DynamoDB 狀態
    ↓
[處理完成]
    ↓
[SNS 發布通知]
    ↓
[用戶接收通知]
```

### 成本分析

**每月 10,000 個文件處理：**

```
S3 儲存：
→ 10K 文件 × 1MB = 10GB
→ 成本：$0.23/月

SQS 請求：
→ 10K 訊息
→ 成本：10K × $0.40 / 1M = $0.004

Lambda 執行：
→ 10K 調用 × 30 秒 × 512MB
→ 10K × (30 × 0.5 / 1024 × $0.00001667) = $2.45

Textract：
→ 10K 文件 × 10 頁
→ 100K 頁 × $1.50 / 1M = $0.15

DynamoDB：
→ 10K 寫入 + 10K 讀取
→ 20K RCUs × $0.25 / 1M = $0.005

SNS 通知：
→ 10K 通知
→ 10K × $0.50 / 1M = $0.005

總計：~$2.84/月
```

---

## 錯誤處理與重試

### SQS 內建重試

```
[Lambda 處理失敗]
    ↓
[訊息回到佇列]
    ↓ (可見性超時)
[重新嘗試]
    ↓
[最多 3 次]
    ↓
[仍失敗 → DLQ]
```

**配置：**
```hcl
resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.documents.arn
  function_name    = aws_lambda_function.process_document.function_name

  # 重試配置
  maximum_retry_attempts = 3
}
```

### 死信佇列（DLQ）

**為什麼需要 DLQ？**
```
✅ 記錄失敗的訊息
✅ 可以分析失敗原因
✅ 可以手動重新處理
✅ 防止訊息丟失
```

**實作：**
```hcl
resource "aws_sqs_queue" "dead_letter" {
  name = "documents-dead-letter"

  message_retention_seconds = 1209600  # 14 天
}

resource "aws_sqs_queue" "main" {
  name = "documents"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 3
  })
}
```

---

## 最佳實踐

### 1. 訊息大小限制

**SQS 限制：256KB**

**解決方案：**
```
[大文件]
    ↓
[上傳到 S3]
    ↓
[SQS 只包含 S3 URI]
    ↓
[Lambda 從 S3 下載處理]
```

**實作：**
```python
# 上傳
s3_key = f"documents/{document_id}.pdf"
s3.upload_file(file, Bucket=bucket, Key=s3_key)

# SQS 訊息（只包含 URI）
sqs.send_message(QueueUrl=queue_url, Message=json.dumps({
    'document_id': document_id,
    's3_bucket': bucket,
    's3_key': s3_key
}))
```

### 2. 幂等性處理

**為什麼需要幂等性？**
```
SQS 可能重複傳遞訊息
→ Lambda 可能重複處理
→ 需要確保冪等性
```

**實作：**
```python
def process_document(document_id, s3_key):
    # 檢查是否已處理
    doc = dynamodb.get_item(Key={'document_id': document_id})

    if doc.get('status') == 'COMPLETED':
        logger.info(f"Document {document_id} already processed")
        return

    # 處理文件
    result = textract.analyze_document(Document={'S3Object': {'Bucket': bucket, 'Name': s3_key}})

    # 更新狀態
    dynamodb.update_item(
        Key={'document_id': document_id},
        UpdateExpression='SET #status = :status, result = :result',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': 'COMPLETED',
            ':result': result
        }
    )
```

### 3. 監控佇列深度

**為什麼重要？**
```
佇列深度積壓
→ 處理速度 < 上傳速度
→ 需要擴展或優化
```

**告警設定：**
```hcl
resource "aws_cloudwatch_metric_alarm" "queue_depth" {
  alarm_name          = "document-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能說明同步 vs 非同步的差別嗎？
- [ ] 我知道什麼時候該用非同步處理嗎？
- [ ] 我理解輪詢、回調、發布/訂閱的差別嗎？

**技術選擇：**
- [ ] 我能比較 SQS、SNS、EventBridge 嗎？
- [ ] 我知道如何選擇合適的服務嗎？
- [ ] 我理解死信佇列的作用嗎？

**實作能力：**
- [ ] 我能設計非同步架構嗎？
- [ ] 我知道如何實作幂等性嗎？
- [ ] 我能設定佇列深度告警嗎？

---

## 下一階段

完成 Stage 3 後，你會理解：
- ✅ 事件驅動架構的設計
- ✅ 非同步處理的最佳實踐
- ✅ SQS/SNS 的使用場景
- ✅ 文字提取（Textract）的整合

**下一章：** 向量資料庫與 RAG 架構
