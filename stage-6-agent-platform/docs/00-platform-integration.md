# Agent Platform：整合所有架構

**學習目標：** 理解如何將多個系統整合成統一平台，掌握生產級部署

---

## 回顧：我們建立了什麼？

**Stage 1-5 的成果：**
- Stage 1：網路基礎（VPC、子網、安全）
- Stage 2：AI Chatbot（Lambda + Bedrock）
- Stage 3：文件分析（非同步處理）
- Stage 4：RAG 知識庫（向量搜尋）
- Stage 5：Autonomous Agent（工具使用）

**問題：分散的系統**
```
每個 Stage 都獨立運作
→ 不同的 API 端點
→ 不同的認證機制
→ 不同的監控系統
→ 難以管理和維護
```

---

## Stage 6 的目標

### 統一平台

**整合所有能力到單一 API：**
```
[統一 API Gateway]
    ↓
[路由到不同的 Agent]
    ├─ Chatbot Agent (Stage 2)
    ├─ Document Agent (Stage 3)
    ├─ RAG Agent (Stage 4)
    └─ Autonomous Agent (Stage 5)
    ↓
[統一監控]
[統一認證]
[統一錯誤處理]
```

### 層級架構

```
┌─────────────────────────────────────────┐
│         API Gateway (統一入口)           │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┬────────────┐
        ↓             ↓             ↓
┌──────────────┐ ┌──────────┐ ┌────────────┐
│ Orchestrator │ │ Specialist│ │  Services  │
│  (ECS/Fargate)│ │  Agents   │ │ (Lambda)   │
│              │ │ (Lambda)  │ │            │
│ - 路由       │ │          │ │ - Chatbot  │
│ - 協調       │ │ - Chat   │ │ - Docs     │
│ - 聚合       │ │ - RAG    │ │ - Vector   │
└──────────────┘ │ - Tools  │ │ - Tools    │
                 │          │ └────────────┘
                 └──────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
┌──────────────┐ ┌──────────────────┐
│   Shared     │ │    Specialist    │
│  Resources   │ │    Resources     │
├──────────────┤ ├──────────────────┤
│ DynamoDB     │ │ DynamoDB (RAG)   │
│ OpenSearch   │ │ S3 (Documents)   │
│ S3           │ │ SQS (Queue)      │
│ Bedrock      │ │ SNS (Notify)     │
└──────────────┘ └──────────────────┘
```

---

## 路由策略

### 路由決策樹

```
[API 請求]
    ↓
[識別請求類型]
    ↓
┌─────────────────────────────────────┐
│ 請求類型分析                       │
├─────────────────────────────────────┤
│ 1. 簡單對話                       │
│    → Chatbot Agent                 │
│ 2. 需要知識庫                     │
│    → RAG Agent                     │
│ 3. 需要處理文件                   │
│    → Document Agent                │
│ 4. 需要執行工具                   │
│    → Autonomous Agent              │
└─────────────────────────────────────┘
```

### 實作範例

```python
class Orchestrator:
    def __init__(self):
        self.agents = {
            'chatbot': ChatbotAgent(),
            'rag': RAGAgent(),
            'document': DocumentAgent(),
            'autonomous': AutonomousAgent()
        }

    def route_request(self, request):
        """路由請求到適當的 Agent"""
        # 分析請求
        request_type = self.analyze_request(request)

        # 選擇 Agent
        agent = self.agents[request_type]

        # 執行
        return agent.execute(request)

    def analyze_request(self, request):
        """分析請求類型"""
        query = request.get('query', '').lower()

        # 簡單對話
        if self.is_simple_chat(query):
            return 'chatbot'

        # 需要知識
        if self.needs_knowledge(query):
            return 'rag'

        # 文件處理
        if request.get('file'):
            return 'document'

        # 工具使用
        if self.needs_tools(query):
            return 'autonomous'

        # 預設
        return 'chatbot'

    def is_simple_chat(self, query):
        """判斷是否為簡單對話"""
        keywords = ['你好', 'hello', 'hi', '謝謝', 'thank']
        return any(kw in query for kw in keywords)

    def needs_knowledge(self, query):
        """判斷是否需要知識庫"""
        keywords = ['產品', '保固', '價格', '如何', '什麼是']
        return any(kw in query for kw in keywords)

    def needs_tools(self, query):
        """判斷是否需要工具"""
        keywords = ['查詢', '搜尋', '計算', '分析']
        return any(kw in query for kw in keywords)
```

---

## ECS vs Lambda 選擇

### Orchestrator 的技術選擇

**為什麼用 ECS 而不是 Lambda？**

| 特性 | Lambda | ECS Fargate |
|------|--------|-------------|
| **啟動時間** | 秒級（冷啟動） | 分鐘級 |
| **執行時間** | < 15 分鐘 | 無限制 |
| **狀態** | 無狀態 | 有狀態 |
| **記憶體** | 有限 | 較大 |
| **成本** | 按使用 | 按小時 |

**Orchestrator 的需求：**
```
✅ 長時間執行（協調多個 Agent）
✅ 需要狀態（追蹤對話歷史）
✅ 較大記憶體（載入 Agent 配置）
✅ 無冷啟動（快速回應）
```

**決策：ECS Fargate**
```python
# ECS Task 定義
container_definitions = [{
    "name": "orchestrator",
    "image": "orchestrator:latest",
    "memory": 2048,
    "cpu": 512,
    "essential": True,
    "environment": [
        {"name": "AGENTS_ENDPOINT", "value": agents_api_url},
        {"name": "DYNAMODB_TABLE", "value": conversations_table},
        {"name": "LOG_LEVEL", "value": "INFO"}
    ],
    "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": "/ecs/orchestrator",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "ecs"
        }
    }
}]
```

---

## 分層 Agent 架構

### 主 Agent vs 專門 Agent

**主 Agent（Orchestrator）：**
```
職責：
├─ 路由請求
├─ 協調 Agent
├─ 聚合結果
└─ 管理對話

不負責：
├─ 實際推理（交給專門 Agent）
├─ 工具執行（交給專門 Agent）
└─ 知識檢索（交給專門 Agent）
```

**專門 Agent：**
```
Chatbot Agent：
├─ 處理一般對話
├─ 閒聊
└─ 簡單問題

RAG Agent：
├─ 知識檢索
├─ 語問回答
└─ 文件引用

Document Agent：
├─ 文件上傳
├─ 文字提取
└─ 內容分析

Autonomous Agent：
├─ 規劃任務
├─ 使用工具
└─ 多步推理
```

### 協作範例

```
[用戶]：「分析這份 PDF 並摘要重點」
    ↓
[Orchestrator]
    ├─ 識別：文件處理 + RAG
    ├─ 步驟 1：呼叫 Document Agent
    │   → [Document Agent] 上傳並提取文字
    ├─ 步驟 2：呼叫 RAG Agent
    │   → [RAG Agent] 搜尋相關知識
    └─ 步驟 3：聚合結果
        → 結合提取文字 + 知識庫
        → 產生摘要
```

---

## 統一認證與授權

### 認證流程

```
[用戶登入]
    ↓
[Cognito User Pool]
    ↓ (驗證)
[JWT Token]
    ↓
[API Gateway]
    ↓ (驗證 JWT)
[Orchestrator]
    ↓
[專門 Agent]
```

### 實作範例

**API Gateway Authorizer：**
```hcl
resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.platform.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    audience = ["my-platform-audience"]
    issuer   = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_xxxxx"
  }
}

resource "aws_apigatewayv2_route" "protected" {
  api_id    = aws_apigatewayv2_api.platform.id
  route_key = "POST /agent"

  target    = "integrations/${aws_apigatewayv2_integration.orchestrator.id}"
  authorization_type = "JWT"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
}
```

---

## 統一監控與可觀測性

### X-Ray 分散式追蹤

**為什麼需要 X-Ray？**
```
[用戶請求]
    ↓
[API Gateway] → 50ms
    ↓
[Orchestrator] → 100ms
    ↓
[RAG Agent]
    ├─ [OpenSearch] → 200ms
    └─ [Bedrock] → 2000ms
    ↓
[回應用戶]

總延遲：2350ms

問題：
→ 瓶頸在哪裡？
→ 哪個 Agent 最慢？
→ 哪個 API Call 花最久？
```

**X-Ray 服務圖：**
```
Service Map:
[Client] → [API Gateway] → [Orchestrator] → [RAG Agent]
                                        ├─→ [OpenSearch] (200ms)
                                        └─→ [Bedrock] (2000ms)

→ 一目了然：Bedrock 是瓶頸
```

### CloudWatch Dashboard

**統一 Dashboard：**
```python
dashboard = {
    "widgets": [
        # Orchestrator 指標
        {
            "type": "metric",
            "title": "Orchestrator Metrics",
            "metrics": [
                ["AWS/ECS", "CPUUtilization", {"Service": "orchestrator"}],
                ["AWS/ECS", "MemoryUtilization", {"Service": "orchestrator"}]
            ]
        },
        # Agent 指標
        {
            "type": "metric",
            "title": "Agent Performance",
            "metrics": [
                ["AWS/Lambda", "Duration", {"Function": "chatbot-agent"}],
                ["AWS/Lambda", "Duration", {"Function": "rag-agent"}],
                ["AWS/Lambda", "Duration", {"Function": "document-agent"}]
            ]
        },
        # 錯誤率
        {
            "type": "metric",
            "title": "Error Rates",
            "metrics": [
                ["AWS/Lambda", "Errors", {"Function": "*"}],
                ["AWS/APIGateway", "5XXError", {"ApiId": api_id}]
            ]
        }
    ]
}
```

---

## 部署策略

### 藍綠部署

```
[版本 1 (Current)]
├─ Orchestrator v1
└─ Agents v1

[版本 2 (New)]
├─ Orchestrator v2
└─ Agents v2
```

**策略 1：Canary 部署**
```
10% 流量 → 版本 2
90% 流量 → 版本 1

觀察：
→ 錯誤率
→ 延遲
→ 成本

如果版本 2 正常 → 逐步增加比例
```

**策略 2：藍綠部署**
```
[藍色環境] (生產)
├─ Orchestrator v1
└─ Agents v1

[綠色環境] (新版本)
├─ Orchestrator v2
└─ Agents v2

步驟：
1. 部署綠色環境
2. 測試綠色環境
3. 切換流量到綠色
4. 保留藍色（回滾用）
```

---

## 成本優化

### 整體成本分析

```
Stage 1: 網路基礎
→ VPC, 子網, NAT
→ 成本：$100/月

Stage 2: Chatbot
→ Lambda, API Gateway, Bedrock
→ 成本：$20/月

Stage 3: 文件分析
→ Lambda, SQS, SNS, Textract
→ 成本：$5/月

Stage 4: RAG
→ OpenSearch, Bedrock Embeddings
→ 成本：$120/月

Stage 5: Agent
→ Lambda, Step Functions, Bedrock
→ 成本：$30/月

Stage 6: Platform
→ ECS, ALB, extra monitoring
→ 成本：$50/月

────────────────────
總計：~$325/月
```

### 優化策略

**1. 共享資源**
```
多個 Stage 共享：
→ VPC 和子網（Stage 1）
→ DynamoDB 表
→ OpenSearch 叢集
→ S3 Bucket

節省：~$50/月
```

**2. 開發環境簡化**
```
開發環境：
→ 單 AZ
→ 較小的實例
→ 無備份

節省：~40%
```

**3. Auto Scaling**
```
ECS Auto Scaling：
→ 最小 1 個 task
→ 最大 5 個 task
→ 根据負載調整

節省：~30%（非尖峰時段）
```

---

## 檢核問題

**在完成所有 Stage 後，請問自己：**

**系統整合：**
- [ ] 我能設計統一平台架構嗎？
- [ ] 我知道如何路由請求嗎？
- [ ] 我理解分層 Agent 的設計嗎？

**技術選擇：**
- [ ] 我知道什麼時用 ECS vs Lambda 嗎？
- [ ] 我能設計藍綠部署嗎？
- [ ] 我理解監控的最佳實踐嗎？

**成本優化：**
- [ ] 我能計算整體平台成本嗎？
- [ ] 我知道如何優化成本嗎？
- [ ] 我能平衡成本和效能嗎？

**生產就緒：**
- [ ] 我能設計高可用架構嗎？
- [ ] 我知道如何處理災難恢復嗎？
- [ ] 我能設定完整的監控嗎？

---

## 完成整個旅程

恭喜！完成所有 Stage 後，你已經：

**技術能力：**
✅ 建立完整的 AWS 基礎架構
✅ 實作 Serverless AI 應用
✅ 設計事件驅動系統
✅ 整合向量資料庫和 RAG
✅ 建構自主 Agent
✅ 部署生產級平台

**架構思維：**
✅ 理解不同技術的取捨
✅ 能夠做架構決策
✅ 知道如何優化成本
✅ 掌握監控和除錯

**AI 應用：**
✅ 整合多個 AI 模型
✅ 建構 RAG 系統
✅ 實作 Tool Use
✅ 設計 Agent 記憶

**下一步：**
- 持續學習新的 AI 技術
- 探索更複雜的 Agent 模式
- 優化現有架構
- 分享你的知識

**你已經是一位合格的 AI 應用架構師了！** 🎉
