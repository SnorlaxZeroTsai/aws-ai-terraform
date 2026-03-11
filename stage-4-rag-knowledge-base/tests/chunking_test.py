"""
Tests for Chunking Strategies
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from chunking.strategies import FixedSizeChunking, SemanticChunking, HybridChunking, create_chunking_strategy
from chunking.evaluation import ChunkEvaluator


def test_fixed_size_chunking():
    """Test fixed-size chunking"""
    print("\n=== Testing Fixed-Size Chunking ===")

    text = "This is a sample document. It contains multiple sentences. " * 50

    chunker = FixedSizeChunking(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk(text)

    print(f"Created {len(chunks)} chunks")

    # Evaluate
    ChunkEvaluator.print_report(chunks)

    # Verify chunks
    assert len(chunks) > 0, "Should create at least one chunk"
    assert all('content' in c for c in chunks), "All chunks should have content"
    assert all('metadata' in c for c in chunks), "All chunks should have metadata"

    print("✓ Fixed-size chunking test passed")


def test_semantic_chunking():
    """Test semantic chunking"""
    print("\n=== Testing Semantic Chunking ===")

    text = """
    This is the first paragraph. It contains important information.

    This is the second paragraph. It continues the discussion.

    This is the third paragraph. It concludes the topic.
    """ * 10

    chunker = SemanticChunking(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk(text)

    print(f"Created {len(chunks)} chunks")

    # Evaluate
    ChunkEvaluator.print_report(chunks)

    # Verify chunks
    assert len(chunks) > 0, "Should create at least one chunk"
    assert all('content' in c for c in chunks), "All chunks should have content"

    print("✓ Semantic chunking test passed")


def test_hybrid_chunking():
    """Test hybrid chunking"""
    print("\n=== Testing Hybrid Chunking ===")

    text = """
    This is the first paragraph with important details.

    This is the second paragraph with more information.

    This is the third paragraph with concluding remarks.
    """ * 10

    chunker = HybridChunking(chunk_size=600, chunk_overlap=100)
    chunks = chunker.chunk(text)

    print(f"Created {len(chunks)} chunks")

    # Evaluate
    ChunkEvaluator.print_report(chunks)

    # Verify chunks
    assert len(chunks) > 0, "Should create at least one chunk"
    assert all('content' in c for c in chunks), "All chunks should have content"

    print("✓ Hybrid chunking test passed")


def test_chunking_factory():
    """Test chunking strategy factory"""
    print("\n=== Testing Chunking Factory ===")

    strategies = ['fixed', 'semantic', 'hybrid']

    for strategy_type in strategies:
        chunker = create_chunking_strategy(strategy_type, chunk_size=500, chunk_overlap=100)
        assert chunker is not None, f"Should create {strategy_type} strategy"
        print(f"✓ Created {strategy_type} strategy")

    print("✓ Chunking factory test passed")


def test_chunk_overlap():
    """Test chunk overlap calculation"""
    print("\n=== Testing Chunk Overlap ===")

    text = "This is a test document. " * 100

    chunker = FixedSizeChunking(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk(text)

    overlap = ChunkEvaluator.calculate_overlap(chunks)
    print(f"Average overlap ratio: {overlap:.2%}")

    assert overlap > 0, "Should have some overlap"

    print("✓ Chunk overlap test passed")


def test_chunk_distribution():
    """Test chunk size distribution"""
    print("\n=== Testing Chunk Distribution ===")

    text = "This is a test. " * 200

    chunker = HybridChunking(chunk_size=600, chunk_overlap=100)
    chunks = chunker.chunk(text)

    distribution = ChunkEvaluator.analyze_distribution(chunks)

    print("Size distribution:")
    for label, count in distribution['distribution'].items():
        print(f"  {label}: {count}")

    print("\nPercentiles:")
    for percentile, value in distribution['percentiles'].items():
        print(f"  {percentile}: {value:.2f}")

    assert 'distribution' in distribution, "Should have distribution data"
    assert 'percentiles' in distribution, "Should have percentile data"

    print("✓ Chunk distribution test passed")


def run_all_tests():
    """Run all chunking tests"""
    print("\n" + "=" * 50)
    print("Running Chunking Tests")
    print("=" * 50)

    try:
        test_fixed_size_chunking()
        test_semantic_chunking()
        test_hybrid_chunking()
        test_chunking_factory()
        test_chunk_overlap()
        test_chunk_distribution()

        print("\n" + "=" * 50)
        print("✓ All chunking tests passed!")
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
