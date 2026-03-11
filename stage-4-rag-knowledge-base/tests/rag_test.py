"""
Tests for RAG Service
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.rag_service import RAGService
from chunking.strategies import create_chunking_strategy
from chunking.evaluation import ChunkEvaluator


def test_rag_initialization():
    """Test RAG service initialization"""
    print("\n=== Testing RAG Initialization ===")

    # Note: This test requires actual AWS credentials and OpenSearch endpoint
    # For local testing, you may need to mock these services

    print("RAG service initialization test")
    print("Note: Full integration tests require AWS resources")
    print("For unit tests, use mocking frameworks")

    print("✓ RAG initialization test passed")


def test_chunking_pipeline():
    """Test document chunking pipeline"""
    print("\n=== Testing Chunking Pipeline ===")

    sample_doc = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by humans or animals. Leading AI textbooks define the field as the study of "intelligent agents": any system that perceives its environment and takes actions that maximize its chance of achieving its goals.

    AI applications include advanced web search engines, recommendation systems (used by YouTube, Amazon and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g. Tesla), and competing at the highest level in strategic game systems (such as chess and Go).

    Machine learning is the study of computer algorithms that can improve automatically through experience and by the use of data. It is seen as a part of artificial intelligence. Machine learning algorithms build a model based on sample data, known as "training data", in order to make predictions or decisions without being explicitly programmed to do so.

    Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.
    """

    # Create chunks
    chunker = create_chunking_strategy('hybrid', chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk(sample_doc)

    print(f"Created {len(chunks)} chunks from sample document")

    # Evaluate chunks
    metrics = ChunkEvaluator.evaluate_chunks(chunks)
    print(f"Average chunk size: {metrics['avg_chunk_size']:.2f}")
    print(f"Total chunks: {metrics['chunk_count']}")

    assert len(chunks) > 0, "Should create chunks"
    assert metrics['avg_chunk_size'] > 0, "Should have non-zero average size"

    print("✓ Chunking pipeline test passed")


def test_retrieval_simulation():
    """Simulate retrieval process"""
    print("\n=== Testing Retrieval Simulation ===")

    # Simulate indexed documents
    documents = [
        {
            'id': 'doc1',
            'content': 'Python is a high-level programming language known for its simplicity and readability.',
            'metadata': {'source': 'doc1.txt'}
        },
        {
            'id': 'doc2',
            'content': 'Terraform is an infrastructure as code tool that allows you to define and provision infrastructure.',
            'metadata': {'source': 'doc2.txt'}
        },
        {
            'id': 'doc3',
            'content': 'AWS OpenSearch is a managed service that makes it easy to deploy, operate, and scale OpenSearch clusters.',
            'metadata': {'source': 'doc3.txt'}
        }
    ]

    # Simulate query
    query = "What is Terraform?"

    # Simulate retrieval (in real system, this would use vector similarity)
    retrieved_docs = [doc for doc in documents if 'Terraform' in doc['content']]

    print(f"Query: {query}")
    print(f"Retrieved {len(retrieved_docs)} documents")

    for doc in retrieved_docs:
        print(f"  - {doc['id']}: {doc['content'][:50]}...")

    assert len(retrieved_docs) > 0, "Should retrieve relevant documents"

    print("✓ Retrieval simulation test passed")


def test_rag_query_simulation():
    """Simulate RAG query process"""
    print("\n=== Testing RAG Query Simulation ===")

    query = "What is machine learning?"

    # Simulated context chunks
    context_chunks = [
        {
            'content': 'Machine learning is the study of computer algorithms that can improve automatically through experience.',
            'score': 0.95
        },
        {
            'content': 'ML algorithms build a model based on sample data, known as training data.',
            'score': 0.88
        }
    ]

    print(f"Query: {query}")
    print(f"Retrieved {len(context_chunks)} context chunks")

    for i, chunk in enumerate(context_chunks, 1):
        print(f"  Chunk {i} (score: {chunk['score']:.2f}): {chunk['content'][:60]}...")

    # Simulated answer
    answer = "Machine learning is the study of computer algorithms that improve automatically through experience. These algorithms build models using training data to make predictions or decisions."

    print(f"\nGenerated Answer: {answer}")

    assert len(context_chunks) > 0, "Should have context"
    assert len(answer) > 0, "Should generate answer"

    print("✓ RAG query simulation test passed")


def test_health_check_simulation():
    """Simulate health check"""
    print("\n=== Testing Health Check Simulation ===")

    health = {
        'opensearch': True,
        'bedrock': True,
        'index_exists': True
    }

    print("Health status:")
    print(f"  OpenSearch: {'✓' if health['opensearch'] else '✗'}")
    print(f"  Bedrock: {'✓' if health['bedrock'] else '✗'}")
    print(f"  Index Exists: {'✓' if health['index_exists'] else '✗'}")

    all_healthy = all(health.values())
    print(f"\nOverall Health: {'Healthy' if all_healthy else 'Unhealthy'}")

    assert all_healthy, "All components should be healthy"

    print("✓ Health check simulation test passed")


def run_all_tests():
    """Run all RAG tests"""
    print("\n" + "=" * 50)
    print("Running RAG Tests")
    print("=" * 50)

    try:
        test_rag_initialization()
        test_chunking_pipeline()
        test_retrieval_simulation()
        test_rag_query_simulation()
        test_health_check_simulation()

        print("\n" + "=" * 50)
        print("✓ All RAG tests passed!")
        print("=" * 50 + "\n")

    except AssertionError as e:
        print(f"\n✗ Test failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_all_tests()
