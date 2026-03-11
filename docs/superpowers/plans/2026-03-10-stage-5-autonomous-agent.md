# Stage 5: Autonomous Agent - Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an autonomous AI agent using the ReAct (Reasoning + Acting) pattern, with tool-calling capabilities, Step Functions orchestration, and memory management.

**Architecture:** User Query → Agent Core → ReAct Loop → Tool Registry → Tool Execution → Result Processing → Response

**Tech Stack:** Terraform, AWS Step Functions, Lambda, DynamoDB, Bedrock Claude, Python 3.11

---

## Chunk 1: Project Setup

### Task 1: Create Directory Structure

**Files:**
- Create: `stage-5-autonomous-agent/README.md`
- Create: `stage-5-autonomous-agent/.gitignore`
- Create: `stage-5-autonomous-agent/requirements.txt`
- Create: `stage-5-autonomous-agent/terraform/main.tf`
- Create: `stage-5-autonomous-agent/terraform/variables.tf`
- Create: `stage-5-autonomous-agent/terraform/outputs.tf`
- Create: `stage-5-autonomous-agent/terraform/provider.tf`

- [ ] **Step 1: Create directories**

```bash
mkdir -p stage-5-autonomous-agent/terraform/modules/{step_functions,lambda,dynamodb}
mkdir -p stage-5-autonomous-agent/src/{agent,tools,workflows,utils}
mkdir -p stage-5-autonomous-agent/src/tools/implementations
mkdir -p stage-5-autonomous-agent/tests
mkdir -p stage-5-autonomous-agent/docs
```

- [ ] **Step 2: Create provider.tf** (similar to previous stages)

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
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "autonomous-agent"
}

variable "max_iterations" {
  description = "Maximum agent iterations"
  type        = number
  default     = 10

  validation {
    condition     = var.max_iterations >= 1 && var.max_iterations <= 50
    error_message = "Iterations must be between 1 and 50."
  }
}

variable "max_execution_time" {
  description = "Maximum execution time in seconds"
  type        = number
  default     = 300

  validation {
    condition     = var.max_execution_time >= 60 && var.max_execution_time <= 900
    error_message = "Execution time must be between 60 and 900 seconds."
  }
}

variable "enable_memory" {
  description = "Enable agent memory"
  type        = bool
  default     = true
}

variable "memory_ttl_days" {
  description = "Memory retention in days"
  type        = number
  default     = 30
}

variable "allowed_tools" {
  description = "List of enabled tools"
  type = list(object({
    name        = string
    enabled     = bool
    description = string
  }))
  default = [
    {name = "search", enabled = true, description = "Web search"},
    {name = "query", enabled = true, description = "Database query"},
    {name = "calculate", enabled = true, description = "Calculator"},
    {name = "rag_search", enabled = true, description = "RAG knowledge search"}
  ]
}
```

- [ ] **Step 4: Create requirements.txt**

```bash
cat > stage-5-autonomous-agent/requirements.txt << 'EOF'
# AWS SDK
boto3==1.34.84
botocore==1.34.84

# Agent framework
langchain==0.1.10
langchain-aws==0.1.0
langchain-community==0.0.20

# Validation
pydantic==2.6.1

# Utilities
python-dotenv==1.0.1

# Testing
pytest==8.0.2
pytest-mock==3.12.0
pytest-cov==4.1.0
pytest-asyncio==0.23.4
EOF
```

- [ ] **Step 5: Create README.md**

```bash
cat > stage-5-autonomous-agent/README.md << 'EOF'
# Stage 5: Autonomous Agent

## Learning Objectives

After completing this stage, you will be able to:
- [ ] Implement the ReAct (Reasoning + Acting) pattern
- [ ] Design and register tools for LLM agents
- [ ] Orchestrate complex workflows with Step Functions
- [ ] Implement memory systems for agents
- [ ] Handle multi-step reasoning and error recovery

## Architecture Overview

```
User Query → Agent Core → ReAct Loop
                              ↓
                    ┌──────────┴──────────┐
                    ↓                     ↓
              Tool Registry          Memory Store
                    ↓                     ↓
              Tool Execution        Context Retrieval
                    ↓                     ↓
              Step Functions ──────────────┘
                    ↓
              Result Aggregation → Response
```

## Features

- **ReAct Agent**: Reasoning + Acting loop
- **Tool Registry**: Extensible tool system
- **Memory**: Short-term (conversation) and long-term (episodic)
- **Step Functions**: Orchestration and visualization
- **Error Handling**: Retry and recovery

## ReAct Pattern

The agent follows this loop:

1. **Thought**: Reason about current state
2. **Action**: Choose and execute a tool
3. **Observation**: Observe the result
4. **Repeat** until goal is reached

Example:
```
Thought: I need to search for information
Action: search("latest AI news")
Observation: Found 5 articles...
Thought: I have enough information
Action: finish([summary])
```

## Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| search | Web search | query: str |
| query | Database query | sql: str |
| calculate | Math operations | expression: str |
| rag_search | Knowledge base | question: str |

## Prerequisites

- Completed Stages 1-4
- AWS Account with Bedrock
- Python 3.11+

## Deployment

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Usage

### Direct Invocation

```python
from src.agent.core import Agent

agent = Agent()
result = agent.run(
    task="Find the latest AWS AI news and summarize it",
    tools=["search", "rag_search"]
)
print(result["answer"])
```

### Via Step Functions

```bash
# Start execution
aws stepfunctions start-execution \
  --state-machine-arn <arn> \
  --input '{"task": "Your task here"}'
```

## Tool Development

Create custom tools:

```python
from src.tools.base_tool import BaseTool, tool

@tool("my_tool")
def my_function(param1: str, param2: int) -> str:
    """Tool description for LLM"""
    return f"Result: {param1} {param2}"
```

## Memory System

### Conversation Memory
- Stores recent exchanges
- Context window limited
- Automatically managed

### Episodic Memory
- Stores completed tasks
- Retrieved for similar tasks
- TTL-based expiration

### Semantic Memory
- Stores facts and knowledge
- Vector-based retrieval
- Long-term retention

## Cost Estimate

| Component | Cost |
|-----------|------|
| Lambda | $0.20/1M requests |
| Step Functions | $0.025/state transition |
| DynamoDB | On-demand pricing |
| Bedrock Claude | $3/1M input tokens |

**Estimated monthly:** $20-50 for moderate usage

## Monitoring

```bash
# View Step Functions executions
aws stepfunctions list-executions \
  --state-machine-arn <arn>

# Check DynamoDB memory
aws dynamodb scan --table-name agent-memory

# View CloudWatch logs
aws logs tail /aws/lambda/agent-core --follow
```

## Cleanup

```bash
cd terraform
terraform destroy
```

## Next Steps

After completing this stage:
1. Create custom tools for your use case
2. Experiment with memory systems
3. Optimize reasoning prompts
4. Proceed to Stage 6: Agent Platform
EOF
```

- [ ] **Step 6: Create Python structure**

```bash
touch stage-5-autonomous-agent/src/__init__.py
touch stage-5-autonomous-agent/src/agent/__init__.py
touch stage-5-autonomous-agent/src/tools/__init__.py
touch stage-5-autonomous-agent/src/workflows/__init__.py
touch stage-5-autonomous-agent/src/utils/__init__.py
```

- [ ] **Step 7: Commit**

```bash
git add stage-5-autonomous-agent/
git commit -m "feat: stage-5 initial project structure"
```

---

## Chunk 2: Agent Core Implementation

### Task 2: Create Agent Core with ReAct

**Files:**
- Create: `stage-5-autonomous-agent/src/agent/core.py`
- Create: `stage-5-autonomous-agent/src/agent/reasoning.py`
- Create: `stage-5-autonomous-agent/src/agent/memory.py`
- Create: `stage-5-autonomous-agent/src/tools/registry.py`
- Create: `stage-5-autonomous-agent/src/tools/base_tool.py`

- [ ] **Step 1: Create base tool**

```bash
cat > stage-5-autonomous-agent/src/tools/base_tool.py << 'EOF'
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, Optional
from pydantic import BaseModel, Field
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ToolInput(BaseModel):
    """Base model for tool inputs"""
    pass

class ToolOutput(BaseModel):
    """Base model for tool outputs"""
    success: bool
    result: Any
    error: Optional[str] = None

class BaseTool(ABC):
    """Base class for all agent tools"""

    name: str
    description: str
    input_schema: Type[ToolInput]

    def __init__(self):
        self._validate_tool()

    @abstractmethod
    def run(self, **kwargs) -> ToolOutput:
        """Execute the tool"""
        pass

    def _validate_tool(self):
        """Validate tool configuration"""
        if not self.name:
            raise ValueError("Tool must have a name")
        if not self.description:
            raise ValueError("Tool must have a description")

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""

        schema = {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        if self.input_schema != ToolInput:
            # Build schema from pydantic model
            model_schema = self.input_schema.model_json_schema()
            schema["input_schema"]["properties"] = model_schema.get("properties", {})
            schema["input_schema"]["required"] = model_schema.get("required", [])

        return schema

class tool:
    """Decorator for simple function-based tools"""

    def __init__(self, name: str = None):
        self.name = name

    def __call__(self, func):
        """Convert function to tool"""

        class FunctionTool(BaseTool):
            name = self.name or func.__name__
            description = func.__doc__ or f"Tool: {name}"
            input_schema = ToolInput

            def run(self, **kwargs):
                try:
                    result = func(**kwargs)
                    return ToolOutput(success=True, result=result)
                except Exception as e:
                    logger.error(f"Tool {self.name} failed", extra_data={"error": str(e)})
                    return ToolOutput(success=False, result=None, error=str(e))

        return FunctionTool
EOF
```

- [ ] **Step 2: Create tool registry**

```bash
cat > stage-5-autonomous-agent/src/tools/registry.py << 'EOF'
from typing import Dict, List, Any, Optional
from .base_tool import BaseTool
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ToolRegistry:
    """Registry for available tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool"""

        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")

        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""

        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all tool names"""

        return list(self._tools.keys())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas"""

        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool"""

        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        logger.info(f"Executing tool: {name}", extra_data={"kwargs": kwargs})

        result = tool.run(**kwargs)

        if not result.success:
            logger.error(f"Tool {name} failed", extra_data={"error": result.error})
            raise Exception(result.error)

        return result.result

# Global registry
_registry = ToolRegistry()

def register_tool(tool: BaseTool) -> None:
    """Register tool to global registry"""
    _registry.register(tool)

def get_registry() -> ToolRegistry:
    """Get global registry"""
    return _registry
EOF
```

- [ ] **Step 3: Create memory system**

```bash
cat > stage-5-autonomous-agent/src/agent/memory.py << 'EOF'
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import boto3
import os
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MemoryStore(ABC):
    """Base class for memory stores"""

    @abstractmethod
    def add(self, memory: Dict[str, Any]) -> None:
        """Add memory"""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get memory by key"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memories"""
        pass

class ConversationMemory(MemoryStore):
    """Short-term conversation memory"""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.conversations: Dict[str, List[Dict]] = {}

    def add(self, memory: Dict[str, Any]) -> None:
        """Add to conversation"""

        session_id = memory.get("session_id", "default")
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        self.conversations[session_id].append({
            "role": memory.get("role", "user"),
            "content": memory.get("content", ""),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Prune old turns
        if len(self.conversations[session_id]) > self.max_turns:
            self.conversations[session_id] = self.conversations[session_id][-self.max_turns:]

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get conversation history"""

        return self.conversations.get(key)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search conversations (keyword match)"""

        results = []
        for session_id, turns in self.conversations.items():
            for turn in turns:
                if query.lower() in turn["content"].lower():
                    results.append(turn)
                    if len(results) >= limit:
                        return results
        return results

class EpisodicMemory(MemoryStore):
    """Long-term episodic memory in DynamoDB"""

    def __init__(self):
        self.client = boto3.client("dynamodb")
        self.table_name = os.getenv("MEMORY_TABLE", "agent-memory")
        self.ttl_days = int(os.getenv("MEMORY_TTL_DAYS", "30"))

    def add(self, memory: Dict[str, Any]) -> None:
        """Store episode"""

        import uuid

        episode_id = memory.get("episode_id", str(uuid.uuid4()))

        item = {
            "episode_id": {"S": episode_id},
            "task": {"S": memory.get("task", "")},
            "outcome": {"S": memory.get("outcome", "")},
            "tools_used": {"SS": memory.get("tools_used", [])},
            "created_at": {"S": datetime.utcnow().isoformat()},
            "expire_at": {"N": str(int((datetime.utcnow() + timedelta(days=self.ttl_days)).timestamp()))}
        }

        self.client.put_item(TableName=self.table_name, Item=item)
        logger.info("Stored episode", extra_data={"episode_id": episode_id})

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get episode by ID"""

        response = self.client.get_item(
            TableName=self.table_name,
            Key={"episode_id": {"S": key}}
        )

        if "Item" not in response:
            return None

        return self._from_dynamodb(response["Item"])

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search similar episodes"""

        # Simple scan with filter (production would use GSI or OpenSearch)
        response = self.client.scan(
            TableName=self.table_name,
            FilterExpression=boto3.dynamodb.conditions.Attr("task").contains(query),
            Limit=limit
        )

        return [self._from_dynamodb(item) for item in response.get("Items", [])]

    def _from_dynamodb(self, item: Dict) -> Dict[str, Any]:
        """Convert DynamoDB item to dict"""

        def get_value(attr):
            if "S" in attr:
                return attr["S"]
            elif "N" in attr:
                return int(attr["N"])
            elif "SS" in attr:
                return attr["SS"]
            elif "M" in attr:
                return {k: self._from_dynamodb(v) for k, v in attr["M"].items()}
            return None

        return {k: get_value(v) for k, v in item.items()}

class MemorySystem:
    """Unified memory system"""

    def __init__(self):
        self.conversation = ConversationMemory()
        self.episodic = EpisodicMemory() if os.getenv("ENABLE_MEMORY", "true").lower() == "true" else None

    def add_conversation(self, role: str, content: str, session_id: str = None) -> None:
        """Add to conversation memory"""

        self.conversation.add({
            "role": role,
            "content": content,
            "session_id": session_id or "default"
        })

    def add_episode(self, task: str, outcome: str, tools_used: List[str]) -> None:
        """Add to episodic memory"""

        if self.episodic:
            self.episodic.add({
                "task": task,
                "outcome": outcome,
                "tools_used": tools_used
            })

    def get_context(self, session_id: str = None) -> str:
        """Get conversation context"""

        history = self.conversation.get(session_id or "default")
        if not history:
            return ""

        context_parts = []
        for turn in history[-5:]:  # Last 5 turns
            context_parts.append(f"{turn['role']}: {turn['content']}")

        return "\n".join(context_parts)

    def recall_similar(self, task: str) -> List[Dict[str, Any]]:
        """Recall similar episodes"""

        if self.episodic:
            return self.episodic.search(task)
        return []
EOF
```

- [ ] **Step 4: Create reasoning engine**

```bash
cat > stage-5-autonomous-agent/src/agent/reasoning.py << 'EOF'
from typing import List, Dict, Any, Optional
import json
import re
from ..tools.registry import get_registry
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ReActEngine:
    """ReAct (Reasoning + Acting) engine"""

    def __init__(self, llm_service, max_iterations: int = 10):
        self.llm = llm_service
        self.max_iterations = max_iterations
        self.registry = get_registry()

        self.system_prompt = """You are a helpful AI assistant with access to tools.

Follow this format:
Thought: [your reasoning about what to do next]
Action: [tool name]
Action Input: [JSON input for the tool]
Observation: [result of the action]
... (repeat Thought/Action/Observation)

When you have enough information to answer:
Thought: [final reasoning]
Action: finish
Action Input: {"answer": "[your final answer]"}

Available tools:
{tools}

Remember:
- Start with Thought to reason about the task
- Choose appropriate actions
- Use observations to inform next steps
- End with finish action when done
"""

    def run(
        self,
        task: str,
        available_tools: List[str],
        context: str = None
    ) -> Dict[str, Any]:
        """Run ReAct loop"""

        # Build tools list
        tool_schemas = [self.registry.get(name).get_schema()
                       for name in available_tools
                       if self.registry.get(name)]

        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tool_schemas
        ])

        prompt = self.system_prompt.format(tools=tools_desc)

        if context:
            prompt += f"\n\nConversation context:\n{context}\n"

        prompt += f"\n\nTask: {task}\n"

        history = []
        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1
            logger.info(f"ReAct iteration {iterations}")

            # Get LLM response
            response = self.llm.invoke_claude(
                prompt=prompt + "\n" + "\n".join(history[-5:]),
                max_tokens=1000
            )

            response_text = response["response"].strip()
            logger.info("LLM response", extra_data={"response": response_text})

            # Parse response
            thought, action, action_input = self._parse_react_response(response_text)

            if action == "finish":
                logger.info("Task completed")
                return {
                    "status": "completed",
                    "answer": action_input.get("answer", "Task completed"),
                    "iterations": iterations,
                    "history": history
                }

            # Execute action
            try:
                result = self.registry.execute(action, **action_input)
                observation = str(result)

                logger.info("Action success", extra_data={"action": action, "result": observation})

            except Exception as e:
                observation = f"Error: {str(e)}"
                logger.error("Action failed", extra_data={"action": action, "error": str(e)})

            # Add to history
            history.append(f"Thought: {thought}")
            history.append(f"Action: {action}")
            history.append(f"Action Input: {json.dumps(action_input)}")
            history.append(f"Observation: {observation}")

        # Max iterations reached
        logger.warning("Max iterations reached")
        return {
            "status": "incomplete",
            "answer": "Maximum iterations reached",
            "iterations": iterations,
            "history": history
        }

    def _parse_react_response(self, response: str) -> tuple:
        """Parse ReAct format response"""

        thought_match = re.search(r"Thought:\s*(.+?)(?=\n(?:Action|Observation|$))", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(.+?)(?=\n|$)", response, re.IGNORECASE)
        input_match = re.search(r"Action Input:\s*(.+?)(?=\n(?:Thought|Action|Observation|$))", response, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else "I need to proceed with the task"
        action = action_match.group(1).strip().lower() if action_match else "unknown"

        try:
            action_input = json.loads(input_match.group(1).strip()) if input_match else {}
        except json.JSONDecodeError:
            action_input = {"raw": input_match.group(1).strip()} if input_match else {}

        return thought, action, action_input
EOF
```

- [ ] **Step 5: Create agent core**

```bash
cat > stage-5-autonomous-agent/src/agent/core.py << 'EOF'
from typing import List, Dict, Any, Optional
from .reasoning import ReActEngine
from .memory import MemorySystem
from ..services.llm_service import LLMService
from ..tools.registry import get_registry
from ..utils.logger import get_logger

logger = get_logger(__name__)

class Agent:
    """Autonomous agent with ReAct reasoning"""

    def __init__(
        self,
        max_iterations: int = 10,
        enable_memory: bool = True
    ):
        self.llm = LLMService()
        self.engine = ReActEngine(self.llm, max_iterations)
        self.memory = MemorySystem() if enable_memory else None
        self.registry = get_registry()

        logger.info("Agent initialized", extra_data={
            "max_iterations": max_iterations,
            "enable_memory": enable_memory
        })

    def run(
        self,
        task: str,
        tools: List[str],
        session_id: str = None,
        context: str = None
    ) -> Dict[str, Any]:
        """Execute a task"""

        logger.info("Agent run started", extra_data={"task": task})

        # Add user message to memory
        if self.memory:
            self.memory.add_conversation("user", task, session_id)

        # Get conversation context
        conversation_context = context
        if self.memory and not conversation_context:
            conversation_context = self.memory.get_context(session_id)

        # Recall similar episodes
        similar = []
        if self.memory:
            similar = self.memory.recall_similar(task)
            logger.info("Recalled episodes", extra_data={"count": len(similar)})

        # Run reasoning loop
        result = self.engine.run(
            task=task,
            available_tools=tools,
            context=conversation_context
        )

        # Store episode
        if self.memory:
            self.memory.add_episode(
                task=task,
                outcome=result["answer"],
                tools_used=tools
            )
            self.memory.add_conversation("assistant", result["answer"], session_id)

        return {
            "task": task,
            "answer": result["answer"],
            "status": result["status"],
            "iterations": result["iterations"],
            "tools_used": tools,
            "session_id": session_id
        }

    def chat(
        self,
        message: str,
        session_id: str = None,
        tools: List[str] = None
    ) -> str:
        """Simple chat interface"""

        if not tools:
            tools = self.registry.list_tools()

        result = self.run(
            task=message,
            tools=tools,
            session_id=session_id
        )

        return result["answer"]

    def reset_memory(self, session_id: str = None) -> None:
        """Reset conversation memory"""

        if self.memory:
            if session_id:
                # Clear specific session
                self.memory.conversation.conversations.pop(session_id, None)
            else:
                # Clear all
                self.memory.conversation.conversations.clear()
            logger.info("Memory reset", extra_data={"session_id": session_id})
EOF
```

- [ ] **Step 6: Commit agent core**

```bash
git add stage-5-autonomous-agent/src/agent/ stage-5-autonomous-agent/src/tools/
git commit -m "feat: implement agent core with ReAct reasoning and memory"
```

---

## Chunk 3: Tool Implementations

### Task 3: Create Standard Tools

**Files:**
- Create: `stage-5-autonomous-agent/src/tools/implementations/search_tool.py`
- Create: `stage-5-autonomous-agent/src/tools/implementations/calculate_tool.py`
- Create: `stage-5-autonomous-agent/src/tools/implementations/rag_tool.py`
- Create: `stage-5-autonomous-agent/src/tools/implementations/__init__.py`

- [ ] **Step 1: Create search tool**

```bash
cat > stage-5-autonomous-agent/src/tools/implementations/search_tool.py << 'EOF'
from typing import Dict, Any
import requests
from ..base_tool import BaseTool, ToolInput, ToolOutput, tool

class SearchInput(ToolInput):
    query: str
    num_results: int = 5

@tool("search")
def search_tool(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Search the web for information. Returns relevant search results."""

    # Using a free search API (in production, use AWS Kendra or similar)
    try:
        # Placeholder - implement with actual search API
        results = [
            {
                "title": f"Result for: {query}",
                "url": "https://example.com",
                "snippet": f"Information about {query}"
            }
        ]

        return {
            "results": results[:num_results],
            "query": query
        }

    except Exception as e:
        return {"error": str(e)}
EOF
```

- [ ] **Step 2: Create calculate tool**

```bash
cat > stage-5-autonomous-agent/src/tools/implementations/calculate_tool.py << 'EOF'
from typing import Union
from ..base_tool import BaseTool, ToolInput, ToolOutput, tool

class CalculateInput(ToolInput):
    expression: str

@tool("calculate")
def calculate_tool(expression: str) -> Union[int, float, str]:
    """Calculate mathematical expressions safely. Supports +, -, *, /, **, ()"""

    try:
        # Safe evaluation
        result = eval(expression, {"__builtins__": {}}, {
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        })
        return result
    except Exception as e:
        return f"Calculation error: {str(e)}"
EOF
```

- [ ] **Step 3: Create RAG search tool**

```bash
cat > stage-5-autonomous-agent/src/tools/implementations/rag_tool.py << 'EOF'
import os
from typing import Dict, Any, List
from ..base_tool import BaseTool, ToolInput, ToolOutput, tool

class RAGSearchInput(ToolInput):
    question: str
    top_k: int = 5

@tool("rag_search")
def rag_search_tool(question: str, top_k: int = 5) -> str:
    """Search the knowledge base using RAG (Retrieval Augmented Generation)."""

    try:
        # Import RAG service from Stage 4
        import sys
        sys.path.append("../../stage-4-rag-knowledge-base/src")
        from services.rag_service import RAGService

        rag = RAGService()
        result = rag.query(question, top_k=top_k)

        return f"Based on the knowledge base: {result['answer']}"

    except Exception as e:
        return f"RAG search error: {str(e)}"
EOF
```

- [ ] **Step 4: Create tool initialization**

```bash
cat > stage-5-autonomous-agent/src/tools/implementations/__init__.py << 'EOF'
from .search_tool import search_tool
from .calculate_tool import calculate_tool
from .rag_tool import rag_search_tool
from ..registry import register_tool

# Register all tools
def register_default_tools():
    """Register default agent tools"""

    from ..base_tool import FunctionTool

    # Search tool
    register_tool(FunctionTool(
        name="search",
        description="Web search for information",
        func=search_tool
    ))

    # Calculator
    register_tool(FunctionTool(
        name="calculate",
        description="Calculate mathematical expressions",
        func=calculate_tool
    ))

    # RAG search
    register_tool(FunctionTool(
        name="rag_search",
        description="Search knowledge base with RAG",
        func=rag_search_tool
    ))
EOF
```

- [ ] **Step 5: Commit tools**

```bash
git add stage-5-autonomous-agent/src/tools/implementations/
git commit -m "feat: add standard tools (search, calculate, rag_search)"
```

---

## Chunk 4: Step Functions Workflow

### Task 4: Create Orchestration

**Files:**
- Create: `stage-5-autonomous-agent/terraform/modules/step_functions/main.tf`
- Create: `stage-5-autonomous-agent/src/workflows/agent_flow.asl.json`

- [ ] **Step 1: Create Step Functions module**

```hcl
# Lambda function for Step Functions callback
resource "aws_lambda_function" "agent" {
  function_name = "${var.function_name}-agent"
  role           = var.lambda_role_arn
  handler        = "agent.handler"
  runtime        = "python3.11"
  timeout        = 300

  # Code would be uploaded separately
  filename      = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")

  environment {
    variables = {
      MEMORY_TABLE     = var.memory_table_name
      ENABLE_MEMORY    = var.enable_memory
      MAX_ITERATIONS   = var.max_iterations
    }
  }
}

# State machine
resource "aws_sfn_state_machine" "agent" {
  name     = "${var.name}-workflow"
  role_arn = var.execution_role_arn

  definition = templatefile("${path.module}/workflow.asl.json", {
    agent_function_arn = aws_lambda_function.agent.arn
    max_iterations = var.max_iterations
  })

  # Logging
  logging_configuration {
    level                  = "ALL"
    include_execution_data = true
    destinations {
      cloudwatch_logs_log_group {
        log_group_arn = aws_cloudwatch_log_group.sfn.arn
      }
    }
  }

  # X-Ray tracing
  tracing_configuration {
    enabled = var.enable_tracing
  }

  tags = var.tags
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/vendedlogs/states/${var.name}-workflow"
  retention_in_days = var.log_retention

  tags = var.tags
}

# EventBridge rule for scheduled tasks
resource "aws_cloudwatch_event_rule" "scheduled" {
  count = var.schedule_expression != null ? 1 : 0

  name                = "${var.name}-scheduled"
  schedule_expression  = var.schedule_expression
  event_bus_name      = "default"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "scheduled" {
  count = var.schedule_expression != null ? 1 : 0

  rule           = aws_cloudwatch_event_rule.scheduled[0].name
  event_bus_name = "default"
  target_id      = "AgentWorkflow"
  arn            = aws_sfn_state_machine.agent.arn

  input = jsonencode({
    task = "Execute scheduled agent task"
  })
}
```

- [ ] **Step 2: Create workflow ASL**

```bash
cat > stage-5-autonomous-agent/src/workflows/agent_flow.asl.json << 'EOF'
{
  "Comment": "Autonomous Agent Workflow",
  "StartAt": "InitializeAgent",
  "States": {
    "InitializeAgent": {
      "Type": "Task",
      "Resource": "${agent_function_arn}",
      "Next": "ExecuteReasoning",
      "Retry": [{
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }],
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "ExecutionFailed"
      }]
    },
    "ExecuteReasoning": {
      "Type": "Task",
      "Resource": "${agent_function_arn}",
      "Next": "CheckCompletion",
      "Retry": [{
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }],
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "ExecutionFailed"
      }]
    },
    "CheckCompletion": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.status",
        "StringEquals": "completed",
        "Next": "ExecutionSucceeded"
      }, {
        "Variable": "$.iterations",
        "NumericGreaterThan": ${max_iterations},
        "Next": "MaxIterationsExceeded"
      }],
      "Default": "ExecuteReasoning"
    },
    "ExecutionSucceeded": {
      "Type": "Succeed"
    },
    "ExecutionFailed": {
      "Type": "Fail",
      "Error": "ExecutionFailed",
      "Cause": "Agent execution failed"
    },
    "MaxIterationsExceeded": {
      "Type": "Fail",
      "Error": "MaxIterationsExceeded",
      "Cause": "Agent exceeded maximum iterations"
    }
  }
}
EOF
```

- [ ] **Step 3: Commit workflow**

```bash
git add stage-5-autonomous-agent/terraform/modules/step_functions/ stage-5-autonomous-agent/src/workflows/
git commit -m "feat: add Step Functions workflow for agent orchestration"
```

---

## Chunk 5: Testing & Documentation

### Task 5: Tests and Design Doc

- [ ] **Step 1: Create tests**

```bash
cat > stage-5-autonomous-agent/tests/test_agent.py << 'EOF'
import pytest
from unittest.mock import Mock, patch
from src.agent.core import Agent
from src.agent.memory import ConversationMemory, EpisodicMemory

class TestAgent:
    def test_agent_initialization(self):
        agent = Agent(max_iterations=5)
        assert agent is not None
        assert agent.engine.max_iterations == 5

    @patch("src.agent.reasoning.ReActEngine.run")
    def test_agent_run(self, mock_react):
        mock_react.return_value = {
            "status": "completed",
            "answer": "Test answer",
            "iterations": 3
        }

        agent = Agent(enable_memory=False)
        result = agent.run(
            task="Test task",
            tools=["search"]
        )

        assert result["status"] == "completed"
        assert result["answer"] == "Test answer"

    def test_memory_system(self):
        memory = ConversationMemory()
        memory.add({"role": "user", "content": "Hello", "session_id": "test"})

        history = memory.get("test")
        assert len(history) == 1
        assert history[0]["content"] == "Hello"
EOF
```

- [ ] **Step 2: Create design document**

```bash
cat > stage-5-autonomous-agent/docs/design.md << 'EOF'
# Stage 5: Autonomous Agent - Architecture Design

## 1. Architecture Overview

```
User → API Gateway → Lambda (Agent Core)
                              ↓
                        ReAct Engine
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              Tool Registry        Memory System
                    ↓                   ↓
              Tool Execution      Context Retrieval
                    ↓                   ↓
              Step Functions ─────────────┘
                    ↓
              Response Aggregation
```

## 2. Design Decisions

### Decision 1: ReAct vs Other Agent Patterns

**Problem:** Which agent reasoning pattern?

**Options:**
- ReAct: Reasoning + Acting
- Chain of Thought: Pure reasoning
- Plan-and-Execute: Plan first, then execute
- Reflex: Direct action

**Selection:** ReAct

**Pros:**
- ✅ Transparent reasoning process
- ✅ Flexible tool use
- ✅ Self-correcting
- ✅ Proven effectiveness

**Cons:**
- ❌ Can be verbose
- ❌ May get stuck in loops
- ❌ Requires good tool descriptions

**Why ReAct?**
Best balance of capability and interpretability for learning.

---

### Decision 2: Orchestration Engine

**Problem:** How to orchestrate agent execution?

**Selection:** Step Functions

**Pros:**
- ✅ Visual workflow
- ✅ Built-in error handling
- ✅ Easy debugging
- ✅ AWS native

**Cons:**
- ❌ State machine complexity
- ❌ Execution time limits
- ❌ Cost per transition

**Why Step Functions?**
Observability and visualization are critical for learning.

---

### Decision 3: Memory Architecture

**Problem:** How to implement agent memory?

**Selection:** Hybrid approach

**Components:**
1. Conversation Memory: In-memory, session-scoped
2. Episodic Memory: DynamoDB, long-term
3. Semantic Memory: (Future) Vector-based

**Trade-offs:**
- Simplicity vs Capability
- Cost vs Retention
- Retrieval Speed vs Accuracy

---

### Decision 4: Tool Design Pattern

**Problem:** How to structure tools?

**Selection:** Class-based with decorator alternative

**Pattern:**
```python
# Class-based
class MyTool(BaseTool):
    name = "my_tool"
    def run(self, **kwargs):
        pass

# Function-based
@tool("my_tool")
def my_function(**kwargs):
    pass
```

**Benefits:**
- Flexibility for different use cases
- Type safety with pydantic
- Easy to extend

---

## 3. ReAct Prompt Engineering

### System Prompt Structure

1. Role definition
2. Tool descriptions
3. Format instructions
4. Examples (few-shot)
5. Constraints

### Prompt Optimization

| Issue | Solution |
|-------|----------|
| Looping | Add iteration counter to context |
| Hallucination | Verify tool outputs |
| Wrong tool | Improve descriptions |
| Premature finish | Add completion criteria |

---

## 4. Error Handling

### Tool Failures
- Retry with exponential backoff
- Fallback to alternative tools
- Graceful degradation

### Max Iterations
- Return partial results
- Suggest next steps
- Log for analysis

### Memory Errors
- Continue without memory
- Use local fallback
- Alert monitoring

---

## 5. Cost Analysis

| Component | Cost |
|-----------|------|
| Lambda | $0.20/1M requests |
| Step Functions | $0.025/transition |
| DynamoDB | On-demand |
| Bedrock Claude | $3/1M input tokens |

**Per execution:** ~$0.01-0.05
**Monthly (1K execs):** ~$10-50

---

**Design Document Created:** 2026-03-10
EOF
```

- [ ] **Step 3: Commit**

```bash
git add stage-5-autonomous-agent/tests/ stage-5-autonomous-agent/docs/
git commit -m "test: add agent tests; docs: add architecture design"
```

---

## Completion Checklist

- [ ] Agent core with ReAct implemented
- [ ] Tool registry functional
- [ ] Memory system working
- [ ] Step Functions workflow deployed
- [ ] Standard tools created
- [ ] Tests passing
- [ ] Documentation complete

---

**Implementation Plan Created:** 2026-03-10
**Estimated Time:** 3-4 weeks
**Next:** Begin implementation
