# Stages 2-6: Implementation Overview

> **For agentic workers:** This document provides implementation overviews for stages 2-6. Detailed plans will be created as needed.

**Goal:** Continue the learning roadmap with AI-focused projects, building on the Terraform foundation.

---

## Stage 2: AI Chatbot Service

### Learning Objectives
- Serverless architecture with Lambda and API Gateway
- LLM API integration (Bedrock Claude)
- Environment secrets management
- CloudWatch monitoring

### Architecture
```
User → API Gateway → Lambda (Chat Handler) → Bedrock (Claude)
                                    ↓
                              CloudWatch Logs
                                    ↓
                              Secrets Manager (API keys)
```

### Key Files to Create
```
stage-2-ai-chatbot/
├── terraform/
│   ├── lambda/
│   │   └── main.tf                    # Lambda function, IAM role
│   ├── api_gateway/
│   │   └── main.tf                    # REST API, resources, methods
│   ├── secrets_manager/
│   │   └── main.tf                    # LLM API keys
│   └── cloudwatch/
│       └── main.tf                    # Log groups, alarms
├── src/
│   ├── handlers/
│   │   └── chat.py                    # Lambda entry point
│   ├── services/
│   │   └── llm_service.py             # Bedrock Claude client
│   └── prompts/
│       └── chat_templates.py          # System prompts
├── docs/
│   └── design.md                      # Serverless vs containers analysis
└── tests/
    └── api_tests.py                   # Integration tests
```

### Implementation Steps Overview
1. Create Lambda function with Python runtime
2. Implement chat handler with message history
3. Create API Gateway REST API with /chat endpoint
4. Configure Bedrock integration
5. Add authentication (API keys or Cognito)
6. Implement CloudWatch logging
7. Create deployment scripts

### Key Architecture Decisions
- **Why Lambda vs ECS?** (cost, scale, ops)
- **Why API Gateway vs ALB?** (managed vs control)
- **Cold start mitigation strategies**

---

## Stage 3: Document Analysis System

### Learning Objectives
- Asynchronous event-driven architecture
- S3 for object storage
- AWS Textract for document processing
- DynamoDB for NoSQL data
- SQS/SNS for messaging

### Architecture
```
User → S3 Upload → S3 Event Trigger → Lambda (Textract Handler)
                                         ↓
                                    Textract API
                                         ↓
                                    DynamoDB
                                         ↓
                                    SNS Notification
```

### Key Files to Create
```
stage-3-document-analysis/
├── terraform/
│   ├── s3/
│   │   └── main.tf                    # Bucket, event notifications
│   ├── lambda/
│   │   └── main.tf                    # Processing functions
│   ├── textract/
│   │   └── main.tf                    # Textract permissions
│   ├── dynamodb/
│   │   └── main.tf                    # Tables, GSI, LSIs
│   └── sns_sqs/
│       └── main.tf                    # Topics, queues
├── src/
│   ├── handlers/
│   │   ├── upload_handler.py          # S3 event handler
│   │   └── analysis_handler.py        # Textract orchestration
│   ├── services/
│   │   └── textract_service.py        # Textract client wrapper
│   └── models/
│       └── document.py                # Document data model
├── docs/
│   └── design.md                      # Async architecture patterns
└── tests/
    └── document_pipeline_test.py      # E2E tests
```

### Implementation Steps Overview
1. Create S3 bucket with versioning
2. Configure S3 event notifications to Lambda
3. Implement Textract integration
4. Design DynamoDB schema (partition keys)
5. Create SQS queue for async processing
6. Add SNS for completion notifications
7. Implement retry logic with dead letter queue

### Key Architecture Decisions
- **Why SQS for async?** (decoupling, retry, throttling)
- **DynamoDB schema design** (access patterns)
- **Error handling strategies**

---

## Stage 4: RAG Knowledge Base

### Learning Objectives
- Vector embeddings and similarity search
- OpenSearch Vector Engine
- RAG (Retrieval-Augmented Generation)
- Chunking strategies
- Semantic search

### Architecture
```
Documents → Chunking → Embedding Generation → OpenSearch Vector Store
                                                      ↓
Query → Embedding → Vector Search → Retrieved Chunks → LLM Context
                                                        ↓
                                                    RAG Response
```

### Key Files to Create
```
stage-4-rag-knowledge-base/
├── terraform/
│   ├── opensearch/
│   │   └── main.tf                    # Domain, access policies
│   ├── lambda/
│   │   └── main.tf                    # Embedding, search functions
│   ├── s3/
│   │   └── main.tf                    # Document storage
│   └── bedrock/
│       └── main.tf                    # Embedding model access
├── src/
│   ├── handlers/
│   │   ├── index_handler.py           # Document indexing
│   │   └── search_handler.py          # RAG search
│   ├── services/
│   │   ├── embedding_service.py       # Bedrock embeddings
│   │   ├── opensearch_service.py      # Vector search client
│   │   └── rag_service.py             # RAG orchestration
│   ├── chunking/
│   │   ├── strategies.py              # Chunk implementations
│   │   └── evaluation.py              # Chunk quality metrics
│   └── prompts/
│       └── rag_templates.py           # RAG prompt templates
├── docs/
│   └── design.md                      # Vector DB comparison
└── tests/
    ├── rag_test.py                    # RAG E2E tests
    └── chunking_test.py               # Chunk evaluation
```

### Implementation Steps Overview
1. Deploy OpenSearch domain with vector support
2. Implement chunking strategies (fixed, semantic, hybrid)
3. Create embedding generation pipeline
4. Build vector index with appropriate k-NN settings
5. Implement RAG search with relevance scoring
6. Add prompt engineering for context injection
7. Evaluate retrieval quality

### Key Architecture Decisions
- **Vector DB: OpenSearch vs Pinecone vs pgvector**
- **Chunking strategy trade-offs**
- **Embedding model selection**
- **Reranking strategies**

---

## Stage 5: Autonomous Agent

### Learning Objectives
- ReAct (Reasoning + Acting) pattern
- Tool calling and function registration
- Step Functions for orchestration
- Memory management (short/long term)
- Complex task decomposition

### Architecture
```
User Request → Agent Core → ReAct Loop
                               ↓
                    ┌──────────┴──────────┐
                    ↓                     ↓
              Tool Registry         Memory Store
                    ↓                     ↓
              Tool Execution        Context Retrieval
                    ↓                     ↓
              Step Functions ────────────┘
                    ↓
              Result Aggregation
```

### Key Files to Create
```
stage-5-autonomous-agent/
├── terraform/
│   ├── step_functions/
│   │   └── main.tf                    # State machine, IAM
│   ├── lambda/
│   │   └── main.tf                    # Agent core logic
│   ├── dynamodb/
│   │   └── main.tf                    # Memory storage
│   └── s3/
│       └── main.tf                    # Tool definitions
├── src/
│   ├── agent/
│   │   ├── core.py                    # Agent base class
│   │   ├── reasoning.py               # ReAct implementation
│   │   └── memory.py                  # Memory management
│   ├── tools/
│   │   ├── registry.py                # Tool registration
│   │   ├── base_tool.py               # Tool interface
│   │   └── implementations/
│   │       ├── search_tool.py         # Example: Web search
│   │       ├── query_tool.py          # Example: Database query
│   │       └── file_tool.py           # Example: File operations
│   └── workflows/
│       └── task_flow.asl.json         # Step Functions workflow
├── docs/
│   └── design.md                      # Orchestration patterns
└── tests/
    ├── agent_test.py                  # Agent behavior tests
    └── tool_test.py                   # Tool tests
```

### Implementation Steps Overview
1. Design tool interface and registry
2. Implement ReAct reasoning loop
3. Create sample tools (search, query, file)
4. Build Step Functions workflow
5. Implement memory systems (conversation, episodic, semantic)
6. Add tool output parsing and validation
7. Implement error handling and recovery

### Key Architecture Decisions
- **Orchestration: Step Functions vs custom vs LangChain**
- **Memory architecture design**
- **Tool schema design**
- **Multi-step reasoning strategies**

---

## Stage 6: AI Agent Platform

### Learning Objectives
- Microservices architecture
- Multi-agent collaboration
- API composition and orchestration
- Container orchestration with ECS
- Distributed tracing with X-Ray
- Comprehensive monitoring

### Architecture
```
                            API Gateway
                                  ↓
        ┌─────────────────────────┼─────────────────────────┐
        ↓                         ↓                         ↓
   Agent Service          Chatbot Service           RAG Service
   (ECS Fargate)         (Lambda)                  (Lambda)
        ↓                         ↓                         ↓
        └─────────────────────────┼─────────────────────────┘
                                  ↓
                         Shared Services Layer
                   (DynamoDB, S3, OpenSearch, etc.)
                                  ↓
                         Observability (X-Ray, CW)
```

### Key Files to Create
```
stage-6-agent-platform/
├── terraform/
│   ├── api_gateway/
│   │   └── main.tf                    # Unified API entry
│   ├── ecs/
│   │   └── main.tf                    # ECS cluster, services
│   ├── lambda/
│   │   └── main.tf                    # Serverless components
│   ├── xray/
│   │   └── main.tf                    # Distributed tracing
│   └── cloudwatch/
│       └── main.tf                    # Dashboards, alarms
├── src/
│   ├── platform/
│   │   ├── api/
│   │   │   ├── gateway.py             # API Gateway handler
│   │   │   └── routes.py              # Route definitions
│   │   ├── auth/
│   │   │   └── authorizer.py          # JWT/Cognito auth
│   │   └── orchestrator.py            # Agent coordination
│   ├── agents/                        # Integrated from previous stages
│   │   ├── chatbot/
│   │   ├── rag/
│   │   └── autonomous/
│   └── shared/
│       ├── config.py
│       ├── middleware.py
│       └── utils.py
├── docker/
│   └── Dockerfile                     # Container definition
├── docs/
│   └── design.md                      # Platform architecture
├── scripts/
│   └── deploy.sh                      # Deployment automation
└── tests/
    └── platform_test.py               # Integration tests
```

### Implementation Steps Overview
1. Design unified API gateway with routes to all services
2. Containerize agent service for ECS
3. Implement authentication and authorization
4. Set up X-Ray for distributed tracing
5. Create CloudWatch dashboards
6. Implement health checks and circuit breakers
7. Add monitoring and alerting
8. Create deployment pipeline

### Key Architecture Decisions
- **Deployment: All Lambda vs Hybrid (ECS + Lambda) vs EKS**
- **Multi-agent patterns: Hierarchical vs Network vs Pipeline**
- **API Gateway vs ALB vs NLB**
- **Observability strategy**

---

## Common Patterns Across All Stages

### Terraform Module Structure
```hcl
# Every module follows this pattern
modules/
└── <service-name>/
    ├── main.tf          # Resources
    ├── variables.tf     # Inputs
    ├── outputs.tf       # Outputs
    └── versions.tf      # Provider versions (optional)
```

### Python Service Structure
```python
# Consistent service pattern
class ServiceName:
    def __init__(self, config):
        self.config = config
        self.client = self._create_client()

    def execute(self, input_data):
        # Implementation
        pass

    def _create_client(self):
        # AWS client creation
        pass
```

### Testing Strategy
```python
# Standard test structure
def test_unit_behavior():
    # Test specific functionality
    pass

def test_integration():
    # Test with actual AWS services (use moto for local)
    pass

def test_e2e():
    # Full workflow test
    pass
```

---

## Progressive Complexity

| Stage | Primary Focus | Complexity | Lines of Code (approx) |
|-------|---------------|------------|------------------------|
| 1 | Infrastructure | Low | ~500 (Terraform) |
| 2 | Serverless API | Medium | ~800 (Terraform + Python) |
| 3 | Async Processing | Medium | ~1000 |
| 4 | Vector Search | High | ~1500 |
| 5 | Agent Logic | High | ~2000 |
| 6 | Platform Integration | Very High | ~3000 |

---

## Next Steps

1. **Complete Stage 1** (detailed plan available)
2. **Review architecture decisions** before implementing
3. **Document learnings** as you go
4. **Build incrementally** - test each stage before moving on
5. **Monitor costs** - destroy resources when not in use

---

**Overview Created:** 2026-03-10
**Reference:** docs/superpowers/specs/2026-03-10-learning-roadmap-design.md
