# 錯誤處理模式：設計健壯的系統

**學習目標：** 理解如何在 Serverless 環境中處理錯誤，建立可靠的 AI 應用

---

## 為什麼需要錯誤處理？

### 場景：你的 AI Chatbot 上線了

**沒有錯誤處理的後果：**
```
[用戶發送訊息]
    ↓
[Lambda 呼叫 Bedrock]
    ↓
[Bedrock API 超時]
    ↓
[Lambda 丟出例外]
    ↓
[用戶收到] 500 Internal Server Error
    ↓
[問題]：
→ 用戶不知道發生什麼
→ 無法重試
→ 沒有日誌追蹤
→ 無法診斷問題
```

**有錯誤處理的情況：**
```
[用戶發送訊息]
    ↓
[Lambda 呼叫 Bedrock]
    ↓
[Bedrock API 超時]
    ↓
[Lambda 捕獲錯誤]
    ├─ 記錄詳細日誌
    ├─ 返回友善的錯誤訊息
    ├─ 提供重試指引
    └─ 發送告警給團隊
    ↓
[用戶收到] 503 Service Unavailable
{
  "error": "Service temporarily unavailable",
  "message": "The AI service is experiencing issues. Please try again.",
  "retry_after": 60
}
    ↓
[結果]
→ 用戶知道發生什麼
→ 可以重試
→ 有日誌追蹤
→ 團隊收到通知
```

---

## Serverless 環境的錯誤處理挑戰

### 1. 無狀態性

**問題：**
```
Lambda 執行環境是臨時的
→ 每次執行都是新環境
→ 無法在記憶體中保持狀態
→ 本地快取會丟失
```

**解決方案：**
```
使用外部狀態儲存：
→ DynamoDB（資料庫）
→ S3（檔案儲存）
→ ElastiCache（快取）
→ SQS（訊息佇列）
```

### 2. 自動重試

**Lambda 的重試行為：**
```
[Lambda 函數]
    ↓ 執行失敗
[AWS 自動重試]
    ↓ 第 1 次（立即）
    ↓ 第 2 次（1 分鐘後）
    ↓ 第 3 次（2 分鐘後）
    ↓
[最多 3 次]
```

**問題：**
```
❌ 某些錯誤不應該重試
   → 輸入驗證錯誤
   → 權限錯誤
   → 資源不存在

❌ 重試可能造成問題
   → 重複的資料庫寫入
   → 重複的 API 呼叫
   → 資源不一致
```

### 3. 冷啟動

**問題：**
```
[Lambda 冷啟動]
    ↓ 500ms 延遲
[API Gateway 超時]
    ↓ (29 秒)
[Lambda 執行]
    ↓
[Bedrock API 呼叫]
    ↓
[總延遲：30 秒]
    ↓
[API Gateway 超時（29 秒限制）]
```

**解決方案：**
```
1. 增加 Lambda timeout
2. 預留並發（Provisioned Concurrency）
3. 優化初始化時間
```

---

## 錯誤分類

### 可重試的錯誤（Transient Errors）

**特徵：**
```
→ 臨時性錯誤
→ 重試可能成功
→ 網路相關
```

**範例：**
```python
TRANSIENT_ERRORS = [
    "ThrottlingException",      # API 限流
    "ServiceUnavailable",       # 服務暫時不可用
    "RequestTimeout",           # 請求超時
    "TooManyRequestsException", # 請求過多
]
```

**處理策略：**
```python
import time
from botocore.exceptions import ClientError

def call_with_retry(func, max_retries=3):
    """
    指數退避重試
    """
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            error_code = e.response['Error']['Code']

            # 檢查是否可重試
            if error_code in TRANSIENT_ERRORS:
                if attempt < max_retries - 1:
                    # 指數退避：2^attempt 秒
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

            # 不可重試或重試次數用盡
            raise

    raise Exception("Max retries exceeded")
```

### 不可重試的錯誤（Permanent Errors）

**特徵：**
```
→ 永久性錯誤
→ 重試不會成功
→ 需要修復才能解決
```

**範例：**
```python
PERMANENT_ERRORS = [
    "InvalidParameterException",  # 參數錯誤
    "AccessDenied",              # 權限錯誤
    "ResourceNotFoundException",  # 資源不存在
    "ValidationException",       # 驗證錯誤
]
```

**處理策略：**
```python
def handle_permanent_error(error):
    """
    立即記錄並通知
    不要重試
    """
    logger.error("Permanent error occurred", extra={
        "error_code": error['code'],
        "error_message": error['message'],
        "requires_fix": True
    })

    # 發送告警
    send_alert(
        severity="HIGH",
        message=f"Permanent error: {error['code']}",
        details=error
    )

    # 返回友善的錯誤訊息
    return {
        "statusCode": 400,
        "body": json.dumps({
            "error": "Invalid request",
            "message": "Please check your input and try again"
        })
    }
```

---

## 完整錯誤處理架構

### 多層防禦

```
[第 1 層：輸入驗證]
    ↓ 過濾明顯錯誤
[第 2 層：業務邏輯]
    ↓ 處理請求
[第 3 層：外部 API]
    ↓ 呼叫 Bedrock
    ├─ 重試邏輯
    └─ 超時處理
[第 4 層：錯誤響應]
    ↓ 返回友善訊息
[第 5 層：日誌與告警]
    ↓ 記錄和通知
```

### 實作範例

```python
import json
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# 可重試的錯誤代碼
TRANSIENT_ERROR_CODES = [
    'ThrottlingException',
    'ServiceUnavailable',
    'RequestTimeout',
    'TooManyRequestsException'
]

def lambda_handler(event, context):
    """
    Lambda 處理函數，包含完整的錯誤處理
    """
    correlation_id = context.request_id

    try:
        # 第 1 層：輸入驗證
        validated_input = validate_input(event)
        logger.info("Input validated", extra={
            "correlation_id": correlation_id
        })

        # 第 2 層：業務邏輯
        result = process_chat_request(
            validated_input,
            correlation_id
        )

        logger.info("Request processed successfully", extra={
            "correlation_id": correlation_id,
            "result": result
        })

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except ValidationError as e:
        # 輸入驗證錯誤（不可重試）
        logger.warning("Validation failed", extra={
            "correlation_id": correlation_id,
            "error": str(e)
        })

        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Validation Error',
                'message': str(e)
            })
        }

    except BedrockError as e:
        # Bedrock API 錯誤
        if e.is_transient():
            # 可重試的錯誤
            logger.warning("Bedrock transient error", extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "retryable": True
            })

            # Lambda 會自動重試
            raise

        else:
            # 不可重試的錯誤
            logger.error("Bedrock permanent error", extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "retryable": False
            })

            send_alert_to_team(e)

            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Service Error',
                    'message': 'The AI service is experiencing issues'
                })
            }

    except Exception as e:
        # 未預期的錯誤
        logger.error("Unexpected error", extra={
            "correlation_id": correlation_id,
            "error": str(e),
            "error_type": type(e).__name__
        })

        # 發送緊急告警
        send_emergency_alert(e)

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            })
        }

def validate_input(event):
    """輸入驗證"""
    if not event.get('message'):
        raise ValidationError("message is required")

    if len(event['message']) > 10000:
        raise ValidationError("message too long (max 10000 chars)")

    return event

def process_chat_request(input_data, correlation_id):
    """處理聊天請求"""
    try:
        # 呼叫 Bedrock（含重試邏輯）
        response = call_bedrock_with_retry(
            prompt=input_data['message'],
            correlation_id=correlation_id
        )

        return {
            'message': response['text'],
            'model': 'claude-3-sonnet',
            'tokens_used': response['tokens']
        }

    except ClientError as e:
        # 轉換為自訂錯誤類型
        error_code = e.response['Error']['Code']
        if error_code in TRANSIENT_ERROR_CODES:
            raise BedrockError(str(e), transient=True)
        else:
            raise BedrockError(str(e), transient=False)

def call_bedrock_with_retry(prompt, correlation_id, max_retries=3):
    """含重試邏輯的 Bedrock 呼叫"""
    import time

    for attempt in range(max_retries):
        try:
            return bedrock_client.invoke_model(
                modelId='anthropic.claude-3-sonnet-1-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code in TRANSIENT_ERROR_CODES:
                if attempt < max_retries - 1:
                    # 指數退避
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying after {wait_time}s", extra={
                        "correlation_id": correlation_id,
                        "attempt": attempt + 1,
                        "error_code": error_code
                    })
                    time.sleep(wait_time)
                    continue

            # 重試失敗或不可重試
            raise
```

---

## Circuit Breaker 模式

### 為什麼需要 Circuit Breaker？

**問題：**
```
[Bedrock API 故障]
    ↓
[Lambda 持續重試]
    ↓
[所有請求都超時]
    ↓
[結果]
→ 浪費資源
→ 用戶等待時間長
→ 可能造成連鎖反應
```

**Circuit Breaker：**
```
正常狀態：
[Lambda] → [Bedrock] ✓

故障檢測：
[Bedrock] 連續失敗 5 次
    ↓
斷路器開啟（Open）：
[Lambda] ✗ [Bedrock]
    ↓
快速失敗（Fail Fast）：
[Lambda] → 立即返回錯誤
    ↓
半開狀態（Half-Open）：
等待 30 秒後試探
→ 成功：恢復正常
→ 失敗：繼續開啟
```

### 實作範例

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 斷路
    HALF_OPEN = "half_open"  # 試探

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # 秒
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func):
        """
        透過 Circuit Breaker 呼叫函數
        """
        if self.state == CircuitState.OPEN:
            # 檢查是否應該進入半開狀態
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Try again after {self._get_remaining_timeout()}s"
                )

        try:
            result = func()

            # 成功：重置計數器
            if self.state == CircuitState.HALF_OPEN:
                self._reset()
                logger.info("Circuit breaker reset to CLOSED state")

            return result

        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self):
        """檢查是否應該嘗試恢復"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _get_remaining_timeout(self):
        """取得剩餘超時時間"""
        if self.last_failure_time is None:
            return 0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, self.timeout - elapsed)

    def _on_failure(self):
        """處理失敗"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")

    def _reset(self):
        """重置斷路器"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

# 使用範例
bedrock_circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # 連續 5 次失敗後開啟
    timeout=30            # 30 秒後嘗試恢復
)

def call_bedrock_with_circuit_breaker(prompt):
    """使用 Circuit Breaker 呼叫 Bedrock"""
    def call_bedrock():
        return bedrock_client.invoke_model(...)

    try:
        return bedrock_circuit_breaker.call(call_bedrock)
    except CircuitBreakerOpenError as e:
        # 斷路器開啟：返回友善錯誤
        return {
            'error': 'Service temporarily unavailable',
            'message': str(e),
            'retry_after': bedrock_circuit_breaker._get_remaining_timeout()
        }
```

---

## 降級策略

### 為什麼需要降級？

**場景：**
```
主服務故障時：
→ 不是完全停止服務
→ 而是提供降級功能
→ 維持基本可用性
```

### 降級層級

**第 1 層：完全功能**
```
✅ Claude 3 Opus（最高品質）
→ 完整功能
→ 最佳品質
```

**第 2 層：功能降級**
```
⚠️ Claude 3 Sonnet（中等品質）
→ 品質稍降
→ 功能完整
→ 成本較低
```

**第 3 層：最小功能**
```
⚠️ Claude 3 Haiku（基礎品質）
→ 品質較低
→ 基本功能
→ 成本最低
```

**第 4 層：靜態回應**
```
❌ 預設回應
→ 無 AI 功能
→ 預設訊息
→ 系統維護提示
```

### 實作範例

```python
class DegradationStrategy:
    def __init__(self):
        self.models = [
            {
                'id': 'anthropic.claude-3-opus-1-20240229-v1:0',
                'priority': 1,
                'cost': 'high',
                'quality': 'best'
            },
            {
                'id': 'anthropic.claude-3-sonnet-1-20240229-v1:0',
                'priority': 2,
                'cost': 'medium',
                'quality': 'good'
            },
            {
                'id': 'anthropic.claude-3-haiku-1-20240229-v1:0',
                'priority': 3,
                'cost': 'low',
                'quality': 'basic'
            }
        ]
        self.current_model_index = 0

    def call_with_degradation(self, prompt):
        """
        嘗試使用模型，失敗時降級
        """
        for i, model in enumerate(self.models[self.current_model_index:]):
            try:
                response = bedrock_client.invoke_model(
                    modelId=model['id'],
                    body=json.dumps({'messages': [{'role': 'user', 'content': prompt}]})
                )

                # 成功：更新當前模型索引
                self.current_model_index = i

                # 記錄降級
                if i > 0:
                    logger.warning(f"Degraded to model {model['id']}")

                return {
                    'message': response['text'],
                    'model': model['id'],
                    'quality': model['quality']
                }

            except Exception as e:
                logger.warning(f"Model {model['id']} failed: {e}")
                continue

        # 所有模型都失敗：返回靜態回應
        logger.error("All models failed, returning static response")

        return {
            'message': "I apologize, but I'm currently experiencing technical difficulties. Please try again later.",
            'model': 'static',
            'quality': 'none'
        }

# 使用
degradation = DegradationStrategy()

def lambda_handler(event, context):
    try:
        return degradation.call_with_degradation(event['message'])
    except Exception as e:
        logger.error(f"All strategies failed: {e}")
        return {
            'statusCode': 503,
            'body': json.dumps({
                'error': 'Service Unavailable',
                'message': 'Please try again later'
            })
        }
```

---

## 死信佇列（Dead Letter Queue）

### 為什麼需要 DLQ？

**問題：**
```
[Lambda 持續失敗]
    ↓
[重試 3 次後仍失敗]
    ↓
[事件丟失]
    ↓
[無法恢復]
```

**解決方案：**
```
[Lambda 失敗]
    ↓
[DLQ (SQS/SNS)]
    ↓
[稍後手動處理]
```

### 實作範例

```hcl
# Terraform
resource "aws_sqs_queue" "dead_letter_queue" {
  name = "chatbot-dead-letter-queue"

  message_retention_seconds = 1209600  # 14 天
}

resource "aws_lambda_function" "chatbot" {
  # ... 其他設定

  dead_letter_config {
    target_arn = aws_sqs_queue.dead_letter_queue.arn
  }
}
```

**處理 DLQ 訊息：**
```python
def process_dlq_messages():
    """
    定期處理死信佇列的訊息
    """
    sqs = boto3.client('sqs')

    response = sqs.receive_message(
        QueueUrl=DLQ_URL,
        MaxNumberOfMessages=10
    )

    for message in response.get('Messages', []):
        try:
            # 嘗試重新處理
            event = json.loads(message['Body'])
            result = lambda_handler(event, None)

            # 成功：刪除訊息
            sqs.delete_message(
                QueueUrl=DLQ_URL,
                ReceiptHandle=message['ReceiptHandle']
            )

            logger.info(f"Successfully processed DLQ message: {message['MessageId']}")

        except Exception as e:
            logger.error(f"Failed to process DLQ message: {e}")
            # 訊息保留在佇列中
```

---

## 健康檢查

### 端點健康檢查

```python
def health_check():
    """
    檢查系統健康狀態
    """
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }

    # 檢查 Lambda
    try:
        lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        health['checks']['lambda'] = 'ok'
    except Exception as e:
        health['checks']['lambda'] = f'error: {e}'
        health['status'] = 'unhealthy'

    # 檢查 Bedrock
    try:
        bedrock_client.list_foundation_models()
        health['checks']['bedrock'] = 'ok'
    except Exception as e:
        health['checks']['bedrock'] = f'error: {e}'
        health['status'] = 'degraded'

    # 檢查 Secrets Manager
    try:
        secrets_manager.get_secret_value(SecretId=SECRET_ARN)
        health['checks']['secrets'] = 'ok'
    except Exception as e:
        health['checks']['secrets'] = f'error: {e}'
        health['status'] = 'unhealthy'

    return health
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能解釋可重試 vs 不可重試錯誤嗎？
- [ ] 我理解 Circuit Breaker 的作用嗎？
- [ ] 我知道為什麼需要降級策略嗎？

**實作能力：**
- [ ] 我能實作指數退避重試嗎？
- [ ] 我能設定 Circuit Breaker 嗎？
- [ ] 我能實作降級策略嗎？

**系統設計：**
- [ ] 我能設計多層錯誤處理嗎？
- [ ] 我知道如何使用 DLQ 嗎？
- [ ] 我能實作健康檢查嗎？

---

## 總結

完成 Stage 2 的學習後，你現在了解：

1. ✅ **為什麼需要 Serverless** - 成本、擴展、運維
2. ✅ **Lambda vs 容器 vs VM** - 計算服務選擇
3. ✅ **API Gateway 設計** - REST vs HTTP vs WebSocket
4. ✅ **Bedrock 整合** - AI 模型整合最佳實踐
5. ✅ **密鑰管理** - 安全地儲存敏感資訊
6. ✅ **監控與可觀測性** - 追蹤系統健康
7. ✅ **錯誤處理模式** - 建立可靠的系統

**準備好進入 Stage 3 了嗎？**

下一階段我們會探討：
- 文件分析系統
- 向量資料庫
- RAG（檢索增強生成）
- 更多 AI 應用架構模式
