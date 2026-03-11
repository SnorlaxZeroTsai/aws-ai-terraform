# Stage 6: AI Agent Platform - Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate all previous stages into a unified AI Agent Platform with multi-agent collaboration, API orchestration, containerization, and comprehensive monitoring.

**Architecture:** API Gateway → Orchestrator → Agent Services (Chatbot, RAG, Autonomous) → Shared Services (DynamoDB, S3, OpenSearch) → Observability (X-Ray, CloudWatch)

**Tech Stack:** Terraform, AWS ECS Fargate, Lambda, API Gateway, X-Ray, CloudWatch, Docker, Python 3.11, TypeScript

---

## Chunk 1: Project Setup and Architecture

### Task 1: Create Platform Structure

**Files:**
- Create: `stage-6-agent-platform/README.md`
- Create: `stage-6-agent-platform/.gitignore`
- Create: `stage-6-agent-platform/terraform/main.tf`
- Create: `stage-6-agent-platform/terraform/variables.tf`
- Create: `stage-6-agent-platform/terraform/outputs.tf`
- Create: `stage-6-agent-platform/terraform/provider.tf`

- [ ] **Step 1: Create directories**

```bash
mkdir -p stage-6-agent-platform/terraform/modules/{api_gateway,ecs,lambda,xray,cloudwatch}
mkdir -p stage-6-agent-platform/src/platform/{api,auth,orchestrator}
mkdir -p stage-6-agent-platform/src/agents/{chatbot,rag,autonomous}
mkdir -p stage-6-agent-platform/src/shared/{config,middleware,utils}
mkdir -p stage-6-agent-platform/docker
mkdir -p stage-6-agent-platform/scripts
mkdir -p stage-6-agent-platform/tests
mkdir -p stage-6-agent-platform/docs
```

- [ ] **Step 2: Create provider.tf**

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "ai-platform-terraform-state"
    key            = "stage-6/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "ai-learning-roadmap"
      Stage     = "6-agent-platform"
      ManagedBy = "Terraform"
    }
  }
}

# Get outputs from all previous stages
data "terraform_remote_state" "stage1" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-1/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "stage2" {
  backend = "s3"
  config = {
    bucket = "ai-platform-terraform-state"
    key    = "stage-2/terraform.tfstate"
    region = "us-east-1"
  }
}

# Repeat for stages 3, 4, 5...
```

- [ ] **Step 3: Create variables.tf**

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "platform_name" {
  description = "Platform name"
  type        = string
  default     = "ai-agent-platform"
}

variable "domain_name" {
  description = "Custom domain name"
  type        = string
  default     = null
}

variable "ecs_task_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 512

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.ecs_task_cpu)
    error_message = "Must be valid ECS CPU value."
  }
}

variable "ecs_task_memory" {
  description = "ECS task memory (MB)"
  type        = number
  default     = 1024

  validation {
    condition     = var.ecs_task_memory >= 512 && var.ecs_task_memory <= 16384
    error_message = "Memory must be between 512 and 16384 MB."
  }
}

variable "desired_count" {
  description = "Desired ECS task count"
  type        = number
  default     = 2
}

variable "enable_auto_scaling" {
  description = "Enable ECS auto-scaling"
  type        = bool
  default     = true
}

variable "min_capacity" {
  description = "Minimum ECS tasks"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum ECS tasks"
  type        = number
  default     = 10
}

variable "enable_xray" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "alarm_email" {
  description = "Email for CloudWatch alarms"
  type        = string
  default     = null
}
```

- [ ] **Step 4: Create outputs.tf**

```hcl
output "api_endpoint_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.endpoint_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.cloudwatch.dashboard_url
}
```

- [ ] **Step 5: Create requirements.txt**

```bash
cat > stage-6-agent-platform/requirements.txt << 'EOF'
# API Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.6.1
pydantic-settings==2.1.0

# AWS SDK
boto3==1.34.84
botocore==1.34.84

# AWS X-Ray
aws-xray-sdk==2.13.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# API Clients
httpx==0.26.0
aiobotocore==2.12.3

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.1

# Monitoring
prometheus-client==0.20.0

# Testing
pytest==8.0.2
pytest-asyncio==0.23.4
pytest-cov==4.1.0
httpx==0.26.0
EOF
```

- [ ] **Step 6: Create README.md**

```bash
cat > stage-6-agent-platform/README.md << 'EOF'
# Stage 6: AI Agent Platform

## Overview

The final stage integrates all previous components into a production-ready AI Agent Platform with multi-agent collaboration, unified API, comprehensive monitoring, and containerized deployment.

## Architecture

```
                    ┌─────────────────┐
                    │  API Gateway    │
                    │  + WAF          │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Orchestrator   │
                    │  (ECS/Fargate)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐    ┌───────▼───────┐    ┌──────▼─────┐
│  Chatbot     │    │  RAG         │    │ Autonomous │
│  Service     │    │  Service     │    │  Agent      │
│  (Lambda)    │    │  (Lambda)    │    │  (SF + L)   │
└──────────────┘    └──────────────┘    └────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Shared Layer   │
                    │  - DynamoDB     │
                    │  - S3           │
                    │  - OpenSearch   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Observability   │
                    │  - X-Ray        │
                    │  - CloudWatch   │
                    └─────────────────┘
```

## Features

### API Gateway
- Unified REST API
- Authentication (JWT/API keys)
- Rate limiting and throttling
- Request/response validation

### Orchestrator
- Agent selection and routing
- Multi-agent coordination
- Request aggregation
- Response composition

### Agent Services
- Chatbot: Conversational AI
- RAG: Knowledge base queries
- Autonomous: Complex task execution

### Observability
- X-Ray distributed tracing
- CloudWatch dashboards
- Custom metrics
- Alarm notifications

## Prerequisites

- Completed Stages 1-5
- AWS Account with appropriate permissions
- Docker installed
- Python 3.11+
- Node.js 18+ (for dashboard)

## Deployment

### 1. Build Docker Image

```bash
docker build -t ai-platform:latest .
```

### 2. Push to ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag ai-platform:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ai-platform:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ai-platform:latest
```

### 3. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. Verify Deployment

```bash
# Health check
curl https://api.example.com/health

# List agents
curl https://api.example.com/agents

# Test chatbot
curl -X POST https://api.example.com/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Hello!"}'
```

## API Documentation

### Authentication

```bash
# Get token
curl -X POST https://api.example.com/auth/token \
  -d "username=admin&password=secret"

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/v1/chat
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /agents | List available agents |
| POST | /auth/token | Get auth token |
| POST | /v1/chat | Chatbot endpoint |
| POST | /v1/rag | RAG query |
| POST | /v1/agent | Autonomous agent |
| GET | /v1/status/{job_id} | Job status |

## Monitoring

### CloudWatch Dashboard
- Request rate and latency
- Error rates by service
- ECS task metrics
- Custom agent metrics

### X-Ray Traces
- End-to-end request tracing
- Service map visualization
- Performance analysis

### Alarms
- High error rate
- High latency
- Low task count
- Custom thresholds

## Cost Estimate

| Component | Monthly |
|-----------|---------|
| API Gateway | $50-100 |
| ECS Fargate | $100-300 |
| Lambda | $20-50 |
| X-Ray | $5-10 |
| CloudWatch | $20-50 |
| Data Transfer | $20-50 |

**Total: $215-560/month**

## Scaling

### Auto-scaling
- Target tracking at 70% CPU
- Scale out: 1 task every 60 seconds
- Scale in: 1 task every 300 seconds

### Manual scaling
```bash
aws ecs update-service \
  --cluster ai-platform \
  --service orchestrator \
  --desired-count 5
```

## Troubleshooting

### Issues and Solutions

| Issue | Solution |
|-------|----------|
| 504 errors | Increase Lambda timeout |
| High latency | Enable provisioned concurrency |
| Out of memory | Increase ECS task memory |
| Throttling | Request quota increase |

## Cleanup

```bash
cd terraform
terraform destroy
```

## What's Next

After completing this stage:
- You have a production-ready AI platform
- Understand microservices architecture
- Can design multi-agent systems
- Ready for production deployment
- Equipped to build real AI applications

Congratulations on completing the Learning Roadmap! 🎉
EOF
```

- [ ] **Step 7: Create Python structure**

```bash
touch stage-6-agent-platform/src/__init__.py
touch stage-6-agent-platform/src/platform/__init__.py
touch stage-6-agent-platform/src/platform/api/__init__.py
touch stage-6-agent-platform/src/platform/auth/__init__.py
touch stage-6-agent-platform/src/platform/orchestrator/__init__.py
touch stage-6-agent-platform/src/agents/__init__.py
touch stage-6-agent-platform/src/agents/chatbot/__init__.py
touch stage-6-agent-platform/src/agents/rag/__init__.py
touch stage-6-agent-platform/src/agents/autonomous/__init__.py
touch stage-6-agent-platform/src/shared/__init__.py
touch stage-6-agent-platform/src/shared/config/__init__.py
touch stage-6-agent-platform/src/shared/middleware/__init__.py
touch stage-6-agent-platform/src/shared/utils/__init__.py
```

- [ ] **Step 8: Commit**

```bash
git add stage-6-agent-platform/
git commit -m "feat: stage-6 initial platform structure"
```

---

## Chunk 2: Docker and ECS

### Task 2: Containerize Platform

**Files:**
- Create: `stage-6-agent-platform/docker/Dockerfile`
- Create: `stage-6-agent-platform/docker/docker-compose.yml`
- Create: `stage-6-agent-platform/terraform/modules/ecs/main.tf`
- Create: `stage-6-agent-platform/src/platform/api/main.py`

- [ ] **Step 1: Create Dockerfile**

```bash
cat > stage-6-agent-platform/docker/Dockerfile << 'EOF'
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install X-Ray daemon
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    && wget https://s3.dualstack.us-east-1.amazonaws.com/aws-xray-daemon-service/aws-xray-daemon-linux-process.zip \
    && unzip aws-xray-daemon-linux-process.zip -d /opt/aws-xray \
    && rm aws-xray-daemon-linux-process.zip

# Copy application
COPY ./src /app/src

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with X-Ray
CMD ["python", "-m", "uvicorn", "src.platform.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

- [ ] **Step 2: Create docker-compose for local**

```bash
cat > stage-6-agent-platform/docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=us-east-1
      - ENVIRONMENT=dev
      - ENABLE_XRAY=false
    volumes:
      - ../src:/app/src
    command: ["python", "-m", "uvicorn", "src.platform.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  dynamodb:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/home/dynamodblocal/data

  opensearch:
    image: opensearchproject/opensearch:latest
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"

volumes:
  dynamodb-data:
EOF
```

- [ ] **Step 3: Create ECS module**

```hcl
# ECR Repository
resource "aws_ecr_repository" "this" {
  name                 = var.platform_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

# ECS Cluster
resource "aws_ecs_cluster" "this" {
  name = "${var.platform_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = var.tags
}

# ECS Task Definition
resource "aws_ecs_task_definition" "orchestrator" {
  family                   = "${var.platform_name}-orchestrator"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "orchestrator"
      image     = "${aws_ecr_repository.this.repository_url}:latest"
      cpu       = var.task_cpu
      memory    = var.task_memory
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "ENABLE_XRAY"
          value = var.enable_xray ? "true" : "false"
        }
      ]

      secrets = var.secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.orchestrator.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "orchestrator"
          "awslogs-create-group"  = "true"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      linuxParameters = {
        capabilities = {
          add = ["SYS_ADMIN"]
        }
      }
    }
  ])

  tags = var.tags
}

# ECS Service
resource "aws_ecs_service" "orchestrator" {
  name            = "${var.platform_name}-orchestrator"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "orchestrator"
    container_port   = 8000
  }

  # Enable X-Ray
  enable_execute_command = true

  # Deployment configuration
  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 50
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  # Auto-scaling
  dynamic "capacity_provider_strategy" {
    for_each = var.enable_auto_scaling ? [1] : []
    content {
      capacity_provider = "FARGATE"
      weight            = 1
      base              = 1
    }
  }

  tags = var.tags

  depends_on = [aws_iam_role_policy_attachment.execution]
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "orchestrator" {
  name              = "/ecs/orchestrator"
  retention_in_days = var.log_retention

  tags = var.tags
}

# Application Auto-scaling
resource "aws_appautoscaling_target" "ecs" {
  count = var.enable_auto_scaling ? 1 : 0

  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.this.name}/${aws_ecs_service.orchestrator.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs" {
  count = var.enable_auto_scaling ? 1 : 0

  name               = "${var.platform_name}-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# IAM roles
resource "aws_iam_role" "execution" {
  name = "${var.platform_name}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "${var.platform_name}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Task policy (add as needed)
resource "aws_iam_role_policy" "task" {
  name = "${var.platform_name}-task-policy"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:*",
          "s3:*",
          "lambda:InvokeFunction",
          "bedrock:*",
          "xray:*"
        ]
        Resource = "*"
      }
    ]
  })
}
```

- [ ] **Step 4: Create FastAPI main**

```bash
cat > stage-6-agent-platform/src/platform/api/main.py << 'EOF'
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from ..orchestrator.router import AgentRouter
from ..auth.middleware import auth_middleware
from .middleware import xray_middleware
from ..shared.config import settings
from ..shared.utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Platform",
    description="Unified platform for AI agents",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# X-Ray middleware (if enabled)
if settings.ENABLE_XRAY:
    app.add_middleware(xray_middleware)

# Agent router
agent_router = AgentRouter()

@app.on_event("startup")
async def startup():
    """Initialize services"""
    logger.info("Starting AI Agent Platform")
    await agent_router.initialize()

@app.on_event("shutdown")
async def shutdown():
    """Cleanup services"""
    logger.info("Shutting down AI Agent Platform")
    await agent_router.cleanup()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/agents")
async def list_agents(auth = Depends(auth_middleware)):
    """List available agents"""
    return {
        "agents": agent_router.list_agents()
    }

@app.post("/v1/chat")
async def chat_endpoint(request: dict, auth = Depends(auth_middleware)):
    """Chatbot endpoint"""
    try:
        result = await agent_router.route("chatbot", request)
        return result
    except Exception as e:
        logger.error("Chat endpoint error", extra_data={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/rag")
async def rag_endpoint(request: dict, auth = Depends(auth_middleware)):
    """RAG query endpoint"""
    try:
        result = await agent_router.route("rag", request)
        return result
    except Exception as e:
        logger.error("RAG endpoint error", extra_data={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/agent")
async def agent_endpoint(request: dict, auth = Depends(auth_middleware)):
    """Autonomous agent endpoint"""
    try:
        result = await agent_router.route("autonomous", request)
        return result
    except Exception as e:
        logger.error("Agent endpoint error", extra_data={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/status/{job_id}")
async def job_status(job_id: str, auth = Depends(auth_middleware)):
    """Get job status"""
    status = await agent_router.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", extra_data={"error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "dev"
    )
EOF
```

- [ ] **Step 5: Commit Docker and ECS**

```bash
git add stage-6-agent-platform/docker/ stage-6-agent-platform/terraform/modules/ecs/ stage-6-agent-platform/src/platform/api/
git commit -m "feat: add Docker containerization and ECS deployment"
```

---

## Chunk 3: Orchestrator and Multi-Agent

### Task 3: Create Agent Orchestration

**Files:**
- Create: `stage-6-agent-platform/src/platform/orchestrator/router.py`
- Create: `stage-6-agent-platform/src/platform/orchestrator/collaboration.py`
- Create: `stage-6-agent-platform/src/agents/chatbot/client.py`
- Create: `stage-6-agent-platform/src/agents/rag/client.py`
- Create: `stage-6-agent-platform/src/agents/autonomous/client.py`

- [ ] **Step 1: Create orchestrator router**

```bash
cat > stage-6-agent-platform/src/platform/orchestrator/router.py << 'EOF'
from typing import Dict, Any, List
from ..shared.utils.logger import get_logger
from .collaboration import AgentCollaborator

logger = get_logger(__name__)

class AgentRouter:
    """Routes requests to appropriate agents"""

    def __init__(self):
        self.agents = {}
        self.collaborator = AgentCollaborator()

    async def initialize(self):
        """Initialize agent clients"""
        from ..agents.chatbot.client import ChatbotClient
        from ..agents.rag.client import RAGClient
        from ..agents.autonomous.client import AutonomousClient

        self.agents = {
            "chatbot": ChatbotClient(),
            "rag": RAGClient(),
            "autonomous": AutonomousClient()
        }

        logger.info("Agent router initialized", extra_data={
            "agents": list(self.agents.keys())
        })

    async def cleanup(self):
        """Cleanup agent clients"""
        for agent in self.agents.values():
            if hasattr(agent, "close"):
                await agent.close()

    def list_agents(self) -> List[Dict[str, str]]:
        """List available agents"""
        return [
            {
                "name": name,
                "type": agent.__class__.__name__,
                "description": agent.description
            }
            for name, agent in self.agents.items()
        ]

    async def route(
        self,
        agent_name: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to agent"""

        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = self.agents[agent_name]
        logger.info(f"Routing to {agent_name}", extra_data={"request": request})

        return await agent.execute(request)

    async def route_collaborative(
        self,
        agents: List[str],
        request: Dict[str, Any],
        mode: str = "sequential"
    ) -> Dict[str, Any]:
        """Route to multiple agents with collaboration"""

        if mode == "sequential":
            return await self.collaborator.sequential(agents, request)
        elif mode == "parallel":
            return await self.collaborator.parallel(agents, request)
        elif mode == "hierarchical":
            return await self.collaborator.hierarchical(agents, request)
        else:
            raise ValueError(f"Unknown collaboration mode: {mode}")

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """Get agent job status"""

        # Check all agents for job
        for agent in self.agents.values():
            if hasattr(agent, "get_status"):
                status = await agent.get_status(job_id)
                if status:
                    return status

        return None
EOF
```

- [ ] **Step 2: Create collaboration module**

```bash
cat > stage-6-agent-platform/src/platform/orchestrator/collaboration.py << 'EOF'
from typing import List, Dict, Any
import asyncio
from ..shared.utils.logger import get_logger

logger = get_logger(__name__)

class AgentCollaborator:
    """Manages multi-agent collaboration"""

    def __init__(self):
        pass

    async def sequential(
        self,
        agents: List[str],
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents sequentially, passing results"""

        logger.info("Sequential collaboration", extra_data={
            "agents": agents,
            "request": request
        })

        results = {}
        current_input = request

        for agent_name in agents:
            # Execute agent
            result = await self._execute_agent(agent_name, current_input)
            results[agent_name] = result

            # Pass result to next agent
            current_input = {
                "original_request": request,
                "previous_results": results
            }

        return {
            "mode": "sequential",
            "agents": agents,
            "results": results
        }

    async def parallel(
        self,
        agents: List[str],
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents in parallel"""

        logger.info("Parallel collaboration", extra_data={
            "agents": agents
        })

        # Execute all agents concurrently
        tasks = [
            self._execute_agent(agent, request)
            for agent in agents
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile results
        results = {}
        for agent_name, result in zip(agents, results_list):
            if isinstance(result, Exception):
                results[agent_name] = {"error": str(result)}
            else:
                results[agent_name] = result

        return {
            "mode": "parallel",
            "agents": agents,
            "results": results
        }

    async def hierarchical(
        self,
        agents: List[str],
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Hierarchical: First agent coordinates others"""

        logger.info("Hierarchical collaboration", extra_data={
            "coordinator": agents[0],
            "workers": agents[1:]
        })

        coordinator = agents[0]
        workers = agents[1:]

        # First agent decides how to use others
        coordination_request = {
            **request,
            "available_agents": workers
        }

        coordination_result = await self._execute_agent(
            coordinator,
            coordination_request
        )

        # Execute worker agents as directed
        worker_results = {}
        if "execute" in coordination_result:
            for worker_plan in coordination_result["execute"]:
                worker = worker_plan["agent"]
                worker_request = worker_plan["request"]
                worker_results[worker] = await self._execute_agent(
                    worker,
                    worker_request
                )

        # Coordinator synthesizes final answer
        synthesis_request = {
            "original_request": request,
            "worker_results": worker_results
        }

        final_result = await self._execute_agent(
            coordinator,
            synthesis_request
        )

        return {
            "mode": "hierarchical",
            "coordinator": coordinator,
            "workers": workers,
            "final_result": final_result
        }

    async def _execute_agent(
        self,
        agent_name: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute single agent (to be implemented with actual clients)"""
        # Placeholder - would call actual agent client
        return {
            "agent": agent_name,
            "result": f"Executed with: {request}"
        }
EOF
```

- [ ] **Step 3: Create agent clients**

```bash
# Create client wrappers for each agent type
# These would call the Lambda functions or ECS services from previous stages

cat > stage-6-agent-platform/src/agents/chatbot/client.py << 'EOF'
import boto3
from ...shared.utils.logger import get_logger

logger = get_logger(__name__)

class ChatbotClient:
    """Client for chatbot agent (Stage 2)"""

    description = "Conversational AI assistant"

    def __init__(self):
        self.lambda_client = boto3.client("lambda")
        self.function_name = "ai-chatbot-lambda"

    async def execute(self, request: dict) -> dict:
        """Execute chatbot"""

        payload = {
            "message": request.get("message", ""),
            "conversation_id": request.get("conversation_id")
        }

        response = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType="RequestResponse",
            Payload=payload
        )

        import json
        result = json.loads(response["Payload"].read())

        return {
            "response": result["response"],
            "conversation_id": result["conversation_id"]
        }
EOF
```

- [ ] **Step 4: Commit orchestrator**

```bash
git add stage-6-agent-platform/src/platform/orchestrator/ stage-6-agent-platform/src/agents/
git commit -m "feat: implement agent orchestrator with multi-agent collaboration"
```

---

## Chunk 4: Monitoring and Observability

### Task 4: Add X-Ray and CloudWatch

**Files:**
- Create: `stage-6-agent-platform/terraform/modules/xray/main.tf`
- Create: `stage-6-agent-platform/terraform/modules/cloudwatch/main.tf`
- Create: `stage-6-agent-platform/src/platform/middleware/xray.py`

- [ ] **Step 1: Create X-Ray module**

```hcl
resource "aws_xray_encryption_config" "this" {
  count = var.enable_encryption ? 1 : 0

  type    = "KMS"
  key_id  = var.kms_key_id
  role    = var.xray_role_name
}

# X-Ray sampling rule
resource "aws_xray_sampling_rule" "this" {
  rule_name      = "${var.platform_name}-sampling"
  priority       = 100
  reservoir_size = 1
  fixed_rate     = 0.1  # 10% sampling
  url_path       = "*"

  host     = "*"
  method   = "*"
  service_type = "*"
  resource_arn = "*"

  tags = var.tags
}
```

- [ ] **Step 2: Create CloudWatch module**

```hcl
# Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.platform_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", "orchestrator"],
            [".", "MemoryUtilization", ".", "."],
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "platform-alb"],
            [".", "TargetResponseTime", ".", "."],
            ["AWS/Lambda", "Invocations", "FunctionName", "chatbot"],
            [".", "Errors", ".", "."],
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Platform Metrics"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6

        properties = {
          logGroupName  = aws_cloudwatch_log_group.orchestrator.name
          region        = var.aws_region
          title         = "Orchestrator Logs"
          view          = "table"
        }
      }
    ]
  })
}

# Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.platform_name}-high-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"

  alarm_actions = var.alarm_actions
  ok_actions    = var.alarm_actions

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "${var.platform_name}-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"

  alarm_actions = var.alarm_actions
  ok_actions    = var.alarm_actions

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "low_task_count" {
  alarm_name          = "${var.platform_name}-low-tasks"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "RunningTaskCount"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"

  alarm_actions = var.alarm_actions

  dimensions = {
    ServiceName = "orchestrator"
    ClusterName = aws_ecs_cluster.this.name
  }

  tags = var.tags
}
```

- [ ] **Step 3: Create X-Ray middleware**

```bash
cat > stage-6-agent-platform/src/platform/middleware/xray.py << 'EOF'
from fastapi import Request
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

def xray_middleware(app):
    """Add X-Ray tracing to FastAPI"""

    xray_recorder.configure(
        sampling=True,
        context_missing="LOG_ERROR"
    )

    app.add_middleware(XRayMiddleware,
        xray_recorder=xray_recorder,
        streaming_url=os.getenv("AWS_XRAY_DAEMON_ADDRESS", "127.0.0.1:2000")
    )

    @app.middleware("http")
    async def trace_requests(request: Request, call_next):
        # X-Ray middleware handles tracing
        response = await call_next(request)
        return response
EOF
```

- [ ] **Step 4: Commit monitoring**

```bash
git add stage-6-agent-platform/terraform/modules/xray/ stage-6-agent-platform/terraform/modules/cloudwatch/ stage-6-agent-platform/src/platform/middleware/
git commit -m "feat: add X-Ray tracing and CloudWatch monitoring"
```

---

## Chunk 5: Documentation and Completion

### Task 5: Final Documentation

- [ ] **Step 1: Create architecture design**

```bash
cat > stage-6-agent-platform/docs/design.md << 'EOF'
# Stage 6: AI Agent Platform - Architecture Design

## 1. Platform Overview

This final stage integrates all previous components into a production-ready AI Agent Platform.

## 2. Multi-Agent Collaboration Patterns

### Sequential
```
User → Agent1 → Result1 → Agent2 → Result2 → Agent3 → Final Answer
```
Best for: Multi-step workflows

### Parallel
```
          → Agent1 → Result1
User → ─→ Agent2 → Result2 → Aggregator → Final Answer
          → Agent3 → Result3
```
Best for: Diverse perspectives

### Hierarchical
```
User → Coordinator Agent
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
 Worker1   Worker2   Worker3
    └─────────┴─────────┘
              ↓
         Coordinator → Final Answer
```
Best for: Complex task decomposition

## 3. Deployment Architecture

### Components
- API Gateway: Unified entry point
- ECS Fargate: Long-running orchestrator
- Lambda: Stateless agent services
- ALB/NLB: Load balancing
- X-Ray: Distributed tracing
- CloudWatch: Monitoring and alarms

### Scaling Strategy
- ECS: Auto-scale on CPU/memory
- Lambda: Concurrent executions
- API Gateway: Throttling rules

## 4. Production Considerations

### Security
- JWT authentication
- API key management
- VPC isolation
- WAF rules
- Secret rotation

### Reliability
- Multi-AZ deployment
- Health checks
- Circuit breakers
- Dead letter queues
- Backup and restore

### Performance
- Connection pooling
- Caching strategies
- CDN for static assets
- Database optimization

### Cost Optimization
- Right-sizing instances
- Reserved instances
- Spot instances (where appropriate)
- Data transfer optimization

## 5. Migration to Production

### Pre-Production Checklist
- [ ] All tests passing
- [ ] Security review complete
- [ ] Performance testing done
- [ ] Disaster recovery plan
- [ ] Runbooks documented
- [ ] Monitoring configured
- [ ] Alerts tested
- [ ] Backup strategy verified

### Rollback Strategy
- Blue-green deployment
- Automated rollback
- Feature flags
- Database migrations

## 6. Success Metrics

### Technical
- P99 latency < 2s
- Error rate < 0.1%
- 99.9% availability
- Auto-scaling working

### Business
- User satisfaction
- Cost per query
- Agent success rate
- Platform adoption

---

**Platform Complete!** 🎉
You've built a production-ready AI Agent Platform!
EOF
```

- [ ] **Step 2: Create deployment script**

```bash
cat > stage-6-agent-platform/scripts/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "=== AI Agent Platform Deployment ==="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "AWS CLI required"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "Terraform required"; exit 1; }

# Build and push Docker image
echo "Building Docker image..."
docker build -t ai-platform:latest ../docker

echo "Logging in to ECR..."
$(aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com)

echo "Pushing to ECR..."
docker tag ai-platform:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/ai-platform:latest
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/ai-platform:latest

# Deploy infrastructure
echo "Deploying infrastructure..."
cd ../terraform
terraform init
terraform apply -auto-approve

# Get API endpoint
API_URL=$(terraform output api_endpoint_url)
echo ""
echo "=== Deployment Complete ==="
echo "API Endpoint: $API_URL"
echo "Health Check: $API_URL/health"
echo ""
echo "Test with:"
echo "curl $API_URL/health"
EOF

chmod +x stage-6-agent-platform/scripts/deploy.sh
```

- [ ] **Step 3: Commit final documentation**

```bash
git add stage-6-agent-platform/docs/ stage-6-agent-platform/scripts/
git commit -m "docs: add architecture design and deployment scripts"
```

---

## Completion Checklist

### Infrastructure
- [ ] ECS cluster deployed
- [ ] API Gateway configured
- [ ] Load balancer active
- [ ] X-Ray enabled
- [ ] CloudWatch dashboard
- [ ] Alarms configured

### Application
- [ ] Orchestrator running
- [ ] Agent clients connected
- [ ] Multi-agent patterns working
- [ ] Authentication functional
- [ ] Health checks passing

### Documentation
- [ ] Architecture documented
- [ ] API documented
- [ ] Runbooks created
- [ ] Deployment guide complete

### Testing
- [ ] Integration tests pass
- [ ] Load testing done
- [ ] Security review complete
- [ ] Disaster recovery tested

---

**🎉 CONGRATULATIONS! 🎉**

You've completed the entire AWS AI Terraform Learning Roadmap!

### What You've Built

1. ✅ **Stage 1**: Terraform Foundation - Secure cloud infrastructure
2. ✅ **Stage 2**: AI Chatbot - Serverless LLM applications
3. ✅ **Stage 3**: Document Analysis - Async event-driven systems
4. ✅ **Stage 4**: RAG Knowledge Base - Vector search and embeddings
5. ✅ **Stage 5**: Autonomous Agent - ReAct reasoning and tools
6. ✅ **Stage 6**: AI Agent Platform - Production-ready integration

### Skills Acquired

- Infrastructure as Code with Terraform
- Serverless architecture design
- AI/ML application development
- Vector databases and semantic search
- Agent design and orchestration
- Production deployment and monitoring

### You Are Now

- **Cloud AI Application Architect**
- **Terraform Practitioner**
- **AWS Solutions Expert**
- **AI Systems Designer**
- **Production Engineer**

Ready to build the next generation of AI applications!

---

**Implementation Plan Created:** 2026-03-10
**Estimated Time:** 4-6 weeks
**Status:** Ready to execute

**Next Steps:**
1. Celebrate! 🎉
2. Deploy the platform
3. Build amazing AI applications
4. Share your journey
5. Keep learning!

---

*The complete Learning Roadmap is ready. Happy building!*
