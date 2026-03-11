# Stage 4: RAG Knowledge Base - Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Retrieval-Augmented Generation (RAG) system using OpenSearch Vector Engine, Bedrock Embeddings, and Claude, demonstrating semantic search and knowledge injection for AI applications.

**Architecture:** Documents → Chunking → Embeddings → OpenSearch Vector Store → Query → Vector Search → Retrieved Chunks → LLM Context → Response

**Tech Stack:** Terraform, AWS Lambda, OpenSearch Service, Bedrock (Embeddings + Claude), S3, Python 3.11

---

## Chunk 1: Project Setup

### Task 1: Create Directory Structure

**Files:**
- Create: `stage-4-rag-knowledge-base/README.md`
- Create: `stage-4-rag-knowledge-base/.gitignore`
- Create: `stage-4-rag-knowledge-base/requirements.txt`
- Create: `stage-4-rag-knowledge-base/terraform/main.tf`
- Create: `stage-4-rag-knowledge-base/terraform/variables.tf`
- Create: `stage-4-rag-knowledge-base/terraform/outputs.tf`
- Create: `stage-4-rag-knowledge-base/terraform/provider.tf`

- [ ] **Step 1: Create directories**

```bash
mkdir -p stage-4-rag-knowledge-base/terraform/modules/{opensearch,lambda,s3,bedrock}
mkdir -p stage-4-rag-knowledge-base/src/{handlers,services,chunking,prompts,utils}
mkdir -p stage-4-rag-knowledge-base/tests
mkdir -p stage-4-rag-knowledge-base/docs
mkdir -p stage-4-rag-knowledge-base/data/sample_documents
```

- [ ] **Step 2: Create .gitignore** (similar to Stage 2)

- [ ] **Step 3: Create provider.tf**

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "ai-learning-roadmap"
      Stage     = "4-rag-knowledge-base"
      ManagedBy = "Terraform"
    }
  }
}

data "terraform_remote_state" "foundation" {
  backend = "local"
  config = {
    path = "../stage-1-terraform-foundation/terraform/terraform.tfstate"
  }
}
```

- [ ] **Step 4: Create variables.tf**

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "rag-knowledge-base"
}

variable "opensearch_domain_name" {
  description = "OpenSearch domain name"
  type        = string
  default     = "rag-kb"
}

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.medium.search"

  validation {
    condition     = can(regex("^t3\\.(micro|small|medium)\\.search$", var.opensearch_instance_type))
    error_message = "Must be a valid t3.search instance type."
  }
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch data nodes"
  type        = number
  default     = 2

  validation {
    condition     = var.opensearch_instance_count >= 1 && var.opensearch_instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "opensearch_volume_size" {
  description = "EBS volume size per node (GB)"
  type        = number
  default     = 20

  validation {
    condition     = var.opensearch_volume_size >= 10 && var.opensearch_volume_size <= 100
    error_message = "Volume size must be between 10 and 100 GB."
  }
}

variable "embedding_model_id" {
  description = "Bedrock embedding model"
  type        = string
  default     = "amazon.titan-embed-text-v1"

  validation {
    condition     = can(regex("^(amazon\\.titan|cohere\\.embed)", var.embedding_model_id))
    error_message = "Must be a valid Bedrock embedding model."
  }
}

variable "vector_dimension" {
  description = "Embedding vector dimension"
  type        = number
  default     = 1536

  validation {
    condition     = contains([512, 768, 1024, 1536], var.vector_dimension)
    error_message = "Dimension must be valid for chosen model."
  }
}

variable "chunk_size" {
  description = "Default chunk size in characters"
  type        = number
  default     = 1000

  validation {
    condition     = var.chunk_size >= 200 && var.chunk_size <= 4000
    error_message = "Chunk size must be between 200 and 4000."
  }
}

variable "chunk_overlap" {
  description = "Chunk overlap in characters"
  type        = number
  default     = 200

  validation {
    condition     = var.chunk_overlap >= 0 && var.chunk_overlap <= 500
    error_message = "Overlap must be between 0 and 500."
  }
}

variable "top_k_results" {
  description = "Number of chunks to retrieve"
  type        = number
  default     = 5

  validation {
    condition     = var.top_k_results >= 1 && var.top_k_results <= 20
    error_message = "Top K must be between 1 and 20."
  }
}
```

- [ ] **Step 5: Create outputs.tf**

```hcl
output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
}

output "opensearch_dashboard_url" {
  description = "OpenSearch dashboard URL"
  value       = module.opensearch.dashboard_url
}

output "index_function_name" {
  description = "Document indexer function name"
  value       = try(module.lambda.index_function_name, null)
}

output "search_function_name" {
  description = "RAG search function name"
  value       = try(module.lambda.search_function_name, null)
}

output "s3_bucket_name" {
  description = "Documents S3 bucket"
  value       = module.s3.bucket_name
}
```

- [ ] **Step 6: Create requirements.txt**

```bash
cat > stage-4-rag-knowledge-base/requirements.txt << 'EOF'
# AWS SDK
boto3==1.34.84
botocore==1.34.84

# OpenSearch
opensearch-py==2.4.2

# NLP (for chunking)
sentence-transformers==2.3.1
nltk==3.8.1

# Validation
pydantic==2.6.1

# Utilities
python-dotenv==1.0.1
tiktoken==0.5.2

# Testing
pytest==8.0.2
pytest-mock==3.12.0
pytest-cov==4.1.0
EOF
```

- [ ] **Step 7: Create README.md**

```bash
cat > stage-4-rag-knowledge-base/README.md << 'EOF'
# Stage 4: RAG Knowledge Base

## Learning Objectives

After completing this stage, you will be able to:
- [ ] Understand vector embeddings and semantic search
- [ ] Implement Retrieval-Augmented Generation (RAG)
- [ ] Design vector database schemas
- [ ] Choose appropriate chunking strategies
- [ ] Optimize retrieval quality and relevance

## Architecture Overview

```
Documents → Chunking → Embeddings → OpenSearch Vector Store
                                              ↓
Query → Embedding → k-NN Search → Retrieved Chunks
                                              ↓
                                      Context + Query → LLM → Response
```

## Features

- **Document Indexing**: Automatic chunking and embedding
- **Vector Search**: k-NN similarity search
- **Multiple Chunking Strategies**: Fixed, semantic, hybrid
- **RAG Pipeline**: Context injection and generation
- **OpenSearch Dashboard**: Visualize and manage index

## Prerequisites

- Completed Stages 1-2
- AWS Account with Bedrock enabled
- OpenSearch Service enabled in region
- Python 3.11+

## Deployment

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Usage

### Index a Document

```python
from src.services.index_service import IndexService

service = IndexService()
service.index_document(
    content="Your document text here...",
    metadata={"title": "My Document", "author": "AI"}
)
```

### RAG Query

```python
from src.services.rag_service import RAGService

rag = RAGService()
response = rag.query(
    question="What is RAG?",
    top_k=5
)
print(response["answer"])
```

## Chunking Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| Fixed Size | Equal length chunks | General documents |
| Semantic | Sentence boundaries | Structured text |
| Hybrid | Semantic + size limit | Complex documents |
| Recursive | Hierarchical splitting | Long documents |

## RAG Parameters

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| chunk_size | Characters per chunk | 1000-1500 |
| chunk_overlap | Overlap between chunks | 10-20% |
| top_k | Chunks to retrieve | 3-10 |
| temperature | LLM randomness | 0.3-0.7 |

## Cost Estimate

| Resource | Cost |
|----------|------|
| OpenSearch | ~$60-100/month (t3.medium x2) |
| S3 Storage | ~$0.023/GB |
| Lambda | ~$0.20/1M requests |
| Bedrock Embeddings | ~$0.10/1M tokens |
| Bedrock Claude | ~$3/1M input tokens |

**Estimated monthly:** $70-150

## Monitoring

```bash
# Check OpenSearch cluster health
curl -X GET "https://domain-endpoint/_cluster/health"

# View index stats
curl -X GET "https://domain-endpoint/_cat/indices?v"

# Test search
curl -X POST "https://domain-endpoint/rag-docs/_search" \
  -H "Content-Type: application/json" \
  -d '{"query":{"match_all":{}}}'
```

## Cleanup

```bash
cd terraform
terraform destroy
```

## Next Steps

After completing this stage:
1. Experiment with different chunking strategies
2. Evaluate retrieval quality
3. Try reranking strategies
4. Proceed to Stage 5: Autonomous Agent
EOF
```

- [ ] **Step 8: Create Python structure**

```bash
touch stage-4-rag-knowledge-base/src/__init__.py
touch stage-4-rag-knowledge-base/src/handlers/__init__.py
touch stage-4-rag-knowledge-base/src/services/__init__.py
touch stage-4-rag-knowledge-base/src/chunking/__init__.py
touch stage-4-rag-knowledge-base/src/prompts/__init__.py
touch stage-4-rag-knowledge-base/src/utils/__init__.py
```

- [ ] **Step 9: Commit**

```bash
git add stage-4-rag-knowledge-base/
git commit -m "feat: stage-4 initial project structure"
```

---

## Chunk 2: OpenSearch Module

### Task 2: Create OpenSearch Infrastructure

**Files:**
- Create: `stage-4-rag-knowledge-base/terraform/modules/opensearch/main.tf`
- Create: `stage-4-rag-knowledge-base/terraform/modules/opensearch/variables.tf`
- Create: `stage-4-rag-knowledge-base/terraform/modules/opensearch/outputs.tf`

- [ ] **Step 1: Create OpenSearch module**

```hcl
# Security group for OpenSearch
resource "aws_security_group" "opensearch" {
  name_prefix = "${var.domain_name}-"
  description = "Security group for OpenSearch"
  vpc_id      = var.vpc_id

  # HTTPS access from VPC (or restricted CIDR)
  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# OpenSearch domain
resource "aws_opensearch_domain" "this" {
  domain_name    = var.domain_name
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type          = var.instance_type
    instance_count         = var.instance_count
    dedicated_master_type  = var.dedicated_master_enabled ? var.dedicated_master_type : null
    dedicated_master_count = var.dedicated_master_enabled ? 3 : null
    zone_awareness_enabled = var.zone_awareness_enabled
    availability_zone_count = var.zone_awareness_enabled ? 2 : 1
  }

  ebs_options {
    ebs_enabled {
      volume_type = var.volume_type
      volume_size = var.volume_size
      iops        = var.provisioned_iops
      throughput  = var.provisioned_throughput
    }
  }

  # Encrypt at rest
  encrypt_at_rest {
    enabled = var.encrypt_at_rest
  }

  # Node-to-node encryption
  node_to_node_encryption {
    enabled = var.node_to_node_encryption
  }

  # Fine-grained access control
  advanced_security_options {
    enabled                        = var.advanced_security_enabled
    internal_user_database_enabled = var.internal_user_database_enabled

    master_user_options {
      master_user_name     = var.master_username
      master_user_password = var.master_password
    }
  }

  # Network configuration
  vpc_options {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.opensearch.id]
  }

  # Access policies
  access_policies = jsonencode([
    {
      "DomainPermissions": [
        {
          "Principal": {
            "AWS": "*"
          },
          "Action": [
            "es:ESHttp*"
          ],
          "Effect": "Allow",
          "Resource": "arn:aws:es:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/*"
        }
      ],
      "Version": "2017-10-17"
    }
  ])

  # Software update
  domain_endpoint_options {
    enforce_https                   = true
    tls_security_policy             = "Policy-Min-TLS-1-2-2019-07"
    custom_endpoint_enabled         = false
    custom_endpoint_certificate_arn = ""
  }

  # Auto-tune
  auto_tune_options {
    desired_state = "ENABLED"
    maintenance_type = "SCHEDULED"
    maintenance_schedule {
      start_at = jsonencode({
        "duration" = {
          "value" = 2
          "unit" = "HOURS"
        }
        "schedule" = [{
          "duration" = {
            "value" = 2
            "unit" = "HOURS"
          }
          "cron_expression" = "cron:0 2 * * SAT"
        }]
      })
    }
  }

  # Logs
  log_publishing_options {
    cloudwatch_log_group_arn = var.log_publishing_enabled ? aws_cloudwatch_log_group.opensearch[0].arn : null
    enabled                 = var.log_publishing_enabled
    log_type                = "INDEX_SLOW_LOGS"
  }

  tags = var.tags
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "opensearch" {
  count = var.log_publishing_enabled ? 1 : 0

  name              = "/aws/opensearch/${var.domain_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Wait for domain to be created
resource "time_sleep" "wait_for_domain" {
  depends_on = [aws_opensearch_domain.this]

  create_duration = "5m"
}
```

- [ ] **Step 2: Create variables**

```hcl
variable "domain_name" {
  description = "OpenSearch domain name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for OpenSearch"
  type        = list(string)
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access OpenSearch"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "instance_type" {
  description = "Instance type"
  type        = string
  default     = "t3.medium.search"
}

variable "instance_count" {
  description = "Number of data nodes"
  type        = number
  default     = 2
}

variable "volume_type" {
  description = "EBS volume type"
  type        = string
  default     = "gp3"
}

variable "volume_size" {
  description = "EBS volume size (GB)"
  type        = number
  default     = 20
}

variable "provisioned_iops" {
  description = "Provisioned IOPS (for io1/io2)"
  type        = number
  default     = null
}

variable "provisioned_throughput" {
  description = "Provisioned throughput (for gp3)"
  type        = number
  default     = 125
}

variable "dedicated_master_enabled" {
  description = "Enable dedicated master nodes"
  type        = bool
  default     = false
}

variable "dedicated_master_type" {
  description = "Dedicated master instance type"
  type        = string
  default     = "t3.small.search"
}

variable "zone_awareness_enabled" {
  description = "Enable zone awareness"
  type        = bool
  default     = true
}

variable "encrypt_at_rest" {
  description = "Encrypt at rest"
  type        = bool
  default     = true
}

variable "node_to_node_encryption" {
  description = "Node-to-node encryption"
  type        = bool
  default     = true
}

variable "advanced_security_enabled" {
  description = "Enable fine-grained access control"
  type        = bool
  default     = true
}

variable "internal_user_database_enabled" {
  description = "Enable internal user database"
  type        = bool
  default     = true
}

variable "master_username" {
  description = "Master username"
  type        = string
  default     = "admin"
}

variable "master_password" {
  description = "Master password"
  type        = string
  sensitive   = true
}

variable "log_publishing_enabled" {
  description = "Enable log publishing"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

- [ ] **Step 3: Create outputs**

```hcl
output "domain_id" {
  description = "OpenSearch domain ID"
  value       = aws_opensearch_domain.this.id
}

output "domain_arn" {
  description = "OpenSearch domain ARN"
  value       = aws_opensearch_domain.this.arn
}

output "domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = aws_opensearch_domain.this.endpoint
}

output "dashboard_url" {
  description = "OpenSearch dashboard URL"
  value       = aws_opensearch_domain.this.dashboard_endpoint
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.opensearch.id
}
```

- [ ] **Step 4: Update main.tf**

```hcl
# OpenSearch Module
module "opensearch" {
  source = "./modules/opensearch"

  domain_name    = var.opensearch_domain_name
  vpc_id         = data.terraform_remote_state.foundation.outputs.vpc_id
  subnet_ids     = data.terraform_remote_state.foundation.outputs.private_subnet_ids

  instance_type  = var.opensearch_instance_type
  instance_count = var.opensearch_instance_count
  volume_size    = var.opensearch_volume_size

  master_password = var.opensearch_master_password

  tags = {
    Stage = "4-rag-knowledge-base"
  }
}
```

- [ ] **Step 5: Add password variable**

```hcl
# Add to variables.tf:

variable "opensearch_master_password" {
  description = "OpenSearch master password"
  type        = string
  sensitive   = true
}
```

- [ ] **Step 6: Commit**

```bash
git add stage-4-rag-knowledge-base/terraform/modules/opensearch
git commit -m "feat: add OpenSearch Service module with vector support"
```

---

## Chunk 3: Lambda Functions for RAG

### Task 3: Create Index and Search Functions

**Files:**
- Create: `stage-4-rag-knowledge-base/src/services/embedding_service.py`
- Create: `stage-4-rag-knowledge-base/src/services/opensearch_service.py`
- Create: `stage-4-rag-knowledge-base/src/chunking/strategies.py`
- Create: `stage-4-rag-knowledge-base/src/services/rag_service.py`
- Create: `stage-4-rag-knowledge-base/src/handlers/index.py`
- Create: `stage-4-rag-knowledge-base/src/handlers/search.py`

- [ ] **Step 1: Create embedding service**

```bash
cat > stage-4-rag-knowledge-base/src/services/embedding_service.py << 'EOF'
import boto3
import os
from typing import List
from ..utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    """Service for generating embeddings with Bedrock"""

    def __init__(self):
        self.client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))
        self.model_id = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v1")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""

        logger.info("Generating embedding", extra_data={
            "text_length": len(text),
            "model": self.model_id
        })

        try:
            if "titan" in self.model_id:
                return self._embed_titan(text)
            elif "cohere" in self.model_id:
                return self._embed_cohere(text)
            else:
                raise ValueError(f"Unsupported model: {self.model_id}")

        except Exception as e:
            logger.error("Embedding generation failed", extra_data={"error": str(e)})
            raise

    def _embed_titan(self, text: str) -> List[float]:
        """Embed using Amazon Titan"""

        import json

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "inputText": text
            }),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())
        return response_body["embedding"]

    def _embed_cohere(self, text: str) -> List[float]:
        """Embed using Cohere"""

        import json

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "texts": [text],
                "input_type": "search_document"
            }),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())
        return response_body["embeddings"][0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""

        logger.info("Batch embedding", extra_data={"count": len(texts)})

        return [self.embed_text(text) for text in texts]
EOF
```

- [ ] **Step 2: Create chunking strategies**

```bash
cat > stage-4-rag-knowledge-base/src/chunking/strategies.py << 'EOF'
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ChunkingStrategy(ABC):
    """Base class for chunking strategies"""

    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks"""
        pass

class FixedSizeChunker(ChunkingStrategy):
    """Fixed-size chunking with overlap"""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split into fixed-size chunks"""

        chunks = []
        start = 0
        chunk_num = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append({
                "text": chunk_text,
                "chunk_id": f"{metadata.get('doc_id', 'doc')}_chunk_{chunk_num}",
                "start_pos": start,
                "end_pos": end,
                "metadata": metadata or {}
            })

            start = end - self.overlap
            chunk_num += 1

        logger.info("Fixed-size chunking complete", extra_data={
            "total_chunks": len(chunks)
        })

        return chunks

class SemanticChunker(ChunkingStrategy):
    """Chunk by semantic boundaries (sentences, paragraphs)"""

    def __init__(self, max_size: int = 1500):
        self.max_size = max_size
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\n+')

    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split by semantic boundaries"""

        # First split by paragraphs
        paragraphs = self.paragraph_breaks.split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_num = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.max_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk, chunk_num, metadata
                    ))
                    chunk_num += 1
                current_chunk = para

        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_num, metadata))

        logger.info("Semantic chunking complete", extra_data={
            "total_chunks": len(chunks)
        })

        return chunks

    def _create_chunk(
        self,
        text: str,
        chunk_num: int,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "text": text,
            "chunk_id": f"{metadata.get('doc_id', 'doc')}_chunk_{chunk_num}",
            "metadata": metadata or {}
        }

class RecursiveChunker(ChunkingStrategy):
    """Hierarchical chunking: try paragraphs, then sentences, then fixed"""

    def __init__(self, max_size: int = 1500, overlap: int = 100):
        self.max_size = max_size
        self.overlap = overlap
        self.semantic_chunker = SemanticChunker(max_size)
        self.fixed_chunker = FixedSizeChunker(max_size, overlap)

    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recursively chunk text"""

        # Try semantic first
        chunks = self.semantic_chunker.chunk(text, metadata)

        # If any chunk is too large, use fixed chunking
        if any(len(c["text"]) > self.max_size for c in chunks):
            return self.fixed_chunker.chunk(text, metadata)

        return chunks

class HybridChunker(ChunkingStrategy):
    """Combine semantic and fixed-size approaches"""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.semantic_chunker = SemanticChunker(chunk_size)
        self.fixed_chunker = FixedSizeChunker(chunk_size, overlap)

    def chunk(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Use semantic if possible, fall back to fixed"""

        chunks = self.semantic_chunker.chunk(text, metadata)

        # Check for oversized chunks
        final_chunks = []
        for chunk in chunks:
            if len(chunk["text"]) > self.fixed_chunker.chunk_size:
                sub_chunks = self.fixed_chunker.chunk(chunk["text"], chunk["metadata"])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks

def get_chunker(strategy: str = "hybrid", **kwargs) -> ChunkingStrategy:
    """Factory function for chunkers"""

    chunkers = {
        "fixed": FixedSizeChunker,
        "semantic": SemanticChunker,
        "recursive": RecursiveChunker,
        "hybrid": HybridChunker,
    }

    if strategy not in chunkers:
        raise ValueError(f"Unknown chunking strategy: {strategy}")

    return chunkers[strategy](**kwargs)
EOF
```

- [ ] **Step 3: Create OpenSearch service**

```bash
cat > stage-4-rag-knowledge-base/src/services/opensearch_service.py << 'EOF'
import os
from typing import List, Dict, Any, Optional
from opensearchpy import OpenSearch, RequestsHttpConnection
from ..utils.logger import get_logger

logger = get_logger(__name__)

class OpenSearchService:
    """Service for OpenSearch operations"""

    def __init__(self):
        self.endpoint = os.getenv("OPENSEARCH_ENDPOINT")
        self.index_name = os.getenv("OPENSEARCH_INDEX", "rag-docs")
        self.vector_dimension = int(os.getenv("VECTOR_DIMENSION", "1536"))

        self.client = OpenSearch(
            hosts=[{"host": self.endpoint, "port": 443}],
            http_auth=(
                os.getenv("OPENSEARCH_USERNAME"),
                os.getenv("OPENSEARCH_PASSWORD")
            ),
            use_ssl=True,
            verify_certs=True,
            ssl_show_warn=False,
            connection_class=RequestsHttpConnection
        )

    def create_index(self) -> None:
        """Create index with vector mapping"""

        if self.client.indices.exists(index=self.index_name):
            logger.info("Index already exists", extra_data={"index": self.index_name})
            return

        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "text": {"type": "text"},
                    "chunk_id": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": self.vector_dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "metadata": {"type": "object"},
                    "created_at": {"type": "date"}
                }
            }
        }

        self.client.indices.create(index=self.index_name, body=index_body)
        logger.info("Index created", extra_data={"index": self.index_name})

    def index_document(
        self,
        chunk_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """Index a document chunk"""

        document = {
            "text": text,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "metadata": metadata,
            "created_at": {"$date": "now"}
        }

        self.client.index(
            index=self.index_name,
            id=chunk_id,
            body=document
        )

    def bulk_index(
        self,
        documents: List[Dict[str, Any]]
    ) -> None:
        """Bulk index documents"""

        from opensearchpy.helpers import bulk

        success, failed = bulk(
            self.client,
            documents,
            index=self.index_name,
            raise_on_error=False
        )

        logger.info("Bulk indexing complete", extra_data={
            "success": success,
            "failed": len(failed)
        })

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """k-NN vector search"""

        search_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector,
                                    "k": top_k
                                }
                            }
                        }
                    ]
                }
            }
        }

        if filters:
            for field, value in filters.items():
                search_body["query"]["bool"]["filter"] = [
                    {"term": {f"metadata.{field}": value}}
                ]

        response = self.client.search(
            index=self.index_name,
            body=search_body
        )

        results = []
        for hit in response["hits"]["hits"]:
            results.append({
                "chunk_id": hit["_source"]["chunk_id"],
                "text": hit["_source"]["text"],
                "score": hit["_score"],
                "metadata": hit["_source"].get("metadata", {})
            })

        return results

    def hybrid_search(
        self,
        query_text: str,
        query_vector: List[float],
        top_k: int = 5,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Hybrid vector + keyword search"""

        search_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "should": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector,
                                    "k": top_k
                                }
                            }
                        },
                        {
                            "match": {
                                "text": {
                                    "query": query_text,
                                    "boost": 1 - alpha
                                }
                            }
                        }
                    ]
                }
            }
        }

        response = self.client.search(
            index=self.index_name,
            body=search_body
        )

        return [{
            "chunk_id": hit["_source"]["chunk_id"],
            "text": hit["_source"]["text"],
            "score": hit["_score"],
            "metadata": hit["_source"].get("metadata", {})
        } for hit in response["hits"]["hits"]]

    def delete_index(self) -> None:
        """Delete the index"""

        if self.client.indices.exists(index=self.index_name):
            self.client.indices.delete(index=self.index_name)
            logger.info("Index deleted", extra_data={"index": self.index_name})
EOF
```

- [ ] **Step 4: Create RAG service**

```bash
cat > stage-4-rag-knowledge-base/src/services/rag_service.py << 'EOF'
import os
from typing import List, Dict, Any
from .embedding_service import EmbeddingService
from .opensearch_service import OpenSearchService
from ..utils.logger import get_logger
from ..llm_service import LLMService

logger = get_logger(__name__)

class RAGService:
    """RAG query service"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.opensearch_service = OpenSearchService()
        self.llm_service = LLMService()

        self.top_k = int(os.getenv("TOP_K", "5"))

    def query(
        self,
        question: str,
        top_k: int = None,
        filters: Dict[str, Any] = None,
        use_hybrid: bool = False
    ) -> Dict[str, Any]:
        """RAG query: retrieve + generate"""

        logger.info("RAG query", extra_data={"question": question})

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(question)

        # Retrieve relevant chunks
        if use_hybrid:
            chunks = self.opensearch_service.hybrid_search(
                query_text=question,
                query_vector=query_embedding,
                top_k=top_k or self.top_k
            )
        else:
            chunks = self.opensearch_service.search(
                query_vector=query_embedding,
                top_k=top_k or self.top_k,
                filters=filters
            )

        logger.info("Retrieved chunks", extra_data={"count": len(chunks)})

        # Build context from chunks
        context = self._build_context(chunks)

        # Generate response with context
        response = self._generate_response(question, context)

        return {
            "answer": response,
            "sources": [
                {
                    "chunk_id": c["chunk_id"],
                    "text": c["text"][:200] + "...",
                    "score": c["score"]
                }
                for c in chunks
            ],
            "chunks_used": len(chunks)
        }

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context from retrieved chunks"""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Source {i}] {chunk['text']}")

        return "\n\n".join(context_parts)

    def _generate_response(self, question: str, context: str) -> str:
        """Generate response using LLM with context"""

        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Please provide a helpful answer based on the context provided. If the context doesn't contain relevant information, please say so.

Answer:"""

        response = self.llm_service.invoke_claude(
            prompt=prompt,
            max_tokens=1000
        )

        return response["response"]
EOF
```

- [ ] **Step 5: Create index handler**

```bash
cat > stage-4-rag-knowledge-base/src/handlers/index.py << 'EOF'
import json
from ..services.embedding_service import EmbeddingService
from ..services.opensearch_service import OpenSearchService
from ..chunking.strategies import get_chunker
from ..utils.response import success_response, error_response
from ..utils.logger import get_logger

logger = get_logger(__name__)
embedding_service = EmbeddingService()
opensearch_service = OpenSearchService()

def handler(event, context):
    """Index document into OpenSearch"""

    logger.info("Index handler invoked")

    try:
        # Parse request
        body = json.loads(event.get("body", "{}"))

        text = body.get("text")
        doc_id = body.get("document_id")
        metadata = body.get("metadata", {})
        chunking_strategy = body.get("chunking_strategy", "hybrid")
        chunk_size = body.get("chunk_size", 1000)
        chunk_overlap = body.get("chunk_overlap", 200)

        if not text:
            return error_response("Text is required", 400)

        # Create index if needed
        opensearch_service.create_index()

        # Chunk document
        chunker = get_chunker(
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )

        chunks = chunker.chunk(text, {"doc_id": doc_id, **metadata})

        # Generate embeddings for all chunks
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)

        # Index chunks
        for chunk, embedding in zip(chunks, embeddings):
            opensearch_service.index_document(
                chunk_id=chunk["chunk_id"],
                text=chunk["text"],
                embedding=embedding,
                metadata=chunk["metadata"]
            )

        return success_response({
            "indexed": len(chunks),
            "document_id": doc_id,
            "chunks": [c["chunk_id"] for c in chunks]
        })

    except Exception as e:
        logger.error("Indexing failed", extra_data={"error": str(e)})
        return error_response(str(e), 500)
EOF
```

- [ ] **Step 6: Create search handler**

```bash
cat > stage-4-rag-knowledge-base/src/handlers/search.py << 'EOF'
import json
from ..services.rag_service import RAGService
from ..utils.response import success_response, error_response
from ..utils.logger import get_logger

logger = get_logger(__name__)
rag_service = RAGService()

def handler(event, context):
    """RAG search handler"""

    logger.info("Search handler invoked")

    try:
        body = json.loads(event.get("body", "{}"))

        question = body.get("question")
        top_k = body.get("top_k", 5)
        filters = body.get("filters")
        use_hybrid = body.get("use_hybrid", False)

        if not question:
            return error_response("Question is required", 400)

        result = rag_service.query(
            question=question,
            top_k=top_k,
            filters=filters,
            use_hybrid=use_hybrid
        )

        return success_response(result)

    except Exception as e:
        logger.error("Search failed", extra_data={"error": str(e)})
        return error_response(str(e), 500)
EOF
```

- [ ] **Step 7: Commit code**

```bash
git add stage-4-rag-knowledge-base/src/
git commit -m "feat: implement RAG services with embedding and vector search"
```

---

## Chunk 4: Testing & Documentation

### Task 4: Create Tests and Documentation

- [ ] **Step 1: Create tests**

```bash
cat > stage-4-rag-knowledge-base/tests/test_chunking.py << 'EOF'
import pytest
from src.chunking.strategies import (
    FixedSizeChunker,
    SemanticChunker,
    HybridChunker,
    get_chunker
)

class TestChunking:
    def test_fixed_size_chunker(self):
        text = "A" * 2500
        chunker = FixedSizeChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(text)

        assert len(chunks) == 3
        assert len(chunks[0]["text"]) == 1000
        assert chunks[0]["chunk_id"] == "doc_chunk_0"

    def test_semantic_chunker(self):
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunker = SemanticChunker(max_size=500)
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert "Para 1" in chunks[0]["text"]

    def test_hybrid_chunker(self):
        text = "A" * 3000
        chunker = HybridChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(text)

        assert len(chunks) > 1

    def test_chunker_factory(self):
        chunker = get_chunker("fixed", chunk_size=1000)
        assert isinstance(chunker, FixedSizeChunker)

        with pytest.raises(ValueError):
            get_chunker("invalid")
EOF
```

- [ ] **Step 2: Create design document**

```bash
cat > stage-4-rag-knowledge-base/docs/design.md << 'EOF'
# Stage 4: RAG Knowledge Base - Architecture Design

## 1. Architecture Overview

```
Documents → Chunker → Embeddings → OpenSearch
                                     ↓
Query → Embedding → k-NN Search → Chunks
                                     ↓
                            Context + LLM → Response
```

## 2. Design Decisions

### Decision 1: Vector Database Selection

**Problem:** Which vector database for semantic search?

**Options:**
- A. OpenSearch Service (AWS native)
- B. Pinecone (SaaS)
- C. Weaviate (Self-hosted)
- D. Aurora pgvector

**Selection:** OpenSearch Service

**Pros:**
- ✅ AWS native integration
- ✅ Support for hybrid search (vector + keyword)
- ✅ No data transfer costs (VPC)
- ✅ Familiar operational model
- ✅ Scalable and managed

**Cons:**
- ❌ Higher baseline cost (~$60/month minimum)
- ❌ Complex setup for VPC deployment
- ❌ Requires instance management

**Cost Comparison:**
- OpenSearch t3.medium x2: ~$70/month
- Pinecone Starter: ~$70/month
- Aurora pgvector: ~$15/month (but limited scale)

---

### Decision 2: Chunking Strategy

**Problem:** How to split documents for vector search?

**Selection:** Hybrid approach with strategy selection

**Strategies:**

1. **Fixed Size**: Simple, consistent
   - Best for: General documents
   - Pros: Predictable, easy to implement
   - Cons: May break semantic units

2. **Semantic**: Sentence/paragraph boundaries
   - Best for: Structured content
   - Pros: Preserves meaning
   - Cons: Variable chunk sizes

3. **Hybrid**: Semantic with size limits
   - Best for: Complex documents
   - Pros: Best of both
   - Cons: More complex

**Recommendation:**
- Start with Fixed Size for simplicity
- Switch to Hybrid for production
- Tune chunk_size and overlap based on:

```
chunk_size = 1000-1500 (balance context vs precision)
overlap = 10-20% of chunk_size (preserve context)
```

---

### Decision 3: Embedding Model Selection

**Problem:** Which embedding model to use?

**Options:**
- Amazon Titan Embed: 1536 dimensions
- Cohere Embed: 1024 dimensions
- OpenAI Ada: 1536 dimensions (not in Bedrock)

**Selection:** Amazon Titan Embed Text v1

**Pros:**
- ✅ AWS native (no additional setup)
- ✅ Good balance of quality and speed
- ✅ 1536 dimensions (high quality)

**Cons:**
- ❌ Larger than some alternatives
- ❌ More storage/memory for vectors

**Why Not Others:**
- Cohere: Good but fewer dimensions
- OpenAI: Requires API key management

---

### Decision 4: k-NN Parameters

**Problem:** How to tune vector search quality?

**Parameters:**

| Parameter | Description | Recommended |
|-----------|-------------|-------------|
| k | Results to return | 5-10 |
| ef_search | Accuracy vs speed | 100-200 |
| m | Graph connections | 16-32 |

**Trade-offs:**
- Higher k = more context, slower generation
- Higher ef_search = better recall, slower search
- Higher m = better accuracy, more memory

**Starting Point:**
```python
k = 5
ef_search = 100
m = 24
```

**Tuning Strategy:**
1. Start with defaults
2. Measure retrieval quality
3. Adjust based on use case
4. A/B test with real queries

---

## 3. RAG Pipeline Optimization

### Retrieval Quality Metrics

1. **Relevance**: Retrieved chunks match query intent
2. **Coverage**: Chunks cover all aspects of answer
3. **Conciseness**: Minimize irrelevant context

### Optimization Techniques

1. **Reranking**: Re-score retrieved chunks
2. **Hybrid Search**: Combine vector + keyword
3. **Query Expansion**: Add related terms
4. **Context Window**: Optimize chunk count

### Evaluation

```python
# Evaluate retrieval quality
def evaluate_retrieval(query, retrieved_chunks, expected_answer):
    # Check if expected info is in chunks
    # Measure overlap
    # Score relevance
    pass
```

---

## 4. Cost Analysis

| Component | Unit Cost | Monthly (10K docs) |
|-----------|-----------|-------------------|
| OpenSearch | ~$70/month | ~$70 |
| S3 Storage | $0.023/GB | ~$1 |
| Lambda | $0.20/1M req | ~$2 |
| Bedrock Embeddings | $0.10/1M tokens | ~$0.50 |
| Bedrock Claude | $3/1M input | ~$5-10 |

**Total: ~$80-100/month**

---

## 5. Common Issues

### Problem: Poor retrieval quality

**Solutions:**
1. Adjust chunk_size (too large/small?)
2. Try different chunking strategy
3. Increase top_k
4. Use hybrid search

### Problem: Slow indexing

**Solutions:**
1. Batch embeddings
2. Use bulk API
3. Increase instance size
4. Parallel processing

### Problem: Expensive storage

**Solutions:**
1. Reduce embedding dimension
2. Delete old documents
3. Use compression
4. Consider pgvector for small scale

---

**Design Document Created:** 2026-03-10
EOF
```

- [ ] **Step 2: Commit**

```bash
git add stage-4-rag-knowledge-base/tests/ stage-4-rag-knowledge-base/docs/
git commit -m "test: add chunking tests; docs: add architecture design"
```

---

## Completion Checklist

- [ ] OpenSearch domain deployed
- [ ] Index created with vector mapping
- [ ] Embedding service working
- [ ] Chunking strategies implemented
- [ ] RAG search functional
- [ ] Tests passing
- [ ] Documentation complete

---

**Implementation Plan Created:** 2026-03-10
**Estimated Time:** 3-4 weeks
**Next:** Begin implementation
