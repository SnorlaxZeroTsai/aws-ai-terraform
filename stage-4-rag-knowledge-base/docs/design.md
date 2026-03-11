# Stage 4: RAG Knowledge Base - Design Document

## Overview

This document outlines the design decisions and architecture for Stage 4 of the AWS AI Terraform Learning Roadmap: Retrieval-Augmented Generation (RAG) Knowledge Base.

**Goal**: Build a production-grade RAG system that demonstrates semantic search and knowledge injection for AI applications.

**Tech Stack**:
- OpenSearch Service (Vector Engine)
- AWS Bedrock (Embeddings + LLM)
- AWS Lambda (Python)
- AWS S3 (Document Storage)
- AWS API Gateway

---

## Architecture Decisions

### 1. Vector Database Selection

#### Decision: OpenSearch Service

**Options Considered**:
| Solution | Pros | Cons | Cost |
|----------|------|------|------|
| **OpenSearch** | AWS native, scalable, hybrid search | Operational overhead | Instance-based (~$60-100/month) |
| **Aurora pgvector** | Familiar SQL, lower cost | Poor performance, limited features | Usage-based (~$30-50/month) |
| **Pinecone** | Fully managed, zero ops | Data residency concerns | Index-based (~$70/month) |

**Rationale for OpenSearch**:
✅ **AWS Native Integration**: Seamless with Lambda, VPC, IAM
✅ **Hybrid Search**: Combines keyword + vector search
✅ **Scalability**: Auto-scaling, multi-AZ support
✅ **Feature Rich**: KNN, aggregations, monitoring
✅ **Data Residency**: Stays within AWS region

❌ **Cons**:
- Operational overhead (configuration, updates)
- Minimum instance requirements (cost for small deployments)
- Steeper learning curve than managed alternatives

**Mitigation**:
- Use AWS-managed OpenSearch Service (not self-hosted)
- Start with t3.medium instances for cost optimization
- Use CloudWatch for monitoring and alerting

---

### 2. Embedding Model Selection

#### Decision: Amazon Titan Embeddings v1

**Options**:
| Model | Dimension | Cost | Performance |
|-------|-----------|------|-------------|
| **Titan v1** | 1536 | Low | Good general purpose |
| Titan v2 | 1024 | Medium | Better multilingual |
| Cohere Embed | 1024 | Medium | Good for retrieval |

**Rationale**:
✅ **Lowest Cost**: $0.0001 per 1K tokens
✅ **AWS Native**: No external API calls
✅ **Good Performance**: 1536 dimensions for rich representations
✅ **Availability**: Available in all AWS regions

---

### 3. LLM Selection

#### Decision: Claude 3 Sonnet via Bedrock

**Options**:
| Model | Cost | Context | Strength |
|-------|------|---------|----------|
| **Claude 3 Sonnet** | Medium | 200K | Balanced quality/speed |
| Claude 3 Haiku | Low | 200K | Fast, simple tasks |
| Claude 3 Opus | High | 200K | Best quality |

**Rationale**:
✅ **Balanced Performance**: Good quality at reasonable cost
✅ **Large Context**: 200K tokens for complex RAG
✅ **AWS Integration**: Native Bedrock support
✅ **Reliable**: Consistent performance

---

### 4. Chunking Strategy

#### Decision: Hybrid Approach (Configurable)

**Strategies Implemented**:

1. **Fixed-Size Chunking**
   - Simple, predictable
   - May break semantic boundaries
   - Use case: General documents

2. **Semantic Chunking**
   - Preserves sentence boundaries
   - Better context coherence
   - Use case: Structured documents

3. **Hybrid Chunking**
   - Paragraph-aware + fixed-size fallback
   - Best of both approaches
   - Use case: Mixed content types

**Configuration**:
```python
chunk_size = 1000       # Target chunk size in characters
chunk_overlap = 200     # Overlap between chunks
```

**Rationale**:
- Hybrid provides flexibility for different document types
- Configurable allows optimization per use case
- Overlap ensures context continuity

---

### 5. Deployment Architecture

#### Decision: Serverless (Lambda + API Gateway)

**Alternatives**:
| Approach | Pros | Cons | Cost |
|----------|------|------|------|
| **Serverless** | Auto-scale, pay-per-use | Cold starts, limits | Lowest |
| ECS Fargate | Consistent performance | Higher base cost | Medium |
| EC2 | Full control | Operational overhead | Highest |

**Rationale**:
✅ **Cost Effective**: Pay only when processing
✅ **Auto-scaling**: Handles variable load
✅ **Zero Operations**: No servers to manage
✅ **Quick Deployment**: Fast iteration

**Limitations**:
- Lambda: 15 min timeout, 6MB payload
- API Gateway: 29s timeout, $3.50/M requests
- Cold starts: 1-3s initial latency

**Mitigation**:
- Use Lambda provisioned concurrency if needed (cost trade-off)
- Implement caching for frequent queries
- Optimize Lambda package size

---

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                        API Gateway                          │
│                   (REST API: /search)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Lambda Functions                         │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Search Handler  │        │  Index Handler   │          │
│  │  (RAG Pipeline)  │        │  (Doc Processing)│          │
│  └────────┬─────────┘        └────────┬─────────┘          │
└───────────┼──────────────────────────┼──────────────────────┘
            │                          │
            ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Bedrock    │  │  OpenSearch  │  │     S3       │     │
│  │  Embeddings  │  │  Vector DB   │  │  Documents   │     │
│  │  + Claude    │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Indexing Flow
```
Document Upload → S3 Event → Lambda Index Handler
                                ↓
                        Chunking Strategy
                                ↓
                     Embedding Generation (Bedrock)
                                ↓
                        OpenSearch Index
```

#### Query Flow
```
User Query → API Gateway → Lambda Search Handler
                                ↓
                     Embedding Generation (Bedrock)
                                ↓
                      Vector Search (OpenSearch)
                                ↓
                     Prompt Assembly (Context + Query)
                                ↓
                      LLM Generation (Bedrock Claude)
                                ↓
                            Response
```

---

## Cost Analysis

### Monthly Cost Estimate (Dev Environment)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **OpenSearch** | 2x t3.medium.search, 20GB EBS | ~$96 |
| **Lambda** | 100K invocations, 1GB-s | ~$2 |
| **API Gateway** | 100K requests | ~$0.35 |
| **S3** | 10GB storage, 100K requests | ~$0.50 |
| **Bedrock Embeddings** | 1M tokens | ~$0.10 |
| **Bedrock Claude** | 100K input + 500K output tokens | ~$1.75 |
| **CloudWatch** | Logs, metrics | ~$2 |
| **Data Transfer** | 10GB out | ~$0.85 |
| **Total** | | **~$104** |

### Production Estimate (10x Load)
- OpenSearch: t3.large x 3 nodes = ~$250/month
- Lambda: 1M invocations = ~$20/month
- Bedrock: 10M tokens = ~$17.50/month
- **Total**: ~$290/month

### Cost Optimization Strategies
1. **OpenSearch**: Use Reserved Instances for 1+ year commitments (30% savings)
2. **Lambda**: Optimize memory/timeout, use provisioned concurrency sparingly
3. **Bedrock**: Cache embeddings, use smaller models for simple queries
4. **S3**: Enable lifecycle policies for old documents

---

## Security Considerations

### 1. VPC Isolation
- OpenSearch deployed in private subnets
- Lambda functions in VPC with ENIs
- No public internet access to data plane

### 2. Access Control
- IAM roles for Lambda (least privilege)
- API Gateway authorization (can add API keys/Cognito)
- S3 bucket policies restrict access

### 3. Data Protection
- OpenSearch encryption at rest
- S3 server-side encryption
- TLS for all data in transit

### 4. Secrets Management
- Environment variables for non-sensitive config
- AWS Secrets Manager for sensitive data (if needed)
- No hardcoded credentials

---

## Monitoring & Observability

### Metrics to Track
1. **Performance**:
   - Lambda invocation duration
   - OpenSearch query latency
   - End-to-end query latency

2. **Reliability**:
   - Error rates (Lambda, Bedrock, OpenSearch)
   - Retry counts
   - Failed document indexing

3. **Usage**:
   - Query volume
   - Document count
   - Average chunk size

### Logging
- CloudWatch Logs for Lambda
- OpenSearch slow logs
- S3 access logs

### Alerts
- Lambda error rate > 5%
- OpenSearch cluster health = yellow/red
- Bedrock throttling errors

---

## Limitations & Considerations

### Technical Limitations
1. **OpenSearch**:
   - Minimum 2 nodes for production
   - EBS volumes cannot be shrunk
   - Schema changes require index recreation

2. **Lambda**:
   - 15-minute timeout limit
   - 6MB payload limit
   - 50MB deployment package limit

3. **Bedrock**:
   - Rate limits (throttling)
   - Model availability varies by region
   - No fine-tuning for embeddings

### Operational Considerations
1. **Scalability**:
   - OpenSearch: Auto-scales within instance type
   - Lambda: Auto-scales to 1000 concurrent
   - Need to monitor capacity limits

2. **Data Management**:
   - No automatic cleanup of old embeddings
   - Need to implement document versioning
   - Backup strategy for OpenSearch

3. **Cost Management**:
   - Monitor Bedrock token usage
   - Set up billing alerts
   - Implement cost optimization

---

## Success Criteria

### Functional Requirements
✅ Index documents from S3 automatically
✅ Perform semantic search on indexed content
✅ Generate answers using retrieved context
✅ Support multiple chunking strategies
✅ Handle concurrent queries

### Non-Functional Requirements
✅ Query latency < 10 seconds (P95)
✅ Availability > 99% (excluding planned maintenance)
✅ Cost < $150/month for dev environment
✅ Security: VPC isolation, encryption at rest

### Learning Outcomes
✅ Understand RAG architecture
✅ Experience with vector databases
✅ Bedrock integration patterns
✅ Serverless design trade-offs

---

**Document Version**: 1.0
**Last Updated**: 2026-03-12
**Status**: Implementation Complete
