"""Agent core module implementing the ReAct pattern.

This module provides the base Agent class that orchestrates:
- Reasoning loop using LLM
- Tool selection and execution
- Memory management
- Error handling and recovery
"""

import os
import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from utils import get_env_var, get_aws_client, decimal_to_float

class Agent:
    """Autonomous agent using ReAct pattern.

    The agent follows the ReAct (Reasoning + Acting) pattern:
    1. Observe the current state
    2. Reason about the next action
    3. Act by executing a tool or responding
    4. Repeat until completion or max iterations
    """

    def __init__(
        self,
        bedrock_client: Optional[Any] = None,
        dynamodb_client: Optional[Any] = None,
        s3_client: Optional[Any] = None
    ):
        """Initialize the agent.

        Args:
            bedrock_client: Optional boto3 Bedrock client
            dynamodb_client: Optional boto3 DynamoDB client
            s3_client: Optional boto3 S3 client
        """
        self.bedrock_client = bedrock_client or get_aws_client('bedrock-runtime')
        self.dynamodb_client = dynamodb_client or get_aws_client('dynamodb')
        self.s3_client = s3_client or get_aws_client('s3')

        self.conversation_table = get_env_var('CONVERSATION_TABLE')
        self.episodic_table = get_env_var('EPISODIC_TABLE')
        self.semantic_table = get_env_var('SEMANTIC_TABLE')
        self.tool_bucket = get_env_var('TOOL_BUCKET')
        self.model_id = get_env_var('BEDROCK_MODEL_ID')
        self.max_iterations = int(get_env_var('MAX_ITERATIONS', '10'))

        self._tool_registry = None

    @property
    def tool_registry(self) -> Dict[str, Any]:
        """Lazy load tool registry from S3."""
        if self._tool_registry is None:
            self._tool_registry = self._load_tool_registry()
        return self._tool_registry

    def _load_tool_registry(self) -> Dict[str, Any]:
        """Load tool definitions from S3."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.tool_bucket,
                Prefix='tools/'
            )

            registry = {}
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('.json'):
                    tool_data = json.loads(
                        self.s3_client.get_object(
                            Bucket=self.tool_bucket,
                            Key=obj['Key']
                        )['Body'].read().decode('utf-8')
                    )
                    registry[tool_data['name']] = tool_data

            return registry
        except Exception as e:
            print(f"Error loading tool registry: {e}")
            return {}

    def run(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Run the agent with a query.

        Args:
            query: User query to process
            session_id: Optional session ID for conversation memory

        Returns:
            Agent response with results
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize context
        context = {
            "query": query,
            "session_id": session_id,
            "iteration": 0,
            "history": [],
            "memory": self._retrieve_memory(session_id)
        }

        # ReAct loop
        for iteration in range(self.max_iterations):
            context['iteration'] = iteration

            # Reason about next action
            reasoning = self._reason(context)
            context['history'].append({
                "step": iteration,
                "type": "reasoning",
                "content": reasoning
            })

            # Check if we should respond
            if reasoning.get('action', {}).get('type') == 'respond':
                response = self._generate_response(context)
                self._store_memory(session_id, context)
                return {
                    "status": "success",
                    "response": response,
                    "iterations": iteration + 1,
                    "session_id": session_id
                }

            # Execute tool if needed
            if reasoning.get('action', {}).get('type') == 'tool':
                tool_result = self._execute_tool(
                    reasoning['action']['tool'],
                    reasoning['action'].get('parameters', {})
                )
                context['history'].append({
                    "step": iteration,
                    "type": "tool_execution",
                    "tool": reasoning['action']['tool'],
                    "result": tool_result
                })
                context['memory']['tool_results'].append(tool_result)

        # Max iterations reached
        response = self._generate_response(context)
        self._store_memory(session_id, context)
        return {
            "status": "max_iterations",
            "response": response,
            "iterations": self.max_iterations,
            "session_id": session_id
        }

    def _reason(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Reason about the next action using LLM.

        Args:
            context: Current agent context

        Returns:
            Reasoning result with suggested action
        """
        prompt = self._build_reasoning_prompt(context)

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
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
            reasoning_text = result['content'][0]['text']

            # Parse reasoning to extract action
            return self._parse_reasoning(reasoning_text)

        except Exception as e:
            print(f"Error in reasoning: {e}")
            return {
                "thought": f"Error during reasoning: {str(e)}",
                "action": {"type": "respond"}
            }

    def _build_reasoning_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for LLM reasoning.

        Args:
            context: Current agent context

        Returns:
            Formatted prompt string
        """
        tools_desc = self._get_tools_description()

        prompt = f"""You are an autonomous AI agent using the ReAct pattern. Your goal is to help with the user's query.

Available Tools:
{tools_desc}

User Query: {context['query']}

Conversation History:
{self._format_history(context['memory'].get('conversation', []))}

Recent Steps:
{self._format_recent_steps(context['history'])}

Now, think step by step:
1. Thought: What should I do next?
2. Action: Choose a tool or respond to the user

Format your response as:
Thought: [your reasoning]
Action: {{"type": "tool", "tool": "tool_name", "parameters": {{...}}}}
OR
Action: {{"type": "respond"}}
"""
        return prompt

    def _get_tools_description(self) -> str:
        """Get formatted description of available tools."""
        descriptions = []
        for tool_name, tool_def in self.tool_registry.items():
            desc = f"- {tool_name}: {tool_def.get('description', 'No description')}"
            descriptions.append(desc)
        return "\n".join(descriptions) if descriptions else "No tools available"

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt."""
        if not history:
            return "No previous conversation"

        formatted = []
        for item in history[-5:]:  # Last 5 items
            formatted.append(f"{item.get('role', 'unknown')}: {item.get('content', '')}")
        return "\n".join(formatted)

    def _format_recent_steps(self, history: List[Dict[str, Any]]) -> str:
        """Format recent steps for prompt."""
        if not history:
            return "No previous steps"

        formatted = []
        for item in history[-3:]:  # Last 3 steps
            if item['type'] == 'reasoning':
                formatted.append(f"Thought: {item.get('content', {}).get('thought', '')}")
            elif item['type'] == 'tool_execution':
                formatted.append(f"Executed {item['tool']}: {str(item.get('result', ''))[:100]}")
        return "\n".join(formatted)

    def _parse_reasoning(self, reasoning_text: str) -> Dict[str, Any]:
        """Parse reasoning text to extract action.

        Args:
            reasoning_text: LLM response text

        Returns:
            Parsed reasoning with action
        """
        # Simple parsing - in production, use more robust parsing
        thought = ""
        action = {"type": "respond"}

        lines = reasoning_text.split('\n')
        for line in lines:
            if line.lower().startswith('thought:'):
                thought = line.split(':', 1)[1].strip()
            elif line.lower().startswith('action:'):
                try:
                    action_str = line.split(':', 1)[1].strip()
                    action = json.loads(action_str)
                except json.JSONDecodeError:
                    action = {"type": "respond"}

        return {
            "thought": thought,
            "action": action
        }

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        # In a real implementation, this would call the tool executor Lambda
        # For now, return a mock result
        return {
            "tool": tool_name,
            "parameters": parameters,
            "result": f"Executed {tool_name} with {parameters}",
            "timestamp": datetime.now().isoformat()
        }

    def _generate_response(self, context: Dict[str, Any]) -> str:
        """Generate final response to user.

        Args:
            context: Agent context

        Returns:
            Formatted response string
        """
        prompt = f"""Based on the following steps, provide a helpful response to the user's query.

User Query: {context['query']}

Steps Taken:
{self._format_recent_steps(context['history'])}

Provide a clear, concise response:"""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                })
            )

            result = json.loads(response['body'].read())
            return result['content'][0]['text']

        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

    def _retrieve_memory(self, session_id: str) -> Dict[str, Any]:
        """Retrieve memory for a session.

        Args:
            session_id: Session identifier

        Returns:
            Memory data
        """
        try:
            response = self.dynamodb_client.query(
                TableName=self.conversation_table,
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={
                    ':sid': session_id
                },
                Limit=10,
                ScanIndexForward=False
            )

            history = [
                decimal_to_float(item) for item in response.get('Items', [])
            ]

            return {
                "conversation": history,
                "tool_results": [],
                "learned_patterns": []
            }
        except Exception as e:
            print(f"Error retrieving memory: {e}")
            return {
                "conversation": [],
                "tool_results": [],
                "learned_patterns": []
            }

    def _store_memory(self, session_id: str, context: Dict[str, Any]) -> None:
        """Store conversation memory.

        Args:
            session_id: Session identifier
            context: Agent context to store
        """
        try:
            ttl = int((datetime.now() + timedelta(days=7)).timestamp())

            self.dynamodb_client.put_item(
                TableName=self.conversation_table,
                Item={
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'query': context['query'],
                    'response': context.get('response', ''),
                    'iterations': context['iteration'],
                    'ttl': ttl
                }
            )
        except Exception as e:
            print(f"Error storing memory: {e}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for agent core.

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        Response dictionary
    """
    operation = event.get('operation', 'run')

    if operation == 'run':
        agent = Agent()
        query = event.get('query', '')
        session_id = event.get('session_id')
        return agent.run(query, session_id)

    elif operation == 'store_memory':
        agent = Agent()
        session_id = event.get('session_id')
        agent._store_memory(session_id, event)
        return {"status": "success"}

    elif operation == 'finalize':
        return {
            "status": "completed",
            "result": event.get('action', {})
        }

    elif operation == 'handle_error':
        return {
            "status": "error",
            "error": event.get('error', {}),
            "message": "Agent encountered an error"
        }

    else:
        return {
            "status": "error",
            "message": f"Unknown operation: {operation}"
        }
