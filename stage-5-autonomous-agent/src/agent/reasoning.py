"""Reasoning engine for agent decision-making.

This module implements sophisticated reasoning capabilities:
- Multi-step reasoning chains
- Tool selection based on context
- Error recovery strategies
- Confidence estimation
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from utils import get_env_var, get_aws_client

class ReasoningEngine:
    """Advanced reasoning engine for agent decision-making.

    The reasoning engine uses LLMs to:
    1. Analyze the current context
    2. Evaluate available tools
    3. Plan multi-step strategies
    4. Handle failures gracefully
    """

    def __init__(
        self,
        bedrock_client: Optional[Any] = None,
        model_id: Optional[str] = None
    ):
        """Initialize the reasoning engine.

        Args:
            bedrock_client: Optional boto3 Bedrock client
            model_id: Optional model ID override
        """
        self.bedrock_client = bedrock_client or get_aws_client('bedrock-runtime')
        self.model_id = model_id or get_env_var('BEDROCK_MODEL_ID')

    def reason(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Perform multi-step reasoning.

        Args:
            query: User query
            context: Current context
            available_tools: List of available tools
            max_depth: Maximum reasoning depth

        Returns:
            Reasoning result with action plan
        """
        reasoning_chain = self._build_reasoning_chain(
            query,
            context,
            available_tools,
            max_depth
        )

        return {
            "reasoning_chain": reasoning_chain,
            "action": reasoning_chain[-1].get('action', {'type': 'respond'}),
            "confidence": self._calculate_confidence(reasoning_chain),
            "alternatives": self._generate_alternatives(reasoning_chain, available_tools)
        }

    def _build_reasoning_chain(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """Build a chain of reasoning steps.

        Args:
            query: User query
            context: Current context
            available_tools: Available tools
            max_depth: Maximum depth

        Returns:
            List of reasoning steps
        """
        chain = []
        current_context = context.copy()

        for depth in range(max_depth):
            step = self._reasoning_step(query, current_context, available_tools)
            chain.append(step)

            # If we decided to respond, stop reasoning
            if step.get('action', {}).get('type') == 'respond':
                break

            # Update context with expected tool outcome
            current_context = self._simulate_outcome(current_context, step)

        return chain

    def _reasoning_step(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform a single reasoning step.

        Args:
            query: User query
            context: Current context
            available_tools: Available tools

        Returns:
            Reasoning step with thought and action
        """
        prompt = self._build_reasoning_prompt(query, context, available_tools)

        try:
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                })
            )

            result = json.loads(response['body'].read())
            response_text = result['content'][0]['text']

            return self._parse_reasoning_response(response_text)

        except Exception as e:
            return {
                "thought": f"Error in reasoning: {str(e)}",
                "action": {"type": "respond"},
                "confidence": 0.0
            }

    def _build_reasoning_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for reasoning.

        Args:
            query: User query
            context: Current context
            available_tools: Available tools

        Returns:
            Formatted prompt
        """
        tools_desc = self._format_tools(available_tools)
        history = self._format_history(context.get('history', []))

        prompt = f"""You are an advanced reasoning AI. Analyze the situation and decide the best action.

User Query: {query}

Context:
{self._format_context(context)}

Available Tools:
{tools_desc}

Recent History:
{history}

Think step by step:
1. Analyze what information we have
2. Identify what we still need
3. Determine the best next action
4. Consider potential risks

Respond in this format:
Thought: [detailed analysis]
Action: {{"type": "tool", "tool": "tool_name", "parameters": {{...}}}}
OR
Action: {{"type": "respond"}}
Confidence: [0.0-1.0]
"""
        return prompt

    def _format_tools(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools for prompt.

        Args:
            tools: List of tool definitions

        Returns:
            Formatted string
        """
        formatted = []
        for tool in tools:
            name = tool.get('name', 'unknown')
            desc = tool.get('description', 'No description')
            formatted.append(f"- {name}: {desc}")
        return "\n".join(formatted)

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """Format history for prompt.

        Args:
            history: History list

        Returns:
            Formatted string
        """
        if not history:
            return "No previous actions"

        formatted = []
        for item in history[-5:]:
            if item.get('type') == 'reasoning':
                formatted.append(f"Thought: {item.get('content', {}).get('thought', '')}")
            elif item.get('type') == 'tool_execution':
                result = str(item.get('result', ''))[:100]
                formatted.append(f"Tool {item.get('tool', 'unknown')}: {result}")
        return "\n".join(formatted)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted string
        """
        parts = []
        if 'query' in context:
            parts.append(f"Query: {context['query']}")
        if 'iteration' in context:
            parts.append(f"Iteration: {context['iteration']}")
        if 'memory' in context:
            memory = context['memory']
            if memory.get('conversation'):
                parts.append(f"Previous messages: {len(memory['conversation'])}")
            if memory.get('tool_results'):
                parts.append(f"Tool calls: {len(memory['tool_results'])}")
        return "\n".join(parts)

    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM reasoning response.

        Args:
            response: LLM response text

        Returns:
            Parsed reasoning
        """
        thought = ""
        action = {"type": "respond"}
        confidence = 0.5

        # Extract thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=\n(?:Action|Confidence)|$)', response, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Extract action
        action_match = re.search(r'Action:\s*(\{.+?\})', response, re.DOTALL)
        if action_match:
            try:
                action = json.loads(action_match.group(1))
            except json.JSONDecodeError:
                pass

        # Extract confidence
        confidence_match = re.search(r'Confidence:\s*([0-9.]+)', response)
        if confidence_match:
            confidence = float(confidence_match.group(1))

        return {
            "thought": thought,
            "action": action,
            "confidence": confidence
        }

    def _simulate_outcome(
        self,
        context: Dict[str, Any],
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate the outcome of an action.

        Args:
            context: Current context
            step: Reasoning step

        Returns:
            Updated context
        """
        new_context = context.copy()

        if 'history' not in new_context:
            new_context['history'] = []

        new_context['history'].append({
            "type": "reasoning",
            "content": step
        })

        if step.get('action', {}).get('type') == 'tool':
            # Simulate tool execution
            new_context['history'].append({
                "type": "tool_execution",
                "tool": step['action']['tool'],
                "result": {"simulated": True}
            })

        return new_context

    def _calculate_confidence(self, chain: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence from reasoning chain.

        Args:
            chain: Reasoning chain

        Returns:
            Confidence score
        """
        if not chain:
            return 0.0

        confidences = [step.get('confidence', 0.5) for step in chain]
        return sum(confidences) / len(confidences)

    def _generate_alternatives(
        self,
        chain: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate alternative actions.

        Args:
            chain: Reasoning chain
            available_tools: Available tools

        Returns:
            List of alternative actions
        """
        alternatives = []

        # Suggest using different tools
        for tool in available_tools:
            if tool.get('name') != chain[-1].get('action', {}).get('tool'):
                alternatives.append({
                    "action": {
                        "type": "tool",
                        "tool": tool['name'],
                        "parameters": {}
                    },
                    "reason": f"Alternative: Use {tool['name']}"
                })

        return alternatives[:3]  # Return top 3 alternatives


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for reasoning engine.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Reasoning result
    """
    engine = ReasoningEngine()

    query = event.get('query', '')
    context_data = event.get('context', {})
    available_tools = event.get('available_tools', [])

    result = engine.reason(query, context_data, available_tools)

    return {
        "statusCode": 200,
        "body": result
    }
