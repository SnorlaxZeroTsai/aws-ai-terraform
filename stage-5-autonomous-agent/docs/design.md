# Stage 5: Autonomous Agent - Design Document

**Date:** 2026-03-12
**Status:** Implementation Complete
**Author:** Claude Code

---

## Overview

This document describes the design and implementation of Stage 5: Autonomous Agent, a complete AI agent system built on AWS using the ReAct (Reasoning + Acting) pattern.

### Architecture Goals

1. **Autonomous Reasoning**: Agent can plan and execute multi-step tasks
2. **Tool Integration**: Dynamic tool calling for diverse capabilities
3. **Memory Management**: Multi-tier memory for context retention
4. **Orchestration**: Step Functions for visual workflow management
5. **Scalability**: Serverless architecture for cost-effective scaling

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                        User Request                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Core (Lambda)                     │
│  - ReAct Loop Implementation                                │
│  - Memory Retrieval/Storage                                 │
│  - Context Management                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────────┐      ┌──────────────────────────┐
│  Reasoning Engine    │      │    Tool Registry         │
│  (Lambda)            │      │  - Tool Discovery        │
│  - LLM Inference     │      │  - Parameter Validation  │
│  - Action Selection  │      │  - Execution Wrapper     │
└──────────────────────┘      └───────────┬──────────────┘
                                           │
                                           ▼
                               ┌──────────────────────────┐
                               │   Tool Executor          │
                               │   (Lambda)               │
                               │   - Web Search           │
                               │   - Database Query       │
                               │   - File Operations      │
                               └──────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Memory Systems (DynamoDB)                 │
│  - Conversation Memory (24h TTL)                            │
│  - Episodic Memory (7d TTL)                                 │
│  - Semantic Memory (Persistent)                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Step Functions Orchestrator                    │
│  - Visual Workflow                                         │
│  - Error Handling                                          │
│  - Retry Logic                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Orchestration Strategy

### Choice: Step Functions vs Alternatives

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Step Functions** | ✅ Visual workflow management<br>✅ Built-in error handling<br>✅ Native AWS integration<br>✅ Automatic retries<br>✅ Pay-per-use | ❌ 256KB state limit<br>❌ Complex conditionals<br>✅ **CHOSEN** | |
| Custom Orchestrator | ✅ Full flexibility<br>✅ No state limits | ❌ Maintenance burden<br>❌ Observability challenges<br>❌ Need to build retry logic | |
| LangChain | ✅ AI-optimized<br>✅ Rich ecosystem | ❌ Heavy abstraction<br>❅ Learning curve<br>❌ Less control | |

### Why Step Functions?

1. **Visibility**: Visual workflow helps debug agent reasoning
2. **Reliability**: Built-in retry and error handling
3. **Integration**: Native Lambda and DynamoDB support
4. **Cost**: Pay-per-use pricing model
5. **Observability**: CloudWatch Logs integration

### Mitigating Limitations

- **State Size**: Store large context in DynamoDB, pass references in state
- **Complex Logic**: Use Lambda functions for complex decision making
- **Iteration Limits**: Configure max iterations as variable

---

## Agent Design Patterns

### ReAct Pattern Implementation

The agent follows the ReAct (Reasoning + Acting) loop:

1. **Observe**: Gather context from memory and tools
2. **Reason**: Use LLM to determine next action
3. **Act**: Execute tool or generate response
4. **Reflect**: Store results in memory
5. **Repeat**: Until completion or max iterations

```python
for iteration in range(max_iterations):
    # Reason about next action
    reasoning = reasoning_engine.reason(context)

    # Check if we should respond
    if reasoning.action.type == "respond":
        return generate_response(context)

    # Execute tool
    result = tool_executor.execute(
        reasoning.action.tool,
        reasoning.action.parameters
    )

    # Update context and continue
    context.update(result)
```

### Tool System Design

#### Tool Interface

All tools implement `BaseTool` with:

- `name`: Unique identifier
- `description`: What the tool does
- `parameters`: Schema of expected inputs
- `execute()`: Implementation
- `validate_parameters()`: Input validation

#### Tool Categories

1. **Information**: Web search, news search
2. **Database**: DynamoDB query, SQL query
3. **File**: Read, write, list files
4. **Analysis**: JSON parsing, data transformation

#### Tool Registration

Tools are auto-discovered from `src/tools/implementations/`:

```python
registry.register_tools_from_directory('src/tools/implementations')
```

---

## Memory Architecture

### Three-Tier Memory System

#### 1. Conversation Memory (Short-term)

**Purpose**: Track dialogue history
**Storage**: DynamoDB
**TTL**: 24 hours
**Schema**:
- Partition Key: `session_id`
- Sort Key: `timestamp`
- Attributes: `role`, `content`, `metadata`

**Use Cases**:
- Recent messages
- Conversation context
- User preferences (temporary)

#### 2. Episodic Memory (Medium-term)

**Purpose**: Remember specific events
**Storage**: DynamoDB
**TTL**: 7 days
**Schema**:
- Partition Key: `episode_id`
- Sort Key: `timestamp`
- GSI: `session_id` → `timestamp`
- Attributes: `type`, `data`

**Use Cases**:
- Tool execution results
- Errors and failures
- User feedback
- Learning from mistakes

#### 3. Semantic Memory (Long-term)

**Purpose**: Store learned knowledge
**Storage**: DynamoDB
**TTL**: None (persistent)
**Schema**:
- Partition Key: `memory_id`
- GSI: `concept` → `memory_id`
- Attributes: `concept`, `knowledge`, `confidence`

**Use Cases**:
- Learned patterns
- Facts about users
- Best practices
- Domain knowledge

### Memory Retrieval Strategy

```python
# Priority: Recent → Relevant → General
1. Query conversation memory (last 10 messages)
2. Search episodic memory by session/concept
3. Search semantic memory by keywords
4. Merge and rank by relevance
```

---

## Technology Stack

### Infrastructure

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Step Functions** | Orchestration | 10 max iterations |
| **Lambda** | Compute | Python 3.11, 512MB, 5min timeout |
| **DynamoDB** | Memory | On-demand (PAY_PER_REQUEST) |
| **S3** | Tool Definitions | Server-side encryption |
| **CloudWatch** | Logging | 7-day retention |

### Python Libraries

```python
# AWS SDK
boto3==1.34.84

# Validation
pydantic==2.6.3

# Testing
pytest==8.1.1
moto==5.3.5
```

---

## Error Handling Strategy

### Retry Logic

```python
# Step Functions automatic retry
{
  "Retry": [
    {
      "ErrorEquals": ["States.TaskFailed"],
      "IntervalSeconds": 2,
      "MaxAttempts": 3,
      "BackoffRate": 2.0
    }
  ]
}
```

### Error Categories

1. **Transient Errors**: Network timeouts, throttling
   - Strategy: Retry with exponential backoff

2. **Tool Errors**: Invalid parameters, tool failures
   - Strategy: Log to episodic memory, try alternative tool

3. **LLM Errors**: Rate limits, invalid responses
   - Strategy: Retry with simplified prompt

4. **System Errors**: Lambda timeouts, OOM
   - Strategy: Fail gracefully, return error to user

### Fallback Mechanisms

```python
try:
    result = execute_primary_tool()
except Exception:
    # Try alternative tool
    result = execute_alternative_tool()

    # Or respond with partial information
    if result.failed:
        return "I couldn't complete the task, but here's what I found..."
```

---

## Security Considerations

### IAM Permissions

- **Principle of Least Privilege**: Each Lambda has minimal required permissions
- **Resource-Based Policies**: Specific ARNs, not wildcards
- **No Admin Access**: No `*` permissions

### Data Protection

- **Encryption at Rest**: S3 SSE-S3, DynamoDB encryption
- **Encryption in Transit**: All AWS API calls use TLS
- **No Secrets in Code**: Use environment variables
- **TTL on Sensitive Data**: Auto-expire conversation memory

### Tool Security

```python
# Path traversal prevention
if '..' in file_path or file_path.startswith('/'):
    return error("Invalid file path")

# SQL injection prevention
dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE']
if any(kw in query.upper() for kw in dangerous_keywords):
    return error("Dangerous operations not allowed")
```

---

## Performance Optimization

### Lambda Optimization

1. **Memory**: 512MB (balance of CPU and cost)
2. **Timeout**: 300s (5 minutes, max for Step Functions)
3. **Concurrency**: 1000 (AWS default)
4. **Cold Starts**: Minimize by keeping functions warm

### DynamoDB Optimization

1. **Capacity Mode**: On-demand for flexibility
2. **TTL**: Auto-expire old data
3. **GSIs**: Optimized for query patterns
4. **Point-in-Time Recovery**: Enabled

### Cost Optimization

| Component | Strategy | Savings |
|-----------|----------|---------|
| Lambda | Right-sizing memory | 30-50% |
| DynamoDB | TTL on ephemeral data | 40-60% |
| Step Functions | Optimize state transitions | 20-30% |

---

## Monitoring & Observability

### CloudWatch Metrics

- **Execution Count**: Agent invocations
- **Error Rate**: Failed executions
- **Iteration Count**: Average iterations per query
- **Tool Usage**: Most/least used tools

### Logging Strategy

```python
# Structured logging
logger.info({
    "event": "tool_execution",
    "tool": tool_name,
    "duration_ms": duration,
    "success": True
})
```

### Alerting

- **High Error Rate**: >5% failure rate
- **Long Executions**: >8 iterations
- **Cost Spike**: Daily budget exceeded

---

## Testing Strategy

### Unit Tests

```python
def test_tool_execution():
    tool = WebSearchTool()
    result = tool.execute(query="AI news")
    assert result.success is True
    assert "results" in result.data
```

### Integration Tests

```python
def test_agent_workflow():
    agent = Agent()
    result = agent.run("Search for latest AI news")
    assert result["status"] == "success"
    assert len(result["response"]) > 0
```

### End-to-End Tests

```bash
# Deploy and test
terraform apply
aws stepfunctions start-execution --state-machine-arn $ARN
```

---

## Limitations & Future Improvements

### Current Limitations

1. **State Size**: 256KB limit in Step Functions
   - **Workaround**: Store large context in DynamoDB

2. **Tool Discovery**: Manual registration
   - **Future**: Auto-discovery with decorators

3. **Memory Search**: Simple keyword matching
   - **Future**: Vector embeddings for semantic search

4. **Concurrent Tools**: Sequential execution only
   - **Future**: Parallel tool execution

### Potential Enhancements

1. **Multi-Agent Collaboration**: Agents working together
2. **Human-in-the-Loop**: Approval for sensitive actions
3. **Tool Composition**: Chaining multiple tools
4. **Learning from Feedback**: Improve based on user ratings
5. **Advanced Memory**: Vector database for semantic search

---

## Deployment Guide

### Prerequisites

1. AWS Account with appropriate permissions
2. Terraform >= 1.0
3. Python 3.11+
4. Completed Stage 1 (VPC infrastructure)

### Deployment Steps

```bash
# 1. Configure variables
cd terraform
cp terraform.tfvars.template terraform.tfvars
# Edit terraform.tfvars

# 2. Initialize
terraform init

# 3. Review plan
terraform plan

# 4. Deploy
terraform apply

# 5. Note outputs
terraform output
```

### Verification

```bash
# Check state machine
aws stepfunctions describe-state-machine --state-machine-arn $ARN

# Test execution
aws stepfunctions start-execution \
  --state-machine-arn $ARN \
  --input '{"query": "Test query"}'
```

---

## Cost Estimate

### Monthly Costs (us-east-1)

| Component | Usage | Cost |
|-----------|-------|------|
| Step Functions | 10,000 transitions/day | $7.50/mo |
| Lambda | 5,000 invocations/day | $0.75/mo |
| DynamoDB | 100K reads, 50K writes/day | $2.50/mo |
| CloudWatch Logs | 5GB stored | $2.30/mo |
| **Total** | | **$13.05/mo** |

### Free Tier Impact

- Lambda: 400K GB-seconds free (covers most usage)
- DynamoDB: 25GB storage + 200 WCUs free
- CloudWatch Logs: 5GB ingestion free

**With Free Tier**: ~$5/mo primarily for Step Functions

---

## References

- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Step Functions Best Practices](https://docs.aws.amazon.com/step-functions/latest/dg/best-practices.html)
- [Lambda Performance Optimization](https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html)
- [DynamoDB Performance](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html)

---

**Document Status**: Complete
**Last Updated**: 2026-03-12
**Version**: 1.0
