"""
RAG Service
Orchestrates the complete RAG pipeline: query → embedding → retrieval → generation
"""

import logging
from typing import List, Dict, Any, Optional
import os

from .embedding_service import EmbeddingService
from .opensearch_service import OpenSearchService
from ..prompts.rag_templates import RAGPrompts, PromptBuilder
import boto3
import json

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation"""

    def __init__(self,
                 opensearch_endpoint: str = None,
                 embedding_model_id: str = None,
                 llm_model_id: str = None,
                 index_name: str = "rag-index"):
        """
        Initialize the RAG service

        Args:
            opensearch_endpoint: OpenSearch domain endpoint
            embedding_model_id: Bedrock embedding model ID
            llm_model_id: Bedrock LLM model ID
            index_name: OpenSearch index name
        """
        # Initialize services
        self.embedding_service = EmbeddingService(model_id=embedding_model_id)
        self.opensearch_service = OpenSearchService(endpoint=opensearch_endpoint, index_name=index_name)

        # Bedrock runtime for LLM
        self.llm_model_id = llm_model_id or os.getenv('BEDROCK_LLM_MODEL')
        self.bedrock_runtime = boto3.client('bedrock-runtime')

        # Prompt builder
        self.prompt_builder = PromptBuilder(template_type='qa')

        logger.info("Initialized RAG service")

    def initialize_index(self, vector_dimension: int = 1536) -> bool:
        """
        Initialize the OpenSearch index

        Args:
            vector_dimension: Dimension of embedding vectors

        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.opensearch_service.create_index(vector_dimension)
            if success:
                logger.info("Successfully initialized RAG index")
            else:
                logger.error("Failed to initialize RAG index")
            return success
        except Exception as e:
            logger.error(f"Error initializing index: {str(e)}")
            return False

    def index_document(self, doc_id: str, content: str,
                      metadata: Dict[str, Any] = None) -> bool:
        """
        Index a document for retrieval

        Args:
            doc_id: Unique document ID
            content: Document content
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.generate_embedding(content)

            # Index document
            success = self.opensearch_service.index_document(
                doc_id=doc_id,
                content=content,
                embedding=embedding,
                metadata=metadata or {}
            )

            if success:
                logger.info(f"Successfully indexed document: {doc_id}")
            else:
                logger.error(f"Failed to index document: {doc_id}")

            return success

        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return False

    def query(self, user_query: str, max_results: int = 5,
             search_type: str = 'vector',
             template_type: str = 'qa',
             conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform a RAG query

        Args:
            user_query: User's question
            max_results: Maximum number of chunks to retrieve
            search_type: Type of search ('vector', 'hybrid')
            template_type: Prompt template type
            conversation_history: Optional conversation history

        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Step 1: Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(user_query)
            logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")

            # Step 2: Retrieve relevant chunks
            if search_type == 'vector':
                chunks = self.opensearch_service.vector_search(
                    query_embedding=query_embedding,
                    size=max_results
                )
            elif search_type == 'hybrid':
                chunks = self.opensearch_service.hybrid_search(
                    query_text=user_query,
                    query_embedding=query_embedding,
                    size=max_results
                )
            else:
                raise ValueError(f"Unknown search type: {search_type}")

            logger.info(f"Retrieved {len(chunks)} chunks")

            # Step 3: Build prompt with retrieved context
            self.prompt_builder.set_template(template_type)
            prompt = self.prompt_builder.build(
                query=user_query,
                context_chunks=chunks,
                conversation_history=conversation_history
            )

            # Step 4: Generate answer using LLM
            answer = self._generate_answer(prompt)

            return {
                'answer': answer,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'query': user_query,
                'search_type': search_type
            }

        except Exception as e:
            logger.error(f"Error performing RAG query: {str(e)}")
            return {
                'answer': f"Error processing query: {str(e)}",
                'chunks': [],
                'chunk_count': 0,
                'query': user_query,
                'search_type': search_type
            }

    def _generate_answer(self, prompt: str) -> str:
        """
        Generate answer using Bedrock LLM

        Args:
            prompt: Formatted prompt

        Returns:
            Generated answer
        """
        try:
            # Prepare request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            # Invoke Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.llm_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            answer = response_body.get('content', [{}])[0].get('text', '')

            return answer.strip()

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "Error generating answer. Please try again."

    def query_without_generation(self, user_query: str, max_results: int = 5,
                                search_type: str = 'vector') -> List[Dict[str, Any]]:
        """
        Query without LLM generation (retrieval only)

        Args:
            user_query: User's question
            max_results: Maximum number of chunks to retrieve
            search_type: Type of search ('vector', 'hybrid')

        Returns:
            List of retrieved chunks
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(user_query)

            # Retrieve chunks
            if search_type == 'vector':
                chunks = self.opensearch_service.vector_search(
                    query_embedding=query_embedding,
                    size=max_results
                )
            elif search_type == 'hybrid':
                chunks = self.opensearch_service.hybrid_search(
                    query_text=user_query,
                    query_embedding=query_embedding,
                    size=max_results
                )
            else:
                raise ValueError(f"Unknown search type: {search_type}")

            logger.info(f"Retrieved {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error performing retrieval: {str(e)}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on RAG service

        Returns:
            Health status
        """
        health = {
            'opensearch': False,
            'bedrock': False,
            'index_exists': False
        }

        try:
            # Check OpenSearch connection
            health['index_exists'] = self.opensearch_service.index_exists()
            health['opensearch'] = True

            # Check Bedrock access
            test_embedding = self.embedding_service.generate_embedding("test")
            health['bedrock'] = len(test_embedding) > 0

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")

        return health


def create_rag_service(opensearch_endpoint: str = None,
                      embedding_model_id: str = None,
                      llm_model_id: str = None,
                      index_name: str = "rag-index") -> RAGService:
    """
    Factory function to create a RAG service

    Args:
        opensearch_endpoint: OpenSearch domain endpoint
        embedding_model_id: Bedrock embedding model ID
        llm_model_id: Bedrock LLM model ID
        index_name: OpenSearch index name

    Returns:
        RAGService instance
    """
    return RAGService(
        opensearch_endpoint=opensearch_endpoint,
        embedding_model_id=embedding_model_id,
        llm_model_id=llm_model_id,
        index_name=index_name
    )
