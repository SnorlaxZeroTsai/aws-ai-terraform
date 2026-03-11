"""
OpenSearch Service for Vector Operations
Handles OpenSearch vector index creation, document indexing, and similarity search
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class OpenSearchService:
    """Service for interacting with OpenSearch Vector Engine"""

    def __init__(self, endpoint: str = None, index_name: str = "rag-index"):
        """
        Initialize the OpenSearch service

        Args:
            endpoint: OpenSearch domain endpoint
            index_name: Name of the index
        """
        self.endpoint = endpoint or os.getenv('OPENSEARCH_DOMAIN_ENDPOINT')
        self.index_name = index_name

        # Construct the full URL
        if not self.endpoint.startswith('https://'):
            self.endpoint = f"https://{self.endpoint}"

        self.index_url = f"{self.endpoint}/{self.index_name}"

        logger.info(f"Initialized OpenSearchService for endpoint: {self.endpoint}")

    def create_index(self, vector_dimension: int = 1536) -> bool:
        """
        Create a vector index with k-NN configuration

        Args:
            vector_dimension: Dimension of the embedding vectors

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if index already exists
            if self.index_exists():
                logger.info(f"Index {self.index_name} already exists")
                return True

            # Define index settings with k-NN
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                },
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": vector_dimension,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 256,
                                    "m": 24
                                }
                            }
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "keyword"},
                                "chunk_id": {"type": "keyword"},
                                "doc_id": {"type": "keyword"},
                                "timestamp": {"type": "date"}
                            }
                        }
                    }
                }
            }

            # Create index
            response = requests.put(
                self.index_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(index_body),
                verify=False  # Only for development
            )

            if response.status_code in [200, 201]:
                logger.info(f"Successfully created index: {self.index_name}")
                return True
            else:
                logger.error(f"Failed to create index: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False

    def index_exists(self) -> bool:
        """
        Check if the index exists

        Returns:
            True if index exists, False otherwise
        """
        try:
            response = requests.head(self.index_url, verify=False)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking index existence: {str(e)}")
            return False

    def index_document(self, doc_id: str, content: str, embedding: List[float],
                      metadata: Dict[str, Any] = None) -> bool:
        """
        Index a document with its embedding

        Args:
            doc_id: Unique document ID
            content: Document content
            embedding: Embedding vector
            metadata: Optional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            doc_body = {
                "content": content,
                "embedding": embedding,
                "metadata": metadata or {}
            }

            url = f"{self.index_url}/_doc/{doc_id}"
            response = requests.put(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(doc_body),
                verify=False
            )

            if response.status_code in [200, 201]:
                logger.debug(f"Successfully indexed document: {doc_id}")
                return True
            else:
                logger.error(f"Failed to index document {doc_id}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            return False

    def index_documents_batch(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Index multiple documents in bulk

        Args:
            documents: List of documents with id, content, embedding, and metadata

        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0

        for doc in documents:
            doc_id = doc.get('id')
            content = doc.get('content')
            embedding = doc.get('embedding')
            metadata = doc.get('metadata', {})

            if self.index_document(doc_id, content, embedding, metadata):
                success_count += 1
            else:
                failure_count += 1

        logger.info(f"Bulk indexing complete: {success_count} succeeded, {failure_count} failed")
        return {"success": success_count, "failed": failure_count}

    def vector_search(self, query_embedding: List[float], size: int = 5,
                     min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using k-NN

        Args:
            query_embedding: Query embedding vector
            size: Number of results to return
            min_score: Minimum similarity score

        Returns:
            List of search results with scores
        """
        try:
            search_body = {
                "size": size,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_embedding,
                            "k": size
                        }
                    }
                },
                "min_score": min_score
            }

            url = f"{self.index_url}/_search"
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(search_body),
                verify=False
            )

            if response.status_code == 200:
                results = response.json()
                hits = results.get('hits', {}).get('hits', [])

                formatted_results = []
                for hit in hits:
                    formatted_results.append({
                        'id': hit.get('_id'),
                        'score': hit.get('_score'),
                        'content': hit.get('_source', {}).get('content'),
                        'metadata': hit.get('_source', {}).get('metadata', {})
                    })

                logger.info(f"Vector search returned {len(formatted_results)} results")
                return formatted_results
            else:
                logger.error(f"Vector search failed: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error performing vector search: {str(e)}")
            return []

    def hybrid_search(self, query_text: str, query_embedding: List[float],
                     size: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining keyword and vector search

        Args:
            query_text: Query text for keyword search
            query_embedding: Query embedding for vector search
            size: Number of results to return

        Returns:
            List of search results with combined scores
        """
        try:
            search_body = {
                "size": size,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": {
                                        "query": query_text,
                                        "boost": 1.0
                                    }
                                }
                            },
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding,
                                        "k": size
                                    },
                                    "boost": 2.0
                                }
                            }
                        ]
                    }
                }
            }

            url = f"{self.index_url}/_search"
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(search_body),
                verify=False
            )

            if response.status_code == 200:
                results = response.json()
                hits = results.get('hits', {}).get('hits', [])

                formatted_results = []
                for hit in hits:
                    formatted_results.append({
                        'id': hit.get('_id'),
                        'score': hit.get('_score'),
                        'content': hit.get('_source', {}).get('content'),
                        'metadata': hit.get('_source', {}).get('metadata', {})
                    })

                logger.info(f"Hybrid search returned {len(formatted_results)} results")
                return formatted_results
            else:
                logger.error(f"Hybrid search failed: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error performing hybrid search: {str(e)}")
            return []

    def delete_index(self) -> bool:
        """
        Delete the index

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.index_exists():
                logger.info(f"Index {self.index_name} does not exist")
                return True

            response = requests.delete(self.index_url, verify=False)

            if response.status_code in [200, 404]:
                logger.info(f"Successfully deleted index: {self.index_name}")
                return True
            else:
                logger.error(f"Failed to delete index: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error deleting index: {str(e)}")
            return False


def create_opensearch_service(endpoint: str = None, index_name: str = "rag-index") -> OpenSearchService:
    """
    Factory function to create an OpenSearch service instance

    Args:
        endpoint: OpenSearch domain endpoint
        index_name: Name of the index

    Returns:
        OpenSearchService instance
    """
    return OpenSearchService(endpoint, index_name)
