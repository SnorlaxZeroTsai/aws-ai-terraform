# Stage 4: RAG Knowledge Base - Technical Architecture

## System Overview

The RAG Knowledge Base is a serverless system that enables semantic search and question-answering over document collections using vector embeddings and large language models.

### Core Components

1. **Document Storage**: S3 bucket for raw documents
2. **Vector Database**: OpenSearch Service with Vector Engine
3. **Embedding Service**: AWS Bedrock (Titan Embeddings)
4. **LLM Service**: AWS Bedrock (Claude 3 Sonnet)
5. **Compute Layer**: AWS Lambda functions
6. **API Layer**: AWS API Gateway

---

## Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   S3 Bucket     │
                                    │  (Documents)    │
                                    └────────┬────────┘
                                             │
                                             │ s3:ObjectCreated
                                             ▼
┌──────────────┐                    ┌──────────────────┐
│              │                    │   Lambda: Index  │
│  API Gateway │◄───────────────────┤   Handler        │
│   /search    │                    │                  │
└──────┬───────┘                    └────────┬─────────┘
       │                                     │
       │ POST /search                        │
       ▼                                     ▼
┌──────────────────┐               ┌──────────────────┐
│   Lambda: Search │               │   Bedrock:       │
│   Handler        │               │   Embeddings     │
└────────┬─────────┘               └──────────────────┘
         │
         ├─────────────┬─────────────┐
         ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Bedrock  │  │OpenSearch│  │CloudWatch│
  │  Claude  │  │  Vector  │  │  Logs    │
  └──────────┘  └──────────┘  └──────────┘
```

---

## API Endpoints

### 1. Search Endpoint

**URL**: `POST /search`

**Description**: Performs RAG query with context retrieval and LLM generation

**Request Body**:
```json
{
  "query": "What is machine learning?",
  "max_results": 5,
  "search_type": "vector",
  "template_type": "qa",
  "include_chunks": true,
  "retrieval_only": false,
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous answer"
    }
  ]
}
```

**Parameters**:
- `query` (required): User question or search query
- `max_results` (optional): Number of chunks to retrieve (default: 5)
- `search_type` (optional): "vector" or "hybrid" (default: "vector")
- `template_type` (optional): "qa", "summary", "explanation", "conversational" (default: "qa")
- `include_chunks` (optional): Include retrieved chunks in response (default: true)
- `retrieval_only` (optional): Skip LLM generation, return only chunks (default: false)
- `conversation_history` (optional): Array of previous conversation turns

**Response**:
```json
{
  "query": "What is machine learning?",
  "answer": "Machine learning is the study of computer algorithms...",
  "chunks": [
    {
      "id": "doc1#chunk_0",
      "score": 0.95,
      "content": "Machine learning is...",
      "metadata": {
        "source": "doc1.txt",
        "chunk_id": "chunk_0"
      }
    }
  ],
  "chunk_count": 5,
  "search_type": "vector"
}
```

**Error Response**:
```json
{
  "error": "Error message description"
}
```

---

## Data Flow

### Indexing Pipeline

```
1. Document Upload
   └─> User uploads document to S3 bucket

2. S3 Event Trigger
   └─> S3 publishes ObjectCreated event

3. Lambda Index Handler
   └─> Invoked with S3 event details

4. Document Download
   └─> Lambda downloads document from S3

5. Chunking
   └─> Document split into chunks using hybrid strategy
   ├─> Paragraph-aware chunking
   ├─> Fixed-size fallback for long paragraphs
   └─> Configurable overlap (200 chars default)

6. Embedding Generation
   └─> Each chunk sent to Bedrock Titan Embeddings
   └─> 1536-dimensional vector returned per chunk

7. Vector Indexing
   └─> Chunks indexed in OpenSearch with embeddings
   └─> k-NN index enables fast similarity search

8. Completion
   └─> Lambda returns success/failure count
```

### Query Pipeline

```
1. User Query
   └─> POST /search with query text

2. API Gateway
   └─> Routes to Lambda Search Handler

3. Query Embedding
   └─> Query text sent to Bedrock Titan Embeddings
   └─> 1536-dimensional query vector generated

4. Vector Search
   └─> OpenSearch performs k-NN similarity search
   └─> Returns top K most similar chunks (default: 5)

5. Context Assembly
   └─> Retrieved chunks formatted as context
   └─> Chunks ordered by relevance score

6. Prompt Construction
   └─> Context + query assembled into prompt
   └─> Template based on template_type parameter

7. LLM Generation
   └─> Prompt sent to Bedrock Claude 3 Sonnet
   └─> Generated answer returned

8. Response Formatting
   └─> Answer + metadata packaged in JSON
   └─> Returned via API Gateway
```

---

## Component Details

### Lambda Functions

#### Index Handler
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)
- **Trigger**: S3 ObjectCreated events
- **Environment Variables**:
  - `OPENSEARCH_DOMAIN_ENDPOINT`: OpenSearch endpoint URL
  - `BEDROCK_EMBEDDING_MODEL`: Model ID for embeddings
  - `CHUNK_SIZE`: Target chunk size (default: 1000)
  - `CHUNK_OVERLAP`: Chunk overlap (default: 200)
  - `VECTOR_DIMENSION`: Embedding dimension (default: 1536)
  - `LOG_LEVEL`: Logging level (default: INFO)

#### Search Handler
- **Runtime**: Python 3.11
- **Memory**: 256 MB
- **Timeout**: 60 seconds
- **Trigger**: API Gateway POST /search
- **Environment Variables**:
  - `OPENSEARCH_DOMAIN_ENDPOINT`: OpenSearch endpoint URL
  - `BEDROCK_EMBEDDING_MODEL`: Model ID for embeddings
  - `BEDROCK_LLM_MODEL`: Model ID for LLM
  - `MAX_RESULTS`: Default max results (default: 5)
  - `VECTOR_DIMENSION`: Embedding dimension (default: 1536)
  - `LOG_LEVEL`: Logging level (default: INFO)

### OpenSearch Configuration

#### Index Schema
```json
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 100
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text"
      },
      "embedding": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 256,
            "m": 24
          }
        }
      },
      "metadata": {
        "type": "object",
        "properties": {
          "source": {"type": "keyword"},
          "chunk_id": {"type": "keyword"},
          "doc_id": {"type": "keyword"},
          "timestamp": {"type": "date"}
        }
      }
    }
  }
}
```

#### Search Types

1. **Vector Search** (k-NN):
   - Pure similarity search using query embedding
   - Cosine similarity metric
   - Returns top K most similar chunks

2. **Hybrid Search**:
   - Combines keyword search + vector search
   - Keyword match boost: 1.0
   - Vector similarity boost: 2.0
   - Better for queries with specific terms

### Chunking Strategies

#### Fixed-Size Chunking
```
Algorithm:
1. Split text into chunks of fixed size
2. Add overlap between consecutive chunks
3. Create metadata with position info

Use Case: General documents, predictable chunk sizes
```

#### Semantic Chunking
```
Algorithm:
1. Split text into sentences
2. Group sentences into chunks up to target size
3. Split long sentences if needed

Use Case: Structured documents, preserve context
```

#### Hybrid Chunking (Default)
```
Algorithm:
1. Split text into paragraphs
2. Add paragraphs to chunks until target size
3. Use fixed-size chunking for long paragraphs

Use Case: Mixed content, best of both approaches
```

### Prompt Templates

#### Q&A Template
```
You are a helpful AI assistant that answers questions based on the provided context.

Context:
[Source 1] (Relevance: 0.95)
Chunk content...

[Source 2] (Relevance: 0.88)
Chunk content...

Question: {query}

Instructions:
1. Answer using ONLY the provided context
2. If insufficient information, say so
3. Be concise and direct
4. Cite specific parts of context

Answer:
```

#### Conversational Template
```
You are a helpful AI assistant having a conversation.

Conversation History:
User: Previous question
Assistant: Previous answer

Context:
[Chunks...]

Current User Question: {query}

Instructions:
1. Respond naturally to current question
2. Use context and conversation history
3. Be conversational but accurate

Response:
```

---

## Deployment Architecture

### Network Configuration

```
VPC (from Stage 1)
├── Public Subnets
│   └── (Not used by Stage 4)
└── Private Subnets
    ├── OpenSearch Nodes (2x t3.medium)
    └── Lambda Functions
        └── ENIs in private subnets
```

### Security Groups

#### Lambda Security Group
- **Egress**: All traffic (0.0.0.0/0)
- **Ingress**: None (stateless)

#### OpenSearch Security Group
- **Ingress**: 443 from Lambda Security Group
- **Egress**: All traffic (0.0.0.0/0)

### IAM Roles

#### Lambda Execution Role
**Policies**:
- AWSLambdaBasicExecutionRole (CloudWatch logs)
- AWSLambdaVPCAccessExecutionRole (VPC access)
- Bedrock access (InvokeModel)
- S3 access (GetObject, PutObject, DeleteObject)
- OpenSearch access (ES HTTP operations)

---

## Error Handling

### Retry Strategy

| Operation | Max Retries | Backoff | Fallback |
|-----------|-------------|---------|----------|
| Bedrock Embeddings | 3 | Exponential | Return zero vector |
| Bedrock Claude | 3 | Exponential | Return error message |
| OpenSearch Index | 3 | Exponential | Log error, continue |
| OpenSearch Search | 2 | Linear | Return empty results |
| S3 Download | 3 | Exponential | Skip document |

### Error Responses

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "details": {
    "component": "bedrock/opensearch/s3",
    "retryable": true/false
  }
}
```

---

## Performance Characteristics

### Latency Breakdown

| Operation | Typical Duration | P95 Duration |
|-----------|------------------|--------------|
| Query Embedding | 500ms | 1s |
| Vector Search | 200ms | 500ms |
| LLM Generation | 2-5s | 8s |
| Total End-to-End | 3-6s | 10s |

### Throughput

| Component | Max Concurrent | Requests/Second |
|-----------|----------------|-----------------|
| Lambda | 1000 | 100+ |
| OpenSearch | - | 50+ |
| Bedrock | - | 100+ (regional limit) |

### Scalability Limits

- **Lambda**: 1000 concurrent executions (soft limit, can increase)
- **OpenSearch**: Scales within instance type (t3.medium → t3.large → t3.xlarge)
- **API Gateway**: 10,000 requests/second (default limit)
- **Bedrock**: Regional rate limits (can request increase)

---

## Monitoring

### CloudWatch Metrics

#### Lambda
- `Duration`: Function execution time
- `Errors`: Invocation errors
- `Invocations`: Total invocations
- `Throttles`: Throttled invocations

#### OpenSearch
- `CPUUtilization`: Cluster CPU usage
- `FreeStorageSpace`: Available disk space
- `ClusterStatus.green/red/yellow`: Cluster health
- `SearchLatency`: Query latency

#### Custom Metrics
- `IndexingSuccessRate`: Percentage of successful document indexing
- `QueryLatency`: End-to-end query latency
- `RetrievedChunks`: Average number of chunks retrieved

### Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| Lambda Error Rate | > 5% | SNS notification |
| OpenSearch Yellow/Red | Status != green | SNS notification |
| High Query Latency | P95 > 10s | SNS notification |
| Bedrock Throttling | Any throttle | SNS notification |

---

## Disaster Recovery

### Backup Strategy

1. **OpenSearch**:
   - Automated snapshots every 24 hours
   - Retention: 7 days
   - Manual snapshots before major changes

2. **S3**:
   - Versioning enabled
   - Cross-region replication (optional)

3. **Infrastructure**:
   - Terraform state backed up
   - Infrastructure as Code enables recreation

### Recovery Procedures

1. **OpenSearch Failure**:
   - Restore from latest snapshot
   - Reindex from S3 documents

2. **Region Failure**:
   - Deploy to secondary region
   - DNS failover

3. **Data Corruption**:
   - S3 versioning for rollback
   - Reprocess documents from S3

---

**Document Version**: 1.0
**Last Updated**: 2026-03-12
**Status**: Implementation Complete
