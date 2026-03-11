"""Memory management system for the autonomous agent.

This module implements a multi-tier memory system:
- Short-term: Conversation memory (24h TTL)
- Episodic: Specific events and tool results (7d TTL)
- Semantic: Knowledge base and patterns (persistent)
"""

import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from utils import get_env_var, get_aws_client, decimal_to_float

class MemorySystem:
    """Multi-tier memory management system.

    The memory system provides:
    1. Conversation memory: Recent dialogues
    2. Episodic memory: Specific events and tool results
    3. Semantic memory: Learned patterns and knowledge
    """

    def __init__(
        self,
        dynamodb_client: Optional[Any] = None
    ):
        """Initialize the memory system.

        Args:
            dynamodb_client: Optional boto3 DynamoDB client
        """
        self.dynamodb_client = dynamodb_client or get_aws_client('dynamodb')

        self.conversation_table = get_env_var('CONVERSATION_TABLE')
        self.episodic_table = get_env_var('EPISODIC_TABLE')
        self.semantic_table = get_env_var('SEMANTIC_TABLE')

    def store_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store a conversation turn.

        Args:
            session_id: Session identifier
            role: Role (user/assistant/system)
            content: Message content
            metadata: Optional metadata
        """
        ttl = int((datetime.now() + timedelta(days=1)).timestamp())

        item = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'content': content,
            'ttl': ttl
        }

        if metadata:
            item['metadata'] = metadata

        try:
            self.dynamodb_client.put_item(
                TableName=self.conversation_table,
                Item=self._encode_item(item)
            )
        except Exception as e:
            print(f"Error storing conversation: {e}")

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of items to retrieve

        Returns:
            List of conversation items
        """
        try:
            response = self.dynamodb_client.query(
                TableName=self.conversation_table,
                KeyConditionExpression='session_id = :sid',
                ExpressionAttributeValues={
                    ':sid': {'S': session_id}
                },
                Limit=limit,
                ScanIndexForward=False
            )

            items = response.get('Items', [])
            return [decimal_to_float(item) for item in items]

        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    def store_episode(
        self,
        episode_id: str,
        session_id: str,
        episode_type: str,
        data: Dict[str, Any],
        ttl_days: int = 7
    ) -> None:
        """Store an episodic memory.

        Args:
            episode_id: Unique episode identifier
            session_id: Session identifier
            episode_type: Type of episode (tool_result, error, etc.)
            data: Episode data
            ttl_days: Time to live in days
        """
        ttl = int((datetime.now() + timedelta(days=ttl_days)).timestamp())

        item = {
            'episode_id': episode_id,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'type': episode_type,
            'data': data,
            'ttl': ttl
        }

        try:
            self.dynamodb_client.put_item(
                TableName=self.episodic_table,
                Item=self._encode_item(item)
            )
        except Exception as e:
            print(f"Error storing episode: {e}")

    def get_episodes(
        self,
        session_id: Optional[str] = None,
        episode_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve episodic memories.

        Args:
            session_id: Optional session filter
            episode_type: Optional type filter
            limit: Maximum items to retrieve

        Returns:
            List of episodes
        """
        try:
            if session_id:
                # Query by session ID
                response = self.dynamodb_client.query(
                    TableName=self.episodic_table,
                    IndexName='session-index',
                    KeyConditionExpression='session_id = :sid',
                    ExpressionAttributeValues={
                        ':sid': {'S': session_id}
                    },
                    Limit=limit,
                    ScanIndexForward=False
                )
            else:
                # Scan without filter
                response = self.dynamodb_client.scan(
                    TableName=self.episodic_table,
                    Limit=limit
                )

            items = response.get('Items', [])

            # Filter by type if specified
            if episode_type:
                items = [
                    item for item in items
                    if item.get('type', {}).get('S') == episode_type
                ]

            return [decimal_to_float(item) for item in items]

        except Exception as e:
            print(f"Error retrieving episodes: {e}")
            return []

    def store_semantic_memory(
        self,
        memory_id: str,
        concept: str,
        knowledge: Dict[str, Any],
        confidence: float = 1.0
    ) -> None:
        """Store a semantic memory (persistent).

        Args:
            memory_id: Unique memory identifier
            concept: Concept or category
            knowledge: Knowledge content
            confidence: Confidence score (0-1)
        """
        item = {
            'memory_id': memory_id,
            'concept': concept,
            'knowledge': knowledge,
            'confidence': confidence,
            'created_at': datetime.now().isoformat(),
            'access_count': 0
        }

        try:
            self.dynamodb_client.put_item(
                TableName=self.semantic_table,
                Item=self._encode_item(item)
            )
        except Exception as e:
            print(f"Error storing semantic memory: {e}")

    def get_semantic_memory(
        self,
        concept: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve semantic memories.

        Args:
            concept: Optional concept filter
            limit: Maximum items to retrieve

        Returns:
            List of semantic memories
        """
        try:
            if concept:
                # Query by concept
                response = self.dynamodb_client.query(
                    TableName=self.semantic_table,
                    IndexName='concept-index',
                    KeyConditionExpression='concept = :concept',
                    ExpressionAttributeValues={
                        ':concept': {'S': concept}
                    },
                    Limit=limit
                )
            else:
                # Scan
                response = self.dynamodb_client.scan(
                    TableName=self.semantic_table,
                    Limit=limit
                )

            items = response.get('Items', [])
            return [decimal_to_float(item) for item in items]

        except Exception as e:
            print(f"Error retrieving semantic memory: {e}")
            return []

    def search_memories(
        self,
        query: str,
        memory_types: List[str] = ['conversation', 'episodic', 'semantic'],
        limit: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all memory types.

        Args:
            query: Search query
            memory_types: Types to search
            limit: Results per type

        Returns:
            Dictionary of results by type
        """
        results = {}

        # Simple keyword search - in production, use more sophisticated search
        query_lower = query.lower()

        if 'conversation' in memory_types:
            conversations = self.get_conversation_history("", limit * 10)
            results['conversation'] = [
                c for c in conversations
                if query_lower in c.get('content', '').lower()
            ][:limit]

        if 'episodic' in memory_types:
            episodes = self.get_episodes(limit=limit * 10)
            results['episodic'] = [
                e for e in episodes
                if query_lower in str(e.get('data', '')).lower()
            ][:limit]

        if 'semantic' in memory_types:
            semantic = self.get_semantic_memory(limit=limit * 10)
            results['semantic'] = [
                s for s in semantic
                if query_lower in s.get('concept', '').lower() or
                   query_lower in str(s.get('knowledge', '')).lower()
            ][:limit]

        return results

    def cleanup_expired_memory(self) -> Dict[str, int]:
        """Clean up expired memory entries (TTL handles this automatically).

        This method is for manual cleanup if needed.

        Returns:
            Count of items checked
        """
        # DynamoDB TTL handles cleanup automatically
        # This is just a placeholder for any manual cleanup logic
        return {
            'conversation': 0,
            'episodic': 0,
            'semantic': 0
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage.

        Returns:
            Memory statistics
        """
        stats = {
            'conversation_count': 0,
            'episodic_count': 0,
            'semantic_count': 0
        }

        try:
            # Count items in each table (scan with Count)
            response = self.dynamodb_client.scan(
                TableName=self.conversation_table,
                Select='COUNT'
            )
            stats['conversation_count'] = response.get('Count', 0)

            response = self.dynamodb_client.scan(
                TableName=self.episodic_table,
                Select='COUNT'
            )
            stats['episodic_count'] = response.get('Count', 0)

            response = self.dynamodb_client.scan(
                TableName=self.semantic_table,
                Select='COUNT'
            )
            stats['semantic_count'] = response.get('Count', 0)

        except Exception as e:
            print(f"Error getting memory stats: {e}")

        return stats

    def _encode_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Encode item for DynamoDB.

        Args:
            item: Item to encode

        Returns:
            Encoded item
        """
        encoded = {}
        for key, value in item.items():
            if isinstance(value, str):
                encoded[key] = {'S': value}
            elif isinstance(value, (int, float)):
                encoded[key] = {'N': str(value)}
            elif isinstance(value, bool):
                encoded[key] = {'BOOL': value}
            elif isinstance(value, list):
                encoded[key] = {'L': [self._encode_value(v) for v in value]}
            elif isinstance(value, dict):
                encoded[key] = {'M': self._encode_item(value)}
            elif value is None:
                encoded[key] = {'NULL': True}
            else:
                encoded[key] = {'S': str(value)}
        return encoded

    def _encode_value(self, value: Any) -> Dict[str, Any]:
        """Encode a single value for DynamoDB.

        Args:
            value: Value to encode

        Returns:
            Encoded value
        """
        if isinstance(value, str):
            return {'S': value}
        elif isinstance(value, (int, float)):
            return {'N': str(value)}
        elif isinstance(value, bool):
            return {'BOOL': value}
        elif isinstance(value, dict):
            return {'M': self._encode_item(value)}
        else:
            return {'S': str(value)}
