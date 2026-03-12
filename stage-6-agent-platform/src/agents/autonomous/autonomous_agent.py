"""
Autonomous Agent - Wraps Stage 5 Step Functions and Lambda.
"""
import logging
from typing import Dict, Any
import json
import boto3
from datetime import datetime

logger = logging.getLogger(__name__)


class AutonomousAgent:
    """Agent for autonomous task execution using ReAct pattern."""

    def __init__(
        self,
        lambda_client: boto3.client,
        lambda_arn: str = None,
        stepfunctions_client: boto3.client = None,
        state_machine_arn: str = None
    ):
        """Initialize autonomous agent."""
        self.lambda_client = lambda_client
        self.lambda_arn = lambda_arn
        self.sf_client = stepfunctions_client
        self.state_machine_arn = state_machine_arn
        logger.info(f"Autonomous agent initialized with Step Function: {state_machine_arn}")

    async def execute(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute autonomous agent task.

        Args:
            request_data: Task description and parameters

        Returns:
            Execution result or job_id for async execution
        """
        try:
            task = request_data.get('task')
            context = request_data.get('context', {})
            tools = request_data.get('tools')
            max_iterations = request_data.get('max_iterations', 10)

            if not task:
                raise ValueError("Task is required")

            # Start Step Function execution
            execution_input = {
                'task': task,
                'context': context,
                'max_iterations': max_iterations
            }

            if tools:
                execution_input['tools'] = tools

            response = self.sf_client.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=f"agent-{datetime.utcnow().timestamp()}",
                input=json.dumps(execution_input)
            )

            execution_arn = response['executionArn']
            job_id = execution_arn.split(':')[-1]

            return {
                'job_id': job_id,
                'execution_arn': execution_arn,
                'status': 'running',
                'task': task,
                'message': 'Agent execution started'
            }

        except Exception as e:
            logger.error(f"Autonomous agent error: {e}", exc_info=True)
            raise
