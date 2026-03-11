# Stage 5: Autonomous Agent

An autonomous AI agent system built with AWS Step Functions, Lambda, DynamoDB, and Bedrock Claude, implementing the ReAct (Reasoning + Acting) pattern.

## Overview

This stage implements a complete autonomous agent capable of:
- **ReAct Pattern**: Reasoning before acting
- **Tool Calling**: Dynamic tool selection and execution
- **Memory Management**: Short-term and long-term memory systems
- **Step Functions Orchestration**: Visual workflow management
- **Error Recovery**: Graceful handling of failures

## Architecture

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

## Components

### Infrastructure (Terraform)
- **Step Functions**: State machine for agent workflow
- **Lambda**: Agent core, tool executor, reasoning engine
- **DynamoDB**: Memory storage (conversations, episodic, semantic)
- **S3**: Tool definitions and configurations
- **IAM**: Roles and policies for secure access

### Python Code
- **Agent Core**: Base agent class with ReAct loop
- **Reasoning Engine**: LLM-based decision making
- **Memory System**: Multi-tier memory management
- **Tool Registry**: Dynamic tool registration
- **Sample Tools**: Web search, database query, file operations

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- Python 3.11+
- Completed Stage 1 (VPC infrastructure)
- AWS CLI configured

## Deployment

### 1. Configure Variables

```bash
cd terraform
cp terraform.tfvars.template terraform.tfvars
# Edit terraform.tfvars with your values
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Deploy

```bash
terraform apply
```

### 5. Note Outputs

After deployment, note the Step Functions state machine ARN and API endpoint.

## Usage

### Testing the Agent

```bash
cd ../src
python -m pytest tests/
```

### Running the Agent

```python
from src.agent.core import Agent

agent = Agent()
result = agent.run("What's the weather like today?")
print(result)
```

## Memory Architecture

### Conversation Memory
- Short-term context
- Recent interactions
- TTL: 24 hours

### Episodic Memory
- Specific events
- Tool execution results
- TTL: 7 days

### Semantic Memory
- Knowledge base
- Learned patterns
- Persistent

## Tool System

### Creating Custom Tools

```python
from src.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"

    def execute(self, **kwargs):
        # Implementation
        return result
```

### Registering Tools

Tools are automatically discovered from `src/tools/implementations/` and registered with the tool registry.

## Cost Estimation

Monthly costs (us-east-1):
- Step Functions: ~$0.025 per 1,000 state transitions
- Lambda: ~$0.20 per 1M requests (free tier covers most)
- DynamoDB: ~$1.25 per 1M write operations
- Bedrock: Pay-per-use (varies by model)

**Estimated monthly cost**: $5-20 for moderate usage

## Monitoring

View agent executions in AWS Console:
- Step Functions: See execution history
- CloudWatch Logs: Debug logs
- DynamoDB: Query memory states

## Troubleshooting

### Agent Stuck in Loop
- Check `max_iterations` variable
- Review reasoning logs in CloudWatch

### Tool Execution Fails
- Verify IAM permissions
- Check tool definitions in S3
- Review Lambda logs

### Memory Not Persisting
- Check DynamoDB capacity
- Verify TTL settings
- Review IAM policies

## Next Steps

Proceed to **Stage 6: Agent Platform Integration** to combine all stages into a complete AI platform.

## Learning Objectives

After completing this stage, you should understand:
- ✅ ReAct pattern implementation
- ✅ Tool calling architecture
- ✅ Step Functions for orchestration
- ✅ Memory management systems
- ✅ Error handling and recovery

## References

- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)
- [Bedrock Claude](https://docs.aws.amazon.com/bedrock/)

## License

MIT
