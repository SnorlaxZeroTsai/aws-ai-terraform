"""
Agent Orchestrator - Coordinates multi-agent interactions.
Implements hierarchical orchestration pattern.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import boto3
from botocore.exceptions import ClientError

from shared.config.settings import settings
from agents.chatbot.chatbot_agent import ChatbotAgent
from agents.rag.rag_agent import RAGAgent
from agents.autonomous.autonomous_agent import AutonomousAgent
from agents.document.document_agent import DocumentAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents using hierarchical pattern.

    Architecture:
        Orchestrator (Main)
            ├── Chatbot Agent
            ├── RAG Agent
            ├── Autonomous Agent
            └── Document Agent

    The orchestrator routes requests to appropriate agents and can
    coordinate multiple agents for complex tasks.
    """

    def __init__(self, settings: settings):
        """Initialize the orchestrator."""
        self.settings = settings
        self.agents: Dict[str, Any] = {}
        self.aws_clients: Dict[str, Any] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Initializing orchestrator with pattern: {settings.orchestration_pattern}")

    async def initialize(self):
        """Initialize all agents and AWS clients."""
        logger.info("Initializing agents...")

        # Initialize AWS clients
        self.aws_clients['lambda'] = boto3.client(
            'lambda',
            region_name=self.settings.aws_region
        )
        self.aws_clients['stepfunctions'] = boto3.client(
            'stepfunctions',
            region_name=self.settings.aws_region
        )

        # Initialize agents based on configuration
        if self.settings.enable_chatbot_agent:
            self.agents['chatbot'] = ChatbotAgent(
                lambda_client=self.aws_clients['lambda'],
                lambda_arn=self.settings.stage2_chatbot_lambda_arn
            )
            logger.info("Chatbot agent initialized")

        if self.settings.enable_rag_agent:
            self.agents['rag'] = RAGAgent(
                lambda_client=self.aws_clients['lambda'],
                lambda_arn=self.settings.stage4_search_lambda_arn,
                opensearch_endpoint=self.settings.stage4_opensearch_endpoint
            )
            logger.info("RAG agent initialized")

        if self.settings.enable_autonomous_agent:
            self.agents['autonomous'] = AutonomousAgent(
                lambda_client=self.aws_clients['lambda'],
                lambda_arn=self.settings.stage5_agent_core_lambda_arn,
                stepfunctions_client=self.aws_clients['stepfunctions'],
                state_machine_arn=self.settings.stage5_step_function_arn
            )
            logger.info("Autonomous agent initialized")

        if self.settings.enable_document_agent:
            self.agents['document'] = DocumentAgent(
                lambda_client=self.aws_clients['lambda'],
                s3_bucket=self.settings.stage3_s3_bucket_name
            )
            logger.info("Document agent initialized")

        logger.info(f"Initialized {len(self.agents)} agents")

    async def shutdown(self):
        """Cleanup resources."""
        logger.info("Shutting down orchestrator...")
        # Close AWS connections if needed
        self.agents.clear()
        self.aws_clients.clear()
        logger.info("Orchestrator shutdown complete")

    async def list_agents(self) -> List[Dict[str, str]]:
        """List available agents."""
        return [
            {
                "name": agent_name,
                "type": agent.__class__.__name__,
                "enabled": True
            }
            for agent_name, agent in self.agents.items()
        ]

    async def route_to_agent(
        self,
        agent_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to appropriate agent.

        Args:
            agent_type: Type of agent to route to
            request_data: Request data for the agent

        Returns:
            Agent response data

        Raises:
            ValueError: If agent type is not found or disabled
        """
        if agent_type not in self.agents:
            raise ValueError(f"Agent type '{agent_type}' not found or disabled")

        agent = self.agents[agent_type]

        try:
            logger.info(f"Routing to {agent_type} agent")
            response = await agent.execute(request_data)
            return response

        except Exception as e:
            logger.error(f"Error executing {agent_type} agent: {e}", exc_info=True)
            raise

    async def collaborate(
        self,
        agents: List[str],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents for a task.

        Implements hierarchical pattern where orchestrator:
        1. Delegates subtasks to specialist agents
        2. Aggregates results
        3. Synthesizes final response

        Args:
            agents: List of agent types to involve
            task: Task description
            context: Additional context

        Returns:
            Aggregated results from all agents
        """
        logger.info(f"Collaborating agents {agents} on task: {task[:100]}...")

        results = {}
        errors = {}

        # Execute agents in parallel
        tasks_to_execute = []
        for agent_type in agents:
            if agent_type in self.agents:
                tasks_to_execute.append(agent_type)
            else:
                errors[agent_type] = f"Agent {agent_type} not available"

        # Parallel execution
        agent_tasks = [
            self.route_to_agent(agent_type, {
                **context,
                'task': task,
                'agent_type': agent_type
            })
            for agent_type in tasks_to_execute
        ]

        # Wait for all agents to complete
        try:
            agent_results = await asyncio.gather(
                *agent_tasks,
                return_exceptions=True
            )

            for agent_type, result in zip(tasks_to_execute, agent_results):
                if isinstance(result, Exception):
                    errors[agent_type] = str(result)
                else:
                    results[agent_type] = result

        except Exception as e:
            logger.error(f"Error in agent collaboration: {e}", exc_info=True)

        # Synthesize results
        synthesis = self._synthesize_results(results, task)

        return {
            'task': task,
            'agents_involved': tasks_to_execute,
            'individual_results': results,
            'errors': errors,
            'synthesis': synthesis,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _synthesize_results(
        self,
        results: Dict[str, Any],
        task: str
    ) -> Dict[str, Any]:
        """
        Synthesize results from multiple agents.

        In hierarchical pattern, this creates a unified response
        from specialist agent outputs.

        Args:
            results: Individual agent results
            task: Original task

        Returns:
            Synthesized result
        """
        synthesis = {
            'summary': f"Completed task with {len(results)} agents",
            'agent_count': len(results),
            'key_findings': []
        }

        # Extract key findings from each agent
        for agent_type, result in results.items():
            if isinstance(result, dict):
                if 'answer' in result:
                    synthesis['key_findings'].append({
                        'agent': agent_type,
                        'finding': result['answer'][:200]
                    })
                elif 'response' in result:
                    synthesis['key_findings'].append({
                        'agent': agent_type,
                        'finding': result['response'][:200]
                    })

        return synthesis

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an asynchronous job.

        Args:
            job_id: Job identifier

        Returns:
            Job status data or None if not found
        """
        if job_id not in self.jobs:
            return None

        return self.jobs[job_id]

    def _create_job(self, agent_type: str, request_data: Dict[str, Any]) -> str:
        """
        Create a new job tracking entry.

        Args:
            agent_type: Type of agent executing the job
            request_data: Original request data

        Returns:
            Job ID
        """
        job_id = f"{agent_type}-{datetime.utcnow().timestamp()}"

        self.jobs[job_id] = {
            'job_id': job_id,
            'agent_type': agent_type,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'request_data': request_data,
            'result': None,
            'error': None
        }

        return job_id

    def _update_job(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update job status."""
        if job_id in self.jobs:
            self.jobs[job_id].update({
                'status': status,
                'updated_at': datetime.utcnow().isoformat(),
                'result': result,
                'error': error
            })
