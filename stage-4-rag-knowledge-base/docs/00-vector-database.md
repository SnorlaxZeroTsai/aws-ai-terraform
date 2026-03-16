# 向量資料庫：為什麼需要向量搜尋？

**學習目標：** 理解向量資料庫的原理，掌握 RAG 架構的設計

---

## 回顧：我們現在有什麼？

在 Stage 1-3，我們建立了：
- Stage 1：網路基礎（VPC、子網、NAT）
- Stage 2：AI Chatbot（Lambda + Bedrock）
- Stage 3：文件分析（非同步處理、DynamoDB）

**Stage 2 Chatbot 的限制：**
```
[用戶]：「這個產品是什麼？」
    ↓
[Claude]：「我不知道你公司的產品資訊。」
    ↓
[問題]
→ LLM 只有訓練時的知識
→ 無法存取私有資料
→ 無法回答公司特定問題
```

---

## 場景：需要私有知識的 AI

### 真實需求

```
[員工]：「我們公司的產品保固是多久？」
    ↓
[需要知道]
→ 產品手冊
→ 保固政策
→ 內部文件
    ↓
[目前方案]
→ 人工查詢（慢）
→ 關鍵字搜尋（不準確）
→ 問專家（依賴個人）
```

### 解決方案：RAG（檢索增強生成）

```
[用戶問題]
    ↓
[向量化查詢]
    ↓
[向量資料庫搜尋]
    ↓ (最相關的文件)
[檢索到的文件]
    ↓
[結合問題 + 文件]
    ↓
[LLM 生成回答]
    ↓
[準確且有依據的回答]
```

**好處：**
```
✅ 使用私有資料
✅ 回答有依據（可溯源）
✅ 準確度高
✅ 可隨時更新知識
```

---

## 什麼是向量資料庫？

### 向量 = 數學表示

**文字 → 向量：**
```
文字："Apple is a fruit"

向量（簡化）：
[0.23, -0.15, 0.67, 0.89, ...]
(1536 維度)
```

**為什麼要向量化？**
```
相似的概念 → 相近的向量

"Apple" (水果)
[0.23, -0.15, 0.67, ...]
     ↓ 距離短
"Banana" (水果)
[0.21, -0.18, 0.65, ...]

"Apple" (水果)
[0.23, -0.15, 0.67, ...]
     ↓ 距離遠
"iPhone" (科技)
[0.85, 0.42, -0.33, ...]
```

### 向量搜尋 vs 關鍵字搜尋

| 特性 | 關鍵字搜尋 | 向量搜尋 |
|------|-----------|---------|
| **匹配方式** | 精確詞彙 | 語意相似度 |
| **理解能力** | 無 | 高 |
| **同義詞** | 不支援 | 支援 |
| **錯別字** | 不支援 | 支援 |
| **成本** | 低 | 高 |
| **速度** | 快 | 較慢 |
| **適用** | 精確匹配 | 語意搜尋 |

**範例：**
```
查詢：「手機電池續航」

關鍵字搜尋：
→ 必須包含「手機」、「電池」、「續航」
→ 沒有「手機」的文件不會出現
→ "battery life" 不會匹配

向量搜尋：
→ 理解「電池壽命」是相似的
→ 理解 "battery life" 是相似的
→ 找到相關的討論
```

---

## 向量資料庫選擇

### 三個主要選項

| 方案 | 優點 | 缺點 | 成本 |
|------|------|------|------|
| **OpenSearch** | AWS 原生、混合搜尋 | 運維負擔 | $60-100/月 |
| **Aurora pgvector** | 熟悉 SQL、便宜 | 效能差、功能少 | $30-50/月 |
| **Pinecone** | 託管、零運維 | 資料隱私問題 | $70/月 |

### OpenSearch vs Pinecone

**OpenSearch（我們選擇）：**
```
優點：
✅ AWS 原生整合
✅ 混合搜尋（關鍵字 + 向量）
✅ 資料留在 AWS
✅ 可自託管或全託管
✅ 功能豐富

缺點：
❌ 運維負擔
❌ 學習曲線陡峭
❌ 最低成本較高
```

**Pinecone：**
```
優點：
✅ 完全託管
✅ 專門為向量優化
✅ 零運維
✅ 效能好

缺點：
❌ 資料在第三方
❌ 廠商鎖定
❌ 成本較高
❌ 無法自託管
```

---

## Embeddings 模型選擇

### 什麼是 Embeddings？

**Embeddings = 文字轉向量的模型**

```
[文字] → [Embeddings Model] → [向量]
```

### AWS Bedrock Embeddings 模型

**Titan Embeddings（Amazon）：**
```
價格：$0.0001 per 1K tokens
維度：1536
優點：便宜、AWS 原生
缺點：品質一般
```

**Cohere Embed（多語言）：**
```
價格：$0.0001 per 1K tokens
維度：1024
優點：多語言支援好
缺點：較新
```

**選擇建議：**
```
英文：Cohere 或 OpenAI
中文：Cohere 或本地模型
多語言：Cohere
成本敏感：Titan
```

---

## RAG 架構設計

### 完整流程

```
[準備階段]
├─ [文件上傳]
├─ [文字分段]
│   → 每段 500-1000 字
├─ [產生 Embeddings]
│   → 呼叫 Bedrock Titan Embed
└─ [儲存到 OpenSearch]
    → 向量 + 原文

[查詢階段]
├─ [用戶問題]
├─ [產生問題的 Embedding]
├─ [向量搜尋]
│   → 找最相似的 K 個段落
└─ [LLM 生成回答]
    → 問題 + K 個段落 → Claude
```

### 關鍵決策

**1. 分段策略**
```
小段落（200 字）：
✅ 精確匹配
❌ 缺少上下文

大段落（2000 字）：
✅ 有上下文
❌ 不精確

最佳：500-1000 字
```

**2. 檢索數量（K）**
```
K=1：最精確，但可能資訊不足
K=3：平衡（推薦）
K=5：資訊豐富，但可能雜訊多
```

**3. 相似度閾值**
```
Threshold = 0.7
→ 相似度 < 0.7 的文件不採用
→ 避免不相關的資訊
```

---

## 實作範例

### 1. 建立 Embeddings

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def create_embedding(text):
    """使用 Bedrock Titan 產生 Embeddings"""
    body = json.dumps({
        "inputText": text
    })

    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=body
    )

    result = json.loads(response['body'].read())
    return result['embedding']

# 範例
text = "AWS Bedrock is a service for building generative AI applications"
embedding = create_embedding(text)
print(f"Vector dimension: {len(embedding)}")  # 1536
```

### 2. 儲存到 OpenSearch

```python
from opensearchpy import OpenSearch, RequestsHttpConnection

# 連接 OpenSearch
os_client = OpenSearch(
    hosts=[os_endpoint],
    http_auth=aws_auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30
)

# 建立索引
index_name = "documents"

if not os_client.indices.exists(index_name):
    os_client.indices.create(
        index=index_name,
        body={
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "content_vector": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimilality",
                            "engine": "nmslib",
                            "parameters": {"ef_construction": 128, "m": 24}
                        }
                    },
                    "content": {"type": "text"},
                    "metadata": {"type": "object"}
                }
            }
        }
    )

# 儲存文檔
def index_document(doc_id, content, metadata):
    """建立向量索引"""
    # 產生 Embeddings
    embedding = create_embedding(content)

    # 儲存到 OpenSearch
    os_client.index(
        index=index_name,
        id=doc_id,
        body={
            "content_vector": embedding,
            "content": content,
            "metadata": metadata
        }
    )
```

### 3. 向量搜尋

```python
def search_similar(query, k=3):
    """搜尋相似的文檔"""
    # 產生查詢向量
    query_embedding = create_embedding(query)

    # KNN 搜尋
    response = os_client.search(
        index=index_name,
        body={
            "size": k,
            "query": {
                "knn": {
                    "content_vector": {
                        "vector": query_embedding,
                        "k": k
                    }
                }
            }
        }
    )

    # 返回結果
    results = []
    for hit in response['hits']['hits']:
        results.append({
            'content': hit['_source']['content'],
            'score': hit['_score'],
            'metadata': hit['_source']['metadata']
        })

    return results
```

### 4. RAG 查詢

```python
def rag_query(question):
    """RAG 查詢流程"""
    # 1. 檢索相關文檔
    docs = search_similar(question, k=3)

    # 2. 建構提示
    context = "\n\n".join([doc['content'] for doc in docs])

    prompt = f"""
Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:
"""

    # 3. 呼叫 LLM
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-1-20240229-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        })
    )

    result = json.loads(response['body'].read())
    return {
        'answer': result['content'][0]['text'],
        'sources': [doc['metadata'] for doc in docs]
    }
```

---

## 成本分析

### OpenSearch 成本

```
最小配置：
→ t3.medium.search.medium × 2
→ $0.056/hour × 2 × 24 × 30 = $80/月

資料傳輸：
→ 100GB/month = $9/月

總計：~$90/月

加上 EBS、備份等：~$100-120/月
```

### Embeddings 成本

```
Titan Embeddings：
$0.0001 per 1K tokens

範例：10,000 個段落，每個 500 字（~400 tokens）
→ 10K × 400 = 4M tokens
→ 4M × $0.0001 / 1K = $0.40（一次性）

查詢：
→ 1000 查詢/月 × 50 字 = 50K tokens
→ 50K × $0.0001 / 1K = $0.005/月

總計：可以忽略
```

---

## 最佳實踐

### 1. 分段策略

```python
def chunk_text(text, max_length=1000):
    """智能分段"""
    sentences = text.split('。')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence + "。"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "。"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
```

### 2. 元資料過濾

```python
def search_with_filter(query, category=None):
    """結合向量和元資料過濾"""
    query_embedding = create_embedding(query)

    body = {
        "size": 5,
        "query": {
            "bool": {
                "must": [
                    {
                        "knn": {
                            "content_vector": {
                                "vector": query_embedding,
                                "k": 10
                            }
                        }
                    }
                ],
                "filter": []
            }
        }
    }

    # 加入元資料過濾
    if category:
        body["query"]["bool"]["filter"].append({
            "term": {"metadata.category": category}
        })

    return os_client.search(index=index_name, body=body)
```

### 3. 混合搜尋

```python
def hybrid_search(query):
    """結合關鍵字和向量搜尋"""
    query_embedding = create_embedding(query)

    response = os_client.search(
        index=index_name,
        body={
            "query": {
                "hybrid": {
                    "queries": [
                        {
                            "match": {"content": query}
                        },
                        {
                            "knn": {
                                "content_vector": {
                                    "vector": query_embedding,
                                    "k": 10
                                }
                            }
                        }
                    ]
                }
            }
        }
    )

    return response
```

---

## 檢核問題

**在繼續之前，請問自己：**

**概念理解：**
- [ ] 我能解釋向量搜尋的原理嗎？
- [ ] 我知道 RAG 架構的價值嗎？
- [ ] 我理解 Embeddings 的作用嗎？

**技術選擇：**
- [ ] 我能比較 OpenSearch vs Pinecone 嗎？
- [ ] 我知道如何選擇 Embeddings 模型嗎？
- [ ] 我理解分段策略的重要性嗎？

**實作能力：**
- [ ] 我能實作向量搜尋嗎？
- [ ] 我知道如何設計 RAG 流程嗎？
- [ ] 我能優化檢索品質嗎？

---

## 下一階段

完成 Stage 4 後，你會理解：
- ✅ 向量資料庫的原理
- ✅ RAG 架構的設計
- ✅ OpenSearch 的使用
- ✅ Embeddings 的產生和應用
- ✅ 混合搜尋策略

**下一階段：** Autonomous Agent（自主 Agent）
