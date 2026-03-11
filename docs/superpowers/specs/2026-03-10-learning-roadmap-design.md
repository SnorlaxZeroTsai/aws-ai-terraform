# AWS AI Terraform Learning Roadmap - 設計文件

**日期:** 2026-03-10
**狀態:** 已批准
**目標:** 培養合格的雲端 AI 應用架構師

---

## 1. 專案概述

### 1.1 目標

建立一個完整的學習路線圖，透過實作 6 個漸進式 AI 應用專案，掌握：
- Terraform 基礎設施即程式碼（IaC）
- AWS 雲端服務架構設計
- LLM 應用開發
- RAG（檢索增強生成）系統
- AI Agent 設計與實作

### 1.2 目標受眾

**技術背景:** 雲端新手 - 熟悉程式開發，但對 AWS 和 Terraform 較陌生

**學習風格:** 從小型獨立專案開始，逐步整合成大型專案

**學習節奏:** 每階段約 3-4 週（穩健扎實）

### 1.3 架構決策原則

每個階段的設計文件必須包含：
- ✅ 優點
- ❌ 缺點
- 緩解策略
- 限制與考量（技術、成本、可擴展性、安全性）

---

## 2. 整體架構

### 2.1 六階段學習路線

| 階段 | 專案名稱 | 核心技術 | AWS 服務 | 產出成果 |
|------|----------|----------|----------|----------|
| **1** | Terraform 基礎環境 | VPC, EC2, 基礎設施 | VPC, EC2, IAM | 可執行的雲端環境 |
| **2** | AI Chatbot 服務 | LLM API, 認證, 日誌 | Lambda, API Gateway, CloudWatch | 對話式 AI 介面 |
| **3** | 智能文件分析系統 | 文件處理, 非結構化資料 | S3, Textract, DynamoDB | 文件上傳與分析 API |
| **4** | 企業知識庫 RAG | 向量搜尋, 語意理解 | OpenSearch, Bedrock | 語意搜尋系統 |
| **5** | 自主任務型 Agent | 工具調用, 規劃執行 | Step Functions, EventBridge | 能執行複雜任務的 Agent |
| **6** | AI Agent 平台整合 | 多 Agent 協作, API 編排 | 所有服務 + ECS/Lambda | 完整 AI 平台 |

### 2.2 專案相依關係

```
階段1 (基礎設施)
    ↓
階段2 (Chatbot) ─────┐
    ↓                 │
階段3 (文件分析) ─────┤
    ↓                 ├──→ 階段6 (整合平台)
階段4 (RAG) ─────────┤
    ↓                 │
階段5 (Agent) ────────┘
```

### 2.3 根目錄結構

```
aws-ai-terraform/
├── stage-1-terraform-foundation/
├── stage-2-ai-chatbot/
├── stage-3-document-analysis/
├── stage-4-rag-knowledge-base/
├── stage-5-autonomous-agent/
├── stage-6-agent-platform/
├── shared-modules/              # 共享 Terraform 模組
│   ├── vpc/
│   ├── security/
│   └── monitoring/
├── docs/
│   ├── 00-roadmap-overview.md
│   ├── architecture-principles.md
│   └── aws-services-guide.md
├── scripts/
│   ├── init.sh
│   ├── validate-all.sh
│   └── cost-estimate.sh
├── .gitignore
├── README.md
└── CLAUDE.md
```

### 2.4 每階段標準結構

```
stage-N-{project-name}/
├── terraform/              # Terraform 程式碼
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/            # 可重用模組
├── src/                    # 應用程式碼（Python/TypeScript）
├── docs/
│   └── design.md           # 設計文件
├── tests/                  # 測試腳本
└── README.md               # 課程說明與學習目標
```

---

## 3. 各階段詳細設計

### 階段 1：Terraform 基礎環境建置

**學習目標:**
- 理解 IaC 概念
- 掌握 Terraform 基本語法和工作流程
- 建立安全的 AWS 網路基礎

**技術重點:**
- Terraform state 管理
- VPC 設計（公開/私有子網）
- 安全群組與網路 ACL
- IAM 角色與權限最小化原則

**實作內容:**
```
stage-1-terraform-foundation/
├── terraform/
│   ├── vpc/
│   │   └── main.tf
│   ├── security/
│   │   └── main.tf
│   ├── ec2/
│   │   └── main.tf
│   └── iam/
│       └── main.tf
├── docs/
│   └── design.md
└── tests/
    └── connectivity_test.sh
```

**驗收標準:**
- 解釋 VPC 設計原因
- 能從零建置安全網路
- 理解多 AZ 部署的重要性

---

### 階段 2：AI Chatbot 服務

**學習目標:**
- 整合 LLM API
- 建立 Serverless API
- 實作基礎對話管理

**核心架構決策 - Serverless vs 容器 vs VM:**

| 方案 | 優點 | 缺點 | 適用場景 |
|------|------|------|----------|
| **Serverless** (Lambda) | 按用量付費、自動擴展、零運維 | 冷啟動延遲、執行時間限制 | 低頻/不穩定流量 |
| **容器** (ECS/EKS) | 一致性效能、完全控制 | 運維負擔、需管理容量 | 穩定高流量 |
| **EC2** | 最靈活、長時間運行 | 成本高、需手動擴展 | 特殊需求 |

**選擇 Serverless 的原因:**
- Chatbot 流量不穩定
- 開發階段需快速迭代
- 成本效益高

**限制與考量:**
- 技術限制：6MB payload, 15分鐘執行時間
- 成本考量：高頻請求需監控
- 可擴展性：區域限制 1000 併發
- 安全性：使用 Secrets Manager

**實作內容:**
```
stage-2-ai-chatbot/
├── terraform/
│   ├── lambda/
│   ├── api_gateway/
│   ├── secrets_manager/
│   └── cloudwatch/
├── src/
│   ├── handlers/
│   │   └── chat.py
│   ├── services/
│   │   └── llm_service.py
│   └── utils/
├── docs/
│   └── design.md
└── tests/
    └── api_tests.py
```

**驗收標準:**
- 說明 Serverless 優缺點
- 能部署無服務器 API
- 理解 LLM 抽象層的設計原因

---

### 階段 3：智能文件分析系統

**學習目標:**
- 處理非結構化資料
- 整合 AI 服務進行文件理解
- 建立異步處理流程

**核心架構決策 - 為什麼需要訊息佇列:**

- 解耦：上傳和處理分離
- 錯誤處理：自動重試機制
- 負載均攤：調節處理速度

**DynamoDB 分區鍵設計考量:**
- 查詢模式決定分區鍵
- 避免熱分區
- 考慮排序需求

**實作內容:**
```
stage-3-document-analysis/
├── terraform/
│   ├── s3/
│   ├── lambda/
│   ├── textract/
│   ├── dynamodb/
│   └── sns_sqs/
├── src/
│   ├── handlers/
│   │   ├── upload_handler.py
│   │   └── analysis_handler.py
│   ├── services/
│   │   └── textract_service.py
│   └── models/
│       └── document.py
├── docs/
│   └── design.md
└── tests/
    └── document_pipeline_test.py
```

**驗收標準:**
- 設計非結構化資料處理流程
- 理解異步架構的優缺點
- 能處理文件處理的錯誤重試

---

### 階段 4：企業知識庫 RAG 系統

**學習目標:**
- 理解向量搜尋原理
- 實作 RAG 架構
- 掌握語意搜尋與知識注入

**核心架構決策 - 向量資料庫選擇:**

| 方案 | 優點 | 缺點 | 成本考量 |
|------|------|------|----------|
| **OpenSearch** | AWS 原生、可擴展、混合搜尋 | 運維負擔 | 按實例付費 |
| **Aurora pgvector** | 關聯式 + 向量、熟悉 | 效能較差 | 按使用付費 |
| **Pinecone** | 託管、零運維 | 資料出境 | 按索引付費 |

**選擇:** OpenSearch（AWS 原生、進階功能完整）

**Chunk 策略決策:**

| 策略 | 適用場景 | 優缺點 |
|------|----------|--------|
| 固定長度 | 通用文件 | 簡單但可能破壞語意 |
| 語意段落 | 結構化文件 | 保持語意但複雜 |
| 混合式 | 複雜文件 | 最佳但難實作 |

**限制與考量:**
- 最小節點要求（成本）
- 向量維度影響記憶體
- VPC 內部署安全性

**實作內容:**
```
stage-4-rag-knowledge-base/
├── terraform/
│   ├── opensearch/
│   ├── lambda/
│   ├── s3/
│   └── bedrock/
├── src/
│   ├── handlers/
│   │   ├── index_handler.py
│   │   └── search_handler.py
│   ├── services/
│   │   ├── embedding_service.py
│   │   ├── opensearch_service.py
│   │   └── rag_service.py
│   └── prompts/
│       └── rag_templates.py
├── docs/
│   └── design.md
└── tests/
    └── rag_pipeline_test.py
```

**驗收標準:**
- 實作完整的 RAG 系統
- 能調整向量搜尋參數
- 理解不同 Chunk 策略的影響

---

### 階段 5：自主任務型 Agent

**學習目標:**
- 實作 ReAct 模式
- 工具調用設計
- 複雜任務分解與執行

**核心架構決策 - 編排引擎選擇:**

| 方案 | 優點 | 缺點 | 適用場景 |
|------|------|------|----------|
| **Step Functions** | 視覺化、可觀測、原生整合 | 複雜條件邏輯受限 | 標準工作流程 |
| **自建編排器** | 完全彈性 | 需維護、可觀測性差 | 高度動態流程 |
| **LangChain** | AI 特化 | 抽象層過厚 | 原型開發 |

**選擇:** Step Functions + 自建 reasoning

**工具設計模式:**
- 統一介面便于 LLM 調用
- 便于新增工具
- 支援工具組合

**限制與考量:**
- 狀態機大小限制（256 KB）
- 執行次數成本
- 複雜分支需要巧妙設計

**實作內容:**
```
stage-5-autonomous-agent/
├── terraform/
│   ├── step_functions/
│   ├── lambda/
│   ├── dynamodb/
│   └── s3/
├── src/
│   ├── agent/
│   │   ├── core.py
│   │   ├── reasoning.py
│   │   └── memory.py
│   ├── tools/
│   │   ├── registry.py
│   │   ├── base_tool.py
│   │   └── implementations/
│   └── workflows/
│       └── task_flow.asl.json
├── docs/
│   └── design.md
└── tests/
    └── agent_test.py
```

**驗收標準:**
- 設計 Agent 工具系統
- 處理複雜任務流程
- 理解 ReAct 模式的優缺點

---

### 階段 6：AI Agent 平台整合

**學習目標:**
- 整合所有前階段成果
- 多 Agent 協作架構
- API 編排與權限管理
- 監控與可觀測性

**核心架構決策 - 部署架構:**

| 方案 | 優點 | 缺點 | 成本 |
|------|------|------|------|
| **全 Lambda** | 最低成本、自動擴展 | 冷啟動、複雜度限制 | 低 |
| **ECS Fargate** | 一致效能、Docker 一致性 | 基礎成本 | 中 |
| **EKS** | 最靈活 | 運維負擔極高 | 高 |

**選擇:** 混合架構（API/邏輯層 Lambda + 長期服務 ECS）

**多 Agent 協作模式:**

| 模式 | 描述 | 適用場景 |
|------|------|----------|
| 層級式 | 主控 Agent 分派任務 | 明確分工 |
| 網狀協作 | Agent 間直接通訊 | 動態協作 |
| 管線式 | 依序處理任務 | 串行處理 |

**實作內容:**
```
stage-6-agent-platform/
├── terraform/
│   ├── api_gateway/
│   ├── ecs/
│   ├── xray/
│   └── cloudwatch/
├── src/
│   ├── platform/
│   │   ├── api/
│   │   ├── auth/
│   │   └── orchestrator.py
│   ├── agents/
│   └── shared/
├── docs/
│   └── design.md
├── scripts/
│   └── deploy.sh
└── docker/
    └── Dockerfile
```

**驗收標準:**
- 整合所有服務
- 建立可監控的 AI 平台
- 能設計多 Agent 協作系統

---

## 4. 工作流程與交付物

### 4.1 Git 策略

```bash
# 每階段獨立分支
git checkout -b stage-N
# 完成後提交
git commit -m "Complete stage N: [description]"
# 合併到 main
git checkout main
git merge stage-N
```

### 4.2 每階段交付物

**程式碼:**
- Terraform 配置（可執行）
- 應用程式碼（可測試）
- 測試腳本（通過）

**文件:**
- design.md（架構決策）
- README.md（使用說明）
- ARCHITECTURE.md（架構圖）

**驗證:**
- 部署成功的證明
- 測試執行結果
- 成本報告

### 4.3 成本管理

每階段結束後產生成本報告：
- 預估月費用
- 實際使用費用
- 成本最佳化建議
- 免費額度使用情況

---

## 5. 學習驗收標準總覽

| 階段 | 驗收標準 |
|------|----------|
| **1** | 解釋 VPC 設計原因，能從零建置安全網路 |
| **2** | 說明 Serverless 優缺點，能部署無服務器 API |
| **3** | 設計非結構化資料處理流程，理解異步架構 |
| **4** | 實作 RAG 系統，調整向量搜尋參數 |
| **5** | 設計 Agent 工具系統，處理複雜任務流程 |
| **6** | 整合所有服務，建立可監控的 AI 平台 |

---

## 6. 設計原則總結

1. **漸進式學習**：從基礎到進階，每階段建構在前一階段之上
2. **實作為主**：每個階段都是完整的可執行專案
3. **架構思維**：每個決策都有深入的優缺點分析
4. **真實場景**：所有專案都基於實際 AI 應用需求
5. **可重用性**：前面的成果支撐後續發展

---

**設計批准:** 2026-03-10
**下一步:** 使用 writing-plans 技能創建實施計劃
