# AI 模型整合：Bedrock 的選擇

**學習目標：** 理解如何整合 AI 模型，知道不同模型的取捨和最佳實踐

---

## 為什麼選擇 AWS Bedrock？

### 場景：你的 AI 應用需要 LLM

```
選項 A：直接呼叫 OpenAI API
[你的應用]
    ↓ HTTPS
[OpenAI API]
    ↓ 優點
✅ 最強模型
✅ 簡單整合

    ↓ 缺點
❌ 廠商鎖定
❌ 資料出境（可能違反合規）
❌ 單一故障點
❌ 成本不透明
```

```
選項 B：自託管開源模型
[你的應用]
    ↓
[自己管理的 GPU 實例]
    ↓ 優點
✅ 完全控制
✅ 資料不出境
✅ 可選模型

    ↓ 缺點
❌ 需要運維團隊
❌ 初始成本高（GPU $500/月）
❌ 需要模型優化
❌ 升級維護
```

```
選項 C：AWS Bedrock（我們選擇）
[你的應用]
    ↓
[AWS Bedrock]
    ├─ Claude (Anthropic)
    ├─ Llama (Meta)
    ├─ Mistral
    └─ Jurassic (AI21)

優點：
✅ 多個供應商選擇
✅ 資料留在 AWS
✅ 無需管理基礎設施
✅ 企業級 SLA
✅ 按使用付費
```

---

## Bedrock 的重要概念

### 什麼是 Bedrock？

**Bedrock = 完全託管的 AI 服務平台**

```
[AWS Bedrock]
├─ 模型提供者
│   ├─ Anthropic (Claude)
│   ├─ Meta (Llama)
│   ├─ Mistral AI
│   ├─ AI21 (Jurassic)
│   └─ Amazon (Titan)
├─ 無伺服器
│   └─ 無需管理 GPU
├─ 企業功能
│   ├─ 加密
│   ├─ 合規
│   └─ 隱私保護
└─ API 整合
    └─ 統一的 SDK
```

### 定價模式

**按 Token 計費：**
```
輸入 Token（你的提示）：
→ Claude 3 Haiku: $0.00025 per 1K tokens
→ Claude 3 Sonnet: $0.003 per 1K tokens
→ Claude 3 Opus: $0.015 per 1K tokens

輸出 Token（模型回應）：
→ Claude 3 Haiku: $0.00125 per 1K tokens
→ Claude 3 Sonnet: $0.015 per 1K tokens
→ Claude 3 Opus: $0.075 per 1K tokens
```

**實際計算範例：**
```
場景：AI Chatbot
- 平均輸入：500 tokens（用戶問題）
- 平均輸出：1000 tokens（Claude 回應）
- 每天 1000 次對話

Claude 3 Haiku 計算：
輸入：500 × 1000 × 30 / 1000 × $0.00025 = $3.75/月
輸出：1000 × 1000 × 30 / 1000 × $0.00125 = $37.50/月
總計：$41.25/月

Claude 3 Sonnet 計算：
輸入：500 × 1000 × 30 / 1000 × $0.003 = $45/月
輸出：1000 × 1000 × 30 / 1000 × $0.015 = $450/月
總計：$495/月

成本差異：12 倍
```

---

## 模型選擇指南

### Claude 3 系列比較

| 特性 | Haiku | Sonnet | Opus |
|------|-------|--------|------|
| **速度** | 最快（<1s） | 快（1-3s） | 較慢（3-10s） |
| **智慧** | 基礎 | 高 | 最高 |
| **輸入成本** | $0.25/1K | $3/1K | $15/1K |
| **輸出成本** | $1.25/1K | $15/1K | $75/1K |
| **Context Window** | 200K | 200K | 200K |
| **適用場景** | 簡單任務 | 通用 | 複雜任務 |

### 場景導向選擇

**場景 1：簡單問答**
```
需求：
→ 事實性問題回答
→ 文字摘要
→ 分類任務

推薦：Claude 3 Haiku
✅ 速度快
✅ 成本低
✅ 夠用

成本：~$41/月（每天 1000 次對話）
```

**場景 2：一般聊天**
```
需求：
→ 自然對話
→ 輕量推理
→ 代碼生成

推薦：Claude 3 Sonnet
✅ 平衡速度和智慧
✅ 適合多數場景
✅ 性價比高

成本：~$495/月（每天 1000 次對話）
```

**場景 3：複雜推理**
```
需求：
→ 複雜分析
→ 深度推理
→ 專業級輸出

推薦：Claude 3 Opus
✅ 最高智慧
✅ 最佳品質
✅ 專業應用

成本：~$2,475/月（每天 1000 次對話）
```

### 成本優化策略

**策略 1：智能路由**
```
[簡單問題] → Haiku（便宜）
[複雜問題] → Sonnet（中等）
[最困難]   → Opus（昂貴但必要）

實作：
def classify_difficulty(question):
    if len(question) < 100:
        return "haiku"
    elif requires_complex_reasoning(question):
        return "opus"
    else:
        return "sonnet"

節省：混合使用可省 50-70%
```

**策略 2：快取常見問題**
```
[常見問題]
    ↓
檢查快取（DynamoDB）
    ↓ 有快取
返回快取結果（$0）
    ↓ 無快取
呼叫 Bedrock

節省：快取命中率 50% = 省 50% 成本
```

**策略 3：Prompt 優化**
```
優化前：
→ "告訴我關於 AWS 的所有資訊"
→ 輸出：2000 tokens
→ 成本高

優化後：
→ "用 3 點總結 AWS"
→ 輸出：500 tokens
→ 成本降低 75%
```

---

## Bedrock 整合實作

### 基礎整合

**Lambda 函數：**
```python
import boto3
import json
import os

bedrock = boto3.client('bedrock-runtime')

def call_claude(prompt, model_id="anthropic.claude-3-sonnet-1-20240229-v1:0"):
    """呼叫 Claude API"""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    })

    response = bedrock.invoke_model(
        modelId=model_id,
        body=body
    )

    result = json.loads(response['body'].read())
    return result['content'][0]['text']
```

### 進階功能

**1. 系統提示（System Prompt）**
```python
def call_claude_with_system(user_message, system_prompt):
    """使用系統提示"""
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{
            "role": "user",
            "content": user_message
        }]
    })

    # ... 呼叫 Bedrock
```

**2. 對話歷史**
```python
def call_claude_with_history(user_message, history):
    """維持對話上下文"""
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
    ]
    messages.append({
        "role": "user",
        "content": user_message
    })

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": messages
    })

    # ... 呼叫 Bedrock
```

**3. 串流回應（Streaming）**
```python
def call_claude_streaming(prompt):
    """串流回應，減少延遲"""
    response = bedrock.invoke_model_with_response_stream(
        modelId="anthropic.claude-3-sonnet-1-20240229-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    for event in response['body']:
        chunk = json.loads(event['chunk']['bytes'])
        if 'delta' in chunk:
            yield chunk['delta']['text']
```

---

## 提示工程（Prompt Engineering）

### 優化提示以降低成本

**原則：更明確的提示 = 更短的回應 = 更低成本**

**壞提示：**
```python
prompt = "告訴我關於 AWS 的資訊"
# 結果：3000 tokens，籠統的回答
```

**好提示：**
```python
prompt = """
請用 3 點總結 AWS 的核心服務：
1. 計算服務（EC2, Lambda）
2. 儲存服務（S3, EBS）
3. 資料庫服務（RDS, DynamoDB）

每點最多 50 字。
"""
# 結果：500 tokens，精確的回答
```

### 提示模板

**模板 1：角色設定**
```python
SYSTEM_PROMPT = """
你是一位專業的 AI 助手，專精於：
- 清楚簡潔的溝通
- 準確的事實資訊
- 有幫助且友善的態度

回答時：
1. 直接回答問題
2. 避免冗長的解釋
3. 如果不確定，直接說不知道
4. 用列表組織資訊
"""
```

**模板 2：格式化輸出**
```python
prompt = f"""
請分析以下文字並輸出 JSON 格式：

文字：{text}

輸出格式：
{{
  "sentiment": "positive/negative/neutral",
  "topics": ["topic1", "topic2"],
  "summary": "一句話摘要"
}}
"""
```

**模板 3：少樣本學習（Few-shot）**
```python
prompt = """
範例 1：
輸入：我喜歡這個產品！
輸出：positive

範例 2：
這是最差的購買體驗。
輸出：negative

現在請分類：
輸入：{user_input}
輸出：
"""
```

---

## 錯誤處理與重試

### 常見錯誤

**1. 速率限制（Throttling）**
```python
from botocore.exceptions import ClientError
import time

def call_claude_with_retry(prompt, max_retries=3):
    """包含重試邏輯的呼叫"""
    for attempt in range(max_retries):
        try:
            return call_claude(prompt)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < max_retries - 1:
                    # 指數退避
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
            raise
```

**2. 超過 Token 限制**
```python
def truncate_to_token_limit(text, max_tokens=100000):
    """確保不超過模型限制"""
    # 粗略估計：1 token ≈ 4 characters
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        return text[:max_chars]
    return text
```

**3. 模型 unavailable**
```python
def call_with_fallback(prompt):
    """失敗時降級到較小模型"""
    models = [
        "anthropic.claude-3-sonnet-1-20240229-v1:0",
        "anthropic.claude-3-haiku-1-20240229-v1:0"
    ]

    for model in models:
        try:
            return call_claude(prompt, model_id=model)
        except Exception:
            continue

    raise Exception("All models failed")
```

---

## 安全與合規

### 資料隱私

**Bedrock 的承諾：**
```
✅ AWS 不會使用你的資料訓練模型
✅ 資料在傳輸和靜態時都加密
✅ 符合 GDPR, HIPAA 等合規要求
✅ 可以設置 VPC Endpoint（內網通訊）
```

### 內容過濾

**Guardrails for Bedrock：**
```python
# 開啟內容過濾
response = bedrock.invoke_model(
    modelId=model_id,
    body=body,
    guardrailIdentifier='your-guardrail-id',
    guardrailVersion='1'
)

# 阻擋：
# → 有害內容
# → PII（個人隱私資訊）
# → 不當內容
```

### PII 過濾

**實作範例：**
```python
import re

def remove_pii(text):
    """移除可能的 PII"""
    # Email
    text = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]', text)
    # 電話號碼
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
    # 信用卡號
    text = re.sub(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', '[CARD]', text)
    return text
```

---

## 監控與成本控制

### 追蹤 Token 使用

**Lambda 日誌：**
```python
import logger

def log_token_usage(input_tokens, output_tokens, model):
    logger.info({
        "event": "token_usage",
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost": calculate_cost(input_tokens, output_tokens, model)
    })
```

### 設定告警

**CloudWatch Alarm：**
```python
# 當每日成本超過 $50 時告警
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-cost-alarm \
  --metric-name EstimatedCost \
  --namespace Bedrock \
  --statistic Sum \
  --period 86400 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold
```

---

## 替代方案

### 何時不該用 Bedrock

**場景 1：極高頻率 + 簡單任務**
```
需求：
→ 每秒 1000 次請求
→ 簡單分類任務

推薦：
→ 自託管小模型（DistilBERT）
→ 成本更低
→ 延遲更低
```

**場景 2：需要完全控制**
```
需求：
→ 模型需要微調
→ 資料絕對不能出境
→ 特殊領域模型

推薦：
→ 自託管開源模型
→ SageMaker
```

**場景 3：離線處理**
```
需求：
→ 批次處理大量資料
→ 不需要即時回應

推薦：
→ SageMaker Batch Transform
→ 或本地處理
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能解釋 Bedrock 的優勢嗎？
- [ ] 我知道 Claude 3 三個模型的差別嗎？
- [ ] 我理解按 Token 計費的含義嗎？

**成本分析：**
- [ ] 我能計算不同模型的成本嗎？
- [ ] 我知道如何優化 Prompt 來降低成本嗎？
- [ ] 我能設計成本優化策略嗎？

**實作能力：**
- [ ] 我能整合 Bedrock API 嗎？
- [ ] 我知道如何處理錯誤和重試嗎？
- [ ] 我能實作串流回應嗎？

**安全與合規：**
- [ ] 我知道如何保護 PII 資料嗎？
- [ ] 我理解 Bedrock 的資料隱私承諾嗎？
- [ ] 我能設定內容過濾嗎？

---

## 下一章

現在你理解了 AI 模型整合。接下來我們會深入：

1. **密鑰管理** → 如何安全地儲存 API Key？
2. **監控與可觀測性** → 如何追蹤 AI 模型效能？
3. **錯誤處理模式** → 如何設計健壯的 AI 應用？
4. **效能優化** → 如何提升 AI 應用的回應速度？

**準備好了嗎？** 讓我們繼續探索 AI 應用的最佳實踐。
