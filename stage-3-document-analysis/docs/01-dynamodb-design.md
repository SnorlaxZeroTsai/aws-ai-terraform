# 資料庫設計：DynamoDB 的藝術

**學習目標：** 掌握 NoSQL 資料庫設計，理解訪問模式驅動的架構

---

## 為什麼選擇 DynamoDB？

### 場景：文件元資料儲存

**需求：**
- 儲存每個上傳文件的元資料
- 支援快速查詢（按 ID、按狀態、按檔名）
- 自動擴展
- 低延遲

### 傳統 SQL vs NoSQL

**如果用 RDS（MySQL）：**
```sql
CREATE TABLE documents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    document_id VARCHAR(36),
    filename VARCHAR(255),
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'),
    uploaded_at TIMESTAMP,
    -- 更多欄位...

    INDEX idx_status (status),
    INDEX idx_filename (filename),
    INDEX idx_uploaded_at (uploaded_at)
);

-- 查詢範例
SELECT * FROM documents WHERE document_id = 'xxx';
SELECT * FROM documents WHERE status = 'COMPLETED';
SELECT * FROM documents WHERE filename = 'report.pdf';
```

**問題：**
```
❌ 需要管理連線池
❌ 垂直擴展（升級實例大小）
❌ JOIN 操作複雜
❌ 資料庫維護（備份、修補）
❌ 成本較高
```

**用 DynamoDB：**
```python
# 建立項目（Put）
dynamodb.put_item(
    TableName='documents',
    Item={
        'document_id': 'uuid-123',
        'uploaded_at': '2024-03-16T10:00:00Z',
        'filename': 'report.pdf',
        'status': 'PROCESSING',
        # 其他屬性...
    }
)

# 查詢（Get）
doc = dynamodb.get_item(
    TableName='documents',
    Key={'document_id': 'uuid-123', 'uploaded_at': '2024-03-16T10:00:00Z'}
)

# 查詢（Query - 使用 GSI）
result = dynamodb.query(
    TableName='documents',
    IndexName='status-index',
    KeyConditionExpression='status = :status',
    ExpressionAttributeValues={':status': 'COMPLETED'}
)
```

**優點：**
```
✅ 毫秒級延遲
✅ 自動擴展（水平）
✅ 無需管理伺服器
✅ 按使用付費
✅ 內建加密
```

---

## 核心概念

### 1. 主鍵設計

**Partition Key + Sort Key（複合主鍵）**
```
Table: documents

Primary Key:
├─ Partition Key: document_id (String)
└─ Sort Key: uploaded_at (String)

優點：
✅ 同一 document_id 可以有多個版本
✅ 可以按時間排序
✅ 支援時間範圍查詢
```

**設計原則：**
```
❌ 不好的設計：
Partition Key: auto_increment_id
→ 寫入熱點（所有寫入到同一個分區）

✅ 好的設計：
Partition Key: document_id (UUID)
→ 均勻分散到不同分區
→ 並行寫入
```

### 2. 全域次要索引（GSI）

**為什麼需要 GSI？**
```
只能用 Primary Key 查詢
→ 但我們需要按 status 查詢
→ 需要按 filename 查詢

解決方案：GSI
```

**Stage 3 的 GSI 設計：**
```
GSI 1: status-index
├─ Partition Key: status
└─ Sort Key: uploaded_at

用途：查詢所有完成的文件
→ SELECT * WHERE status = 'COMPLETED'

GSI 2: filename-index
├─ Partition Key: filename
└─ Sort Key: uploaded_at

用途：檢查檔名是否已上傳
→ SELECT * WHERE filename = 'report.pdf'
```

**成本考量：**
```
GSI = 複製資料
→ 每個 GSI 都佔用空間
→ 讀寫都會消耗容量

建議：
→ 只建立必要的 GSI
→ 考慮查詢頻率
→ 評估成本
```

### 3. 容量模式

**On-Demand（按需）vs Provisioned（預留）**

| 特性 | On-Demand | Provisioned |
|------|-----------|-------------|
| **成本** | 較高（$1.25/M read） | 較低（固定價格） |
| **管理** | 零管理 | 需要規劃容量 |
| **擴展** | 自動 | 需要設定 |
| **適用** | 不可預測流量 | 穩定流量 |

**選擇建議：**
```
開發/測試：On-Demand
生產環境（不可預測）：On-Demand
生產環境（穩定高流量）：Provisioned + Auto Scaling
```

---

## 訪問模式驅動設計

### 核心原則

**DynamoDB = 訪問模式驅動設計**

```
❌ 錯誤思維：
「我有哪些實體？它們有什麼屬性？」

✅ 正確思維：
「我的應用需要查詢什麼？如何高效查詢？」
```

### Stage 3 的訪問模式

**模式 1：按 document_id 查詢**
```
Query: Get document by ID
Pattern: Primary Key lookup
Access: O(1) - 最快
```

**模式 2：按 status 查詢**
```
Query: Get all completed documents
Pattern: GSI query on status-index
Access: O(log n) - 快
```

**模式 3：按 filename 查詢**
```
Query: Check if filename exists
Pattern: GSI query on filename-index
Access: O(log n) - 快
```

### 反模式：避免 Scan

**❌ 絕對不要用 Scan**
```python
# 錯誤：Scan 整個表
response = dynamodb.scan(TableName='documents')
→ 讀取整個表
→ 極慢
→ 極貴（$1.25/M read units）
→ 應該禁止
```

**✅ 使用 Query 或 Get**
```python
# 正確：按 Primary Key 查詢
response = dynamodb.get_item(Key={...})

# 正確：按 GSI 查詢
response = dynamodb.query(
    IndexName='status-index',
    KeyConditionExpression='status = :status'
)
```

---

## 資料模型設計

### 單表設計 vs 多表設計

**單表設計（推薦）：**
```
Table: items

Primary Key:
├─ PK (Partition Key): type_id (e.g., "USER#123")
└─ SK (Sort Key): sort_id (e.g., "PROFILE", "ORDER#456")

Data:
PK=USER#123, SK=PROFILE → {name: "John", email: "..."}
PK=USER#123, SK=ORDER#456 → {date: "...", total: 100}
PK=USER#123, SK=ORDER#789 → {date: "...", total: 200}

優點：
✅ 相關資料在一起
✅ 單次查詢獲取所有資料
✅ 減少請求次數
```

**多表設計：**
```
Table: users
└─ PK: user_id

Table: orders
└─ PK: order_id

缺點：
❌ 需要多次查詢
❌ JOIN 不存在
❌ 成本更高
```

### 一對多關係

**用戶的文件：**
```
設計選項 1：一個文件一筆記錄
PK: user_id (Partition Key)
SK: document_id (Sort Key)

Query:
Get all documents for user:
→ Query where PK=user_id

設計選項 2：嵌套屬性
PK: user_id
SK: PROFILE
Attributes:
    documents: [doc1, doc2, doc3]

限制：
→ 項目大小限制（400KB）
→ 不適合大量數據
```

---

## 實作最佳實踐

### 1. 批次操作

**BatchWriteItem：**
```python
# 批次寫入（最多 25 項）
dynamodb.batch_write_item(
    RequestItems={
        'documents': [
            {'PutRequest': {'Item': doc1}},
            {'PutRequest': {'Item': doc2}},
            # ... 最多 25 項
        ]
    }
)

優點：
✅ 減少網路往返
✅ 原子性操作（全部成功或全部失敗）
✅ 更低成本
```

### 2. 條件表達式

**防止覆蓋：**
```python
# 只在不存在的情況下建立
dynamodb.put_item(
    TableName='documents',
    Item={'document_id': '123', 'status': 'PENDING'},
    ConditionExpression='attribute_not_exists(document_id)'
)
```

**樂觀鎖：**
```python
# 更新時檢查版本
dynamodb.update_item(
    Key={'document_id': '123'},
    UpdateExpression='SET #status = :status',
    ConditionExpression='version = :expected_version',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':status': 'COMPLETED',
        ':expected_version': 1
    }
)
```

### 3. 投影表達式

**只讀取需要的屬性：**
```python
# 只讀取 status 和 uploaded_at
response = dynamodb.get_item(
    TableName='documents',
    Key={'document_id': '123', 'uploaded_at': '...'},
    ProjectionExpression='status, uploaded_at'
)

優點：
✅ 減少資料傳輸
✅ 降低成本（按讀取容量計費）
✅ 提升效能
```

---

## 成本優化

### 成本結構

```
On-Demand 定價：
→ 讀取：$1.25 per million read units
→ 寫入：$0.25 per million write units
→ 儲存：$0.25 per GB-month

計算範例：
10K 文件，每個 5KB：
→ 儲存：50GB × $0.25 = $12.50/月
→ 讀取：10K × 1 unit = 10K units = $0.01/月
→ 寫入：10K × 1 unit = 10K units = $0.003/月
→ 總計：~$12.51/月
```

### 優化策略

**1. 減少項目大小**
```
❌ 儲存完整文件內容
✅ 只儲存元資料
→ 文件內容放 S3
→ DynamoDB 只存 S3 URI
```

**2. 壓縮屬性**
```
import gzip
import json

# 壓縮大型屬性
large_data = json.dumps(data)
compressed = gzip.compress(large_data.encode())

dynamodb.put_item(Item={
    'document_id': '123',
    'data': compressed
})
```

**3. 使用 TTL**
```python
# 自動刪除舊資料
dynamodb.put_item(
    Item={
        'document_id': '123',
        'uploaded_at': '2024-03-16T10:00:00Z',
        'ttl': int(time.time()) + (30 * 24 * 3600)  # 30 天後刪除
    }
)
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能解釋 DynamoDB 的核心概念嗎？
- [ ] 我理解 Partition Key 和 Sort Key 的作用嗎？
- [ ] 我知道什麼時候需要 GSI 嗎？

**設計能力：**
- [ ] 我能設計訪問模式驅動的資料模型嗎？
- [ ] 我知道如何避免 Scan 嗎？
- [ ] 我能設計一對多關係嗎？

**實作能力：**
- [ ] 我能使用批次操作嗎？
- [ ] 我知道如何使用條件表達式嗎？
- [ ] 我能優化 DynamoDB 成本嗎？

---

## 總結

完成 Stage 3 後，你會理解：
- ✅ NoSQL vs SQL 的選擇
- ✅ DynamoDB 的核心概念
- ✅ 訪問模式驅動設計
- ✅ GSI 的使用場景
- ✅ 成本優化策略

**下一階段：** 向量資料庫與 RAG 架構
