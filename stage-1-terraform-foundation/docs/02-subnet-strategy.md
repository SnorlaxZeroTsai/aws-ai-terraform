# 公有 vs 私有子網策略

**學習目標：** 深入理解子網劃分策略，什麼資源該放哪裡，為什麼這樣分

---

## 回顧：子網的兩種類型

在之前的章節我們學到：
- **公有子網：** 有公網 IP，可以直接對外通訊
- **私有子網：** 無公網 IP，只能透過 NAT 對外通訊

現在讓我們深入探討：**如何決定資源放哪裡？**

---

## 核心決策框架

### 決策樹：資源應該放哪裡？

```
這個資源需要什麼？
    ↓
[直接對外服務？]
    ├─ 是 → 公有子網
    │   ├─ Load Balancer
    │   ├─ API Gateway
    │   ├─ Reverse Proxy
    │   └─ Public Web Server
    │
    └─ 否 → 需要存取資料嗎？
        ├─ 是 → 私有子網
        │   ├─ Application Server
        │   ├─ AI/ML Service
        │   ├─ Cache (Redis/Memcached)
        │   └─ Message Queue
        │
        └─ 否 → 私有子網 (更嚴格的隔離)
            ├─ Database (Primary)
            ├─ Database (Replica)
            └─ Internal Services
```

---

## 類比：公司的辦公室規劃

### 公有子網 = 前台接待區

```
[前台接待區]
├─ 接待員 (Load Balancer)
│   └─ 引導訪客到正確位置
├─ 展示區 (Public Server)
│   └─ 展示產品資訊
└─ 詢問室 (API Gateway)
    └─ 回應一般性問題

特點：
✓ 任何人都可以進入
✓ 有限度的權限
✓ 服務導向
```

### 私有子網 = 內部辦公區

```
[員工辦公區]
├─ 工程師辦公室 (App Server)
│   └─ 處理業務邏輯
├─ 主管辦公室 (Database)
│   └─ 存儲重要資料
└─ 機房/工具間 (Cache, Queue)
    └─ 輔助工具

特點：
✓ 需要門禁卡才能進入
✓ 權限管理
✓ 包含公司核心資產
```

---

## 公有子網：用途與設計

### 放在公有子網的資源

#### 1. Load Balancer（必須）

**為什麼？**
- 需要接收外部請求
- 用戶的瀏覽器/應用程式需要連到它
- 作為統一入口點

**典型配置：**
```
[Internet]
    ↓
[AWS Application Load Balancer]
    ↓ (分發流量)
[AZ-a: Web Server]    [AZ-b: Web Server]
    ↓                       ↓
[私有子網的應用伺服器] [私有子網的應用伺服器]
```

**如果放在私有子網：**
```
❌ Load Balancer 在私有子網
→ 用戶無法直接連線
→ 需要多層 Proxy 設定
→ 架構複雜度增加
→ 延遲增加
```

---

#### 2. API Gateway（必須）

**為什麼？**
- 提供公開的 API 端點
- 需要接收來自世界各地的請求
- 作為 API 的門戶

**典型配置：**
```
[外部用戶/應用]
    ↓
[API Gateway: /chat, /analyze]
    ↓ (觸發)
[AZ-a: Lambda Function]
[AZ-b: Lambda Function]
    ↓ (處理)
[私有子網的資源]
```

**流量路徑：**
```
1. 外部請求 → API Gateway
2. API Gateway → Lambda（公有或私有）
3. Lambda → 資源（私有子網）
```

---

#### 3. NAT Gateway（特殊情況）

**為什麼在公有子網？**
- 需要公網 IP 位址
- 作為私有子網的出口
- 透過它轉發流量

**設計考慮：**
```
[NAT Gateway (EIP: 54.123.45.67)]
    ↑ (放在公有子網)
    ↓ (轉發流量)
[Internet]

流向：
[私有子網 EC2] → [NAT Gateway] → [外部]
```

---

#### 4. Reverse Proxy / Web Server（可選）

**放在公有子網的情況：**
- 靜態網站託管
- Nginx/Apache 反向代理
- 內容傳遞網路 (CDN)

**設計範例：**
```
[Internet]
    ↓
[CloudFront (CDN)]
    ↓
[公有子網: Nginx Reverse Proxy]
    ↓ (靜態檔案、反向代理)
[私有子網: Application Server]
```

**為什麼這樣？**
- Nginx 處理 HTTPS、靜態檔案、快取
- 減輕後端壓力
- 可以部署 WAF 保護

---

### 公有子網的安全性考量

**雖然是"公有"，但仍然有保護：**

**安全層級：**
```
[外部攻擊]
    ↓
[WAF (Web Application Firewall)] ← 第一層過濾
    ↓
[Security Group] ← 第二層控制
    ↓
[Network ACL] ← 第三層過濾
    ↓
[個別資源]
```

**安全配置：**
```hcl
# 只開放必要的端口
resource "aws_security_group" "public" {
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH 只從特定 IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR.OFFICE.IP/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

## 私有子網：用途與設計

### 放在私有子網的資源

#### 1. Application Server（AI 應用）

**為什麼？**
- 包含業務邏輯和知識產權
- 不應該直接暴露給外部
- 需要額外的保護層

**典型配置：**
```
[Load Balancer]
    ↓ (驗證、過濾)
[公有子網: Bastion/Gateway]
    ↓ (安全通訊)
[私有子網: AI 應用伺服器]
    ├─ 處理 AI 模型呼叫
    ├─ 存取檢索資料庫
    └─ 執行業務邏輯
```

**安全好處：**
- ✅ 不能直接從外部 SSH
- ✅ 不能被直接掃描
- ✅ 即使 API 被攻破，應用伺服器仍是安全的

---

#### 2. 資料庫（必須）

**為什麼必須在私有子網？**
- 包含最敏感的資料
- 資料庫應該是最保護的資源
- 攻擊者的主要目標

**多層保護：**
```
[外部攻擊]
    ↓
[公有子網 API] ← 可能被攻破
    ↓ (Security Group 限制)
[私有子網應用] ← 可能被攻破
    ↓ (Security Group 限制)
[私有子網資料庫] ← 最後防線
    ✅ 攻擊者無法直接到達
```

**設計原則：**
```
資料庫安全群組規則：
- 只接受來自應用層的連線
- 拒絕所有來自 0.0.0.0/0 的連線
- 只開放資料庫端口（如 3306 for MySQL）
```

---

#### 3. AI/ML 模型服務

**為什麼在私有子網？**
- 模型服務很貴（p3.2xlarge）
- 包含訓練好的模型
- 不應該暴露給外部

**架構範例：**
```
[API Gateway]
    ↓
[Lambda 輕量模型]
    ↓ (私有通訊)
[私有子網: AI 模型推理服務]
    ├─ GPU 實例：p3.2xlarge
    ├─ 模型：Claude 3.5 Sonnet
    └─ 批次處理引擎
```

**成本考量：**
```
GPU 實例：$5-10/小時
24/7 運作：$120-240/天
$3,600-7,200/月

這麼貴的資源：
✅ 必須保護（私有子網）
✅ 必須監控使用
✅ 必須最佳化效率
```

---

#### 4. 快取服務（Redis/Memcached）

**為什麼在私有子網？**
- 儲存敏感的快取資料
- 可能包含使用者的 session
- 經常與應用伺服器一起部署

**部署模式：**
```
[私有子網應用] ←→ [私有子網 Redis]
                        ↑
                    快取命中率提升
```

**安全考量：**
```
Redis 如果被入侵：
→ Session 袊取
→ 用戶可以偽造身分
→ 資料可能外洩

所以必須：
- 放在私有子網
- 只讓應用存取
- 啟用 TLS/SSL
```

---

#### 5. 訊息佇列（SQS/Kafka）

**為什麼在私有子網？**
- 處理非同步任務
- 包含業務邏輯和資料
- 不應該被外部直接存取

**設計範例：**
```
[API Lambda]
    ↓ (發送訊息)
[SQS Queue (私有子網)]
    ↓ (消費)
[Worker Lambda (私有子網)]
    ↓
[私有子網資料庫]
```

---

### 私有子網的進階設計

#### 分層私有子網

```
VPC: 10.0.0.0/16
│
├─ [私有子網 A1: 應用層]
│   ├─ Application Server
│   └─ API 服務
│
├─ [私有子網 A2: 資料層]
│   ├─ Primary DB
│   └─ Standby DB
│
└─ [私有子網 A3: 管理層]
    ├─ Admin Server
    ├─ Monitoring
    └─ Backup

Security Group 規則：
[A1] ←→ [A2] (允許)
[A1] ←→ [A3] (管理員 IP)
[A2] ←/ [A3] (隔離)
```

**好處：**
- ✅ 分層防禦
- ✅ 減少橫向攻擊面
- ✅ 符合最小權限原則

---

## 什麼情況下可以放公有子網？

### 無狀態服務

**Lambda 冷啟動：**
```
[Lambda Function]
    ├─ 處理請求
    ├─ 呼叫 AI API
    └─ 返回結果

特點：
✓ 無狀態
✓ 短期執行
✓ 數據在 DynamoDB（可設 Endpoint）
✓ 可以放公有子網
```

**為什麼可以？**
- 沒有敏感資料
- 不保留狀態
- 被攻破風險低

---

### 內容傳遞網路

**CloudFront + S3：**
```
[CloudFront (CDN)]
    ↓
[S3-Origin (可設 Endpoint)]
    └─ 靜態資料

→ 不需要公開的 API 端點
→ S3 可以設為私有
→ 安全性高
```

---

## 子網設計最佳實踐

### 1. 命名規範

```bash
# 清楚明確的命名
public-subnet-az-a
public-subnet-az-b
private-app-subnet-az-a
private-app-subnet-az-b
private-db-subnet-az-a
private-db-subnet-az-b
```

### 2. 標籤和文檔

**在 Terraform 中使用標籤：**
```hcl
resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name        = "public-subnet-az-a"
    Type        = "public"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
```

**建立子網清單文檔：**
```markdown
# 子網使用規範

## 公有子網
- **用途：** 對外服務、Load Balancer
- **部署：** ALB, API Gateway, NAT Gateway
- **存取：** 任何人
- **風險：** 較高，需要額外安全措施

## 私有應用子網
- **用途：** 應用伺服器、AI 模型服務
- **部署：** ECS, EC2, Lambda
- **存取：** 只能從公有子網
- **風險：** 中等

## 私有資料子網
- **用途：** 資料庫、快取
- **部署：** RDS, ElastiCache, DynamoDB
- **存取：** 只能從應用子網
- **風險：** 低（最保護）
```

---

### 3. 安全群組設計

**公有子網 SG：**
```hcl
# 只開放必要的端口
ingress {
  from_port   = 443  # HTTPS
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

ingress {
  from_port   = 80   # HTTP (可選，可重定向到 443)
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}
```

**私有應用子網 SG：**
```hcl
# 只接受來自公有子網的連線
ingress {
  from_port   = 8080  # 應用端口
  to_port     = 8080
  protocol    = "tcp"
  security_groups = [aws_security_group.public.id]
}

# 拒絕來自 0.0.0.0/0
# 不能直接從外部存取
```

**私有資料子網 SG：**
```hcl
# 只接受來自應用子網的連線
ingress {
  from_port   = 3306  # MySQL
  to_port     = 3306
  protocol    = "tcp"
  security_groups = [aws_security_group.private_app.id]
}

# 更嚴格的規則
```

---

## 實際案例：E-commerce 平台

### 場景描述

一個電商平台需要：
- 接收用戶訂單
- 處理付款
- 管理商品庫存
- AI 推薦系統
- 後台管理系統

### 子網設計

```
VPC: 10.0.0.0/16
│
├─ [公有子網 × 3 AZ]
│   ├─ ALB (對外服務)
│   ├─ NAT Gateway
│   └─ Bastion Host (管理員入口)
│
├─ [私有 Web 子網 × 3 AZ]
│   ├─ Web Server (產品頁面)
│   ├─ API Server (訂單處理)
│   └─ 推薦服務
│
└─ [私有資料子網 × 3 AZ]
    ├─ RDS MySQL (訂單、會員)
    ├─ RDS PostgreSQL (商品)
    └─ Redis (快取、Session)
```

### 流量路徑

**用戶瀏覽產品：**
```
[用戶] → [ALB] → [Web Server (私有)]
    └─ [快取] ← Redis (私有)
    └─ [資料庫] ← RDS (私有)
```

**AI 推薦：**
```
[API Server]
    ↓
[推薦服務 (私有)]
    ↓
[Embedding Service (私有)]
    ↓
[Vector Database (私有)]
    ↓
[推薦結果]
```

**管理員管理：**
```
[管理員] → [Bastion (公有)]
    ↓ (SSH)
[私有子網]
    ↓
[Admin Server]
    ↓ (存取)
[資料庫]
```

---

## 常見錯誤

### 錯誤 1：資料庫在公有子網

```
❌ [資料庫] ←→ [公網]
→ 可以直接被攻擊
→ 違背合規要求
→ 實例數據外洩風險
```

### 錯誤 2：應用和資料庫在同一層

```
❌ [應用] ←→ [資料庫] (都在同一私有子網)
→ 一旦應用被攻破，資料庫也暴露
→ 違背分層防禦原則
```

**正確做法：**
```
✅ [公有子網應用] ←→ [私有子網應用] ←→ [私有資料子網資料庫]
→ 多層防禦
→ 最小權限
```

### 錯誤 3：過度分割

```
❌ 過度劃分：10 個子網
→ 管理複雜
→ 跨子網延遲
→ 成本增加（每個子網的 NAT？）
```

**原則：從簡單開始**
- 開發：1 公有 + 1 私有
- 測試：2 公有 + 2 私有
- 生產：按需增加

---

## 檢核問題

**在繼續之前，請問自己：**

**基本概念：**
- [ ] 我能解釋公有和私有子網的差別嗎？
- [ ] 我知道什麼資源該放公有子網嗎？
- [ ] 我知道什麼資源必須放私有子網嗎？

**架構設計：**
- [ ] 我能設計多層子網架構嗎？
- [ ] 我理解為什麼要分層防禦嗎？
- [ ] 我知道如何設置子網間的通訊規則嗎？

**安全考量：**
- [ ] 我知道如何用 Security Group 控制流量嗎？
- [ ] 我理解最小權限原則在子網設計中的應用嗎？
- [ ] 我能說明不同層級的安全策略嗎？

**成本考量：**
- [ ] 我知道多子網的成本影響嗎？
- [ ] 我能平衡安全和成本嗎？
- [ ] 我知道什麼時候可以簡化架構嗎？

**實際應用：**
- [ ] 我能根據應用需求設計子網劃分嗎？
- [ ] 我能決定什麼時候該用公有/私有子網嗎？
- [ ] 我能設計多環境（dev/prod）的子網策略嗎？

---

## 下一章

現在我們理解了子網策略。接下來我們會深入：

1. **安全分層設計** → 如何設置多層防禦？
2. **成本優化策略** → 如何降低整體成本？
3. **替代架構方案** → 還有哪些設計選擇？

**準備好了嗎？** 讓我們繼續完善網路基礎架構的設計。
