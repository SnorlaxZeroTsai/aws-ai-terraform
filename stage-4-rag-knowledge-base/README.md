# Stage 4: RAG Knowledge Base

A production-grade Retrieval-Augmented Generation (RAG) system built with AWS services, demonstrating semantic search and knowledge injection for AI applications.

## Overview

This project implements a complete RAG pipeline that:
- Automatically indexes documents uploaded to S3
- Generates vector embeddings using AWS Bedrock
- Enables semantic search via OpenSearch Vector Engine
- Generates context-aware answers using Claude via Bedrock
- Exposes a REST API via API Gateway

## Architecture

```
Documents → S3 → Lambda (Chunking + Embedding) → OpenSearch Vector DB
                                                              ↓
Query → API Gateway → Lambda (RAG Pipeline) → Response
                      ↓
                Query Embedding (Bedrock)
                      ↓
                Vector Search (OpenSearch)
                      ↓
                Context + Query → Claude (Bedrock)
```

## Features

- **Multiple Chunking Strategies**: Fixed-size, semantic, and hybrid approaches
- **Vector Search**: k-NN similarity search with configurable parameters
- **Hybrid Search**: Combines keyword and vector search
- **Multiple Prompt Templates**: Q&A, summary, explanation, conversational
- **Conversation History**: Multi-turn conversations support
- **Configurable Parameters**: Chunk size, overlap, max results, search type

## Tech Stack

- **Infrastructure**: Terraform
- **Compute**: AWS Lambda (Python 3.11)
- **Vector Database**: OpenSearch Service (Vector Engine)
- **Embeddings**: AWS Bedrock (Amazon Titan Embeddings v1)
- **LLM**: AWS Bedrock (Claude 3 Sonnet)
- **Storage**: AWS S3
- **API**: AWS API Gateway

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.0 installed
3. **Python** 3.11+ installed
4. **AWS CLI** configured with credentials
5. **Stage 1** (Terraform Foundation) deployed
6. **Bedrock Access** enabled for:
   - Amazon Titan Embeddings v1
   - Anthropic Claude 3 Sonnet

## Project Structure

```
stage-4-rag-knowledge-base/
├── terraform/                 # Terraform infrastructure code
│   ├── main.tf               # Main configuration
│   ├── variables.tf          # Variable definitions
│   ├── outputs.tf            # Output definitions
│   ├── provider.tf           # Provider configuration
│   └── modules/              # Reusable modules
│       ├── opensearch/       # OpenSearch domain
│       ├── lambda/           # Lambda functions + API Gateway
│       ├── s3/               # S3 bucket for documents
│       └── bedrock/          # Bedrock model access
├── src/                      # Python source code
│   ├── handlers/             # Lambda handlers
│   │   ├── index_handler.py  # Document indexing
│   │   └── search_handler.py # RAG search
│   ├── services/             # Business logic
│   │   ├── embedding_service.py   # Bedrock embeddings
│   │   ├── opensearch_service.py  # Vector search
│   │   └── rag_service.py         # RAG orchestration
│   ├── chunking/             # Chunking strategies
│   │   ├── strategies.py     # Chunk implementations
│   │   └── evaluation.py     # Quality metrics
│   ├── prompts/              # Prompt templates
│   │   └── rag_templates.py  # RAG prompts
│   └── utils/                # Utilities
├── tests/                    # Test suite
│   ├── rag_test.py          # RAG pipeline tests
│   └── chunking_test.py     # Chunking tests
├── docs/                     # Documentation
│   ├── design.md            # Design decisions
│   └── ARCHITECTURE.md      # Technical architecture
├── data/                     # Sample data
│   └── sample_documents/    # Test documents
├── README.md                 # This file
├── requirements.txt          # Python dependencies
└── .gitignore               # Git ignore rules
```

## Deployment Guide

### Step 1: Enable Bedrock Models

Before deploying, enable the required Bedrock models:

1. Go to AWS Console → Amazon Bedrock
2. Navigate to "Model Access"
3. Request access for:
   - Amazon Titan Embeddings v1
   - Anthropic Claude 3 Sonnet
4. Wait for access to be granted (usually immediate)

### Step 2: Configure Terraform Variables

Create a `terraform/terraform.tfvars` file from the template:

```bash
cd terraform
cp terraform.tfvars.template terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region  = "us-east-1"
environment = "dev"

# Update with unique bucket name
documents_bucket_name = "stage4-documents-yourname-1234"

# Adjust instance types based on your needs
opensearch_instance_type = "t3.medium.search"
opensearch_instance_count = 2

# Verify Stage 1 path is correct
stage1_state_path = "../../stage-1-terraform-foundation/terraform/terraform.tfstate"
```

**Important**: Replace `yourname-1234` with a unique identifier for the S3 bucket.

### Step 3: Initialize Terraform

```bash
cd terraform
terraform init
```

### Step 4: Plan Deployment

```bash
terraform plan
```

Review the resources to be created. Expected resources:
- OpenSearch domain
- Lambda functions (2)
- API Gateway REST API
- S3 bucket
- IAM roles and policies
- CloudWatch log groups

### Step 5: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. Deployment takes 10-15 minutes.

### Step 6: Note Outputs

After successful deployment, note the outputs:

```bash
terraform output
```

Save the `api_gateway_url` - you'll need it for testing.

## Usage Guide

### Indexing Documents

Documents are automatically indexed when uploaded to S3:

```bash
# Upload a document
aws s3 cp my_document.txt s3://$(terraform output documents_bucket_name)/documents/

# The document will be automatically:
# 1. Downloaded by Lambda
# 2. Chunked using hybrid strategy
# 3. Converted to embeddings via Bedrock
# 4. Indexed in OpenSearch
```

**Supported formats**: Plain text (.txt), Markdown (.md)

### Querying the Knowledge Base

Use the API Gateway endpoint to perform RAG queries:

```bash
# Set your API Gateway URL
API_URL=$(terraform output api_gateway_url)

# Perform a RAG query
curl -X POST ${API_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "max_results": 5,
    "search_type": "vector"
  }'
```

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
        "source": "doc1.txt"
      }
    }
  ],
  "chunk_count": 5
}
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | User question |
| `max_results` | int | 5 | Number of chunks to retrieve |
| `search_type` | string | "vector" | "vector" or "hybrid" |
| `template_type` | string | "qa" | "qa", "summary", "explanation", "conversational" |
| `include_chunks` | boolean | true | Include chunks in response |
| `retrieval_only` | boolean | false | Skip LLM generation |
| `conversation_history` | array | null | Previous conversation turns |

### Example Queries

#### Basic Q&A
```bash
curl -X POST ${API_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the benefits of serverless architecture?"
  }'
```

#### Summary
```bash
curl -X POST ${API_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize the key points about Docker",
    "template_type": "summary"
  }'
```

#### Conversational
```bash
curl -X POST ${API_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Can you explain more about that?",
    "template_type": "conversational",
    "conversation_history": [
      {"role": "user", "content": "What is Kubernetes?"},
      {"role": "assistant", "content": "Kubernetes is..."}
    ]
  }'
```

#### Retrieval Only (No LLM)
```bash
curl -X POST ${API_URL}/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "microservices architecture",
    "retrieval_only": true
  }'
```

## Testing

### Run Unit Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run chunking tests
python tests/chunking_test.py

# Run RAG tests
python tests/rag_test.py
```

### Test with Sample Documents

```bash
# Copy sample documents to S3
aws s3 sync data/sample_documents/ \
  s3://$(terraform output documents_bucket_name)/documents/

# Wait for indexing (check CloudWatch logs)
aws logs tail /aws/lambda/stage4-lambda-index-dev --follow

# Test query
curl -X POST ${API_URL}/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

## Configuration

### Chunking Strategy

Edit `terraform/terraform.tfvars`:

```hcl
chunk_size = 1000      # Target chunk size (characters)
chunk_overlap = 200    # Overlap between chunks
```

**Recommendations**:
- **Short documents**: chunk_size = 500, overlap = 100
- **Long documents**: chunk_size = 1500, overlap = 300
- **Technical docs**: chunk_size = 800, overlap = 150

### OpenSearch Instance Type

Edit `terraform/terraform.tfvars`:

```hcl
opensearch_instance_type = "t3.medium.search"  # Dev
opensearch_instance_type = "t3.large.search"   # Production
```

**Cost Comparison**:
- t3.medium.search: ~$48/month per node
- t3.large.search: ~$96/month per node
- t3.xlarge.search: ~$192/month per node

### Vector Dimension

Confirm embedding model dimension:

```hcl
# Titan Embeddings v1
vector_dimension = 1536

# Titan Embeddings v2 (if using)
vector_dimension = 1024
```

## Monitoring

### View Logs

```bash
# Index handler logs
aws logs tail /aws/lambda/stage4-lambda-index-dev --follow

# Search handler logs
aws logs tail /aws/lambda/stage4-lambda-search-dev --follow

# OpenSearch logs
aws logs tail /aws/opensearch/stage4-rag --follow
```

### Check Metrics

```bash
# Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=stage4-lambda-search-dev

# OpenSearch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ES \
  --metric-name CPUUtilization \
  --dimensions Name=DomainName,Value=stage4-rag
```

## Troubleshooting

### OpenSearch Domain Not Ready

**Problem**: Lambda fails to connect to OpenSearch

**Solution**:
1. Check OpenSearch domain status in AWS Console
2. Wait for domain to be "Active" (can take 10-15 minutes)
3. Verify security group allows Lambda → OpenSearch on port 443

### Bedrock Access Denied

**Problem**: Lambda fails with "Access Denied" to Bedrock

**Solution**:
1. Verify Bedrock models are enabled in AWS Console
2. Check IAM role has `bedrock:InvokeModel` permission
3. Confirm models are available in your region

### Chunking Errors

**Problem**: Documents fail to index

**Solution**:
1. Check CloudWatch logs for error details
2. Verify document format is supported (plain text)
3. Check chunk size is appropriate for document length

### High Query Latency

**Problem**: Queries take > 10 seconds

**Solution**:
1. Check Lambda memory (increase if needed)
2. Verify OpenSearch has sufficient resources
3. Reduce `max_results` parameter
4. Check Bedrock throttling metrics

## Cost Management

### Estimated Monthly Cost (Dev)

| Service | Configuration | Cost |
|---------|---------------|------|
| OpenSearch | 2x t3.medium, 20GB | $96 |
| Lambda | 100K invocations | $2 |
| API Gateway | 100K requests | $0.35 |
| S3 | 10GB storage | $0.50 |
| Bedrock | 1M tokens | $0.10 |
| CloudWatch | Logs | $2 |
| **Total** | | **~$101** |

### Cost Optimization

1. **Reduce OpenSearch costs**:
   - Use smaller instance types for dev
   - Delete unused indices
   - Enable automated snapshots

2. **Reduce Bedrock costs**:
   - Cache embeddings for repeated content
   - Use smaller models for simple queries
   - Implement rate limiting

3. **Reduce Lambda costs**:
   - Optimize memory allocation
   - Reduce timeout values
   - Use provisioned concurrency sparingly

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

**Warning**: This will delete:
- All indexed documents
- OpenSearch domain
- Lambda functions
- API Gateway
- S3 bucket (and all documents)

**Before destroying**:
1. Export important data from S3
2. Create OpenSearch snapshots if needed
3. Save any custom configurations

## Learning Outcomes

After completing this stage, you will understand:

- **RAG Architecture**: How retrieval-augmented generation works
- **Vector Databases**: OpenSearch Vector Engine, k-NN search
- **Embeddings**: Generating and using text embeddings
- **Serverless Patterns**: Lambda, API Gateway integration
- **AWS Bedrock**: Using foundation models via AWS
- **Chunking Strategies**: Different approaches to document splitting
- **Prompt Engineering**: Designing effective RAG prompts

## Next Steps

1. **Experiment** with different chunking strategies
2. **Optimize** prompt templates for your use case
3. **Add** more document formats (PDF, DOCX)
4. **Implement** caching for repeated queries
5. **Add** authentication to API Gateway
6. **Deploy** to production with larger instance types

## Additional Resources

- [Design Document](docs/design.md) - Architecture decisions and trade-offs
- [Technical Architecture](docs/ARCHITECTURE.md) - Detailed technical specifications
- [AWS OpenSearch Documentation](https://docs.aws.amazon.com/opensearch-service/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## Support

For issues or questions:
1. Check CloudWatch logs for error details
2. Review the troubleshooting section above
3. Consult the architecture documentation
4. Verify all prerequisites are met

---

**Stage**: 4 - RAG Knowledge Base
**Status**: Complete
**Last Updated**: 2026-03-12
