"""
Chunking Evaluation Metrics
Provides metrics for evaluating chunk quality
"""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class ChunkEvaluator:
    """Evaluates chunk quality and distribution"""

    @staticmethod
    def evaluate_chunks(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate chunk quality across multiple metrics

        Args:
            chunks: List of chunks

        Returns:
            Dictionary with evaluation metrics
        """
        if not chunks:
            return {
                'chunk_count': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'std_chunk_size': 0
            }

        chunk_sizes = [len(chunk.get('content', '')) for chunk in chunks]

        metrics = {
            'chunk_count': len(chunks),
            'avg_chunk_size': np.mean(chunk_sizes),
            'median_chunk_size': np.median(chunk_sizes),
            'min_chunk_size': np.min(chunk_sizes),
            'max_chunk_size': np.max(chunk_sizes),
            'std_chunk_size': np.std(chunk_sizes),
            'total_characters': sum(chunk_sizes)
        }

        return metrics

    @staticmethod
    def calculate_overlap(chunks: List[Dict[str, Any]]) -> float:
        """
        Calculate average overlap between consecutive chunks

        Args:
            chunks: List of chunks

        Returns:
            Average overlap ratio
        """
        if len(chunks) < 2:
            return 0.0

        overlaps = []
        for i in range(len(chunks) - 1):
            current_content = chunks[i].get('content', '')
            next_content = chunks[i + 1].get('content', '')

            # Calculate overlap
            overlap = ChunkEvaluator._string_overlap(current_content, next_content)
            overlap_ratio = overlap / len(current_content) if current_content else 0
            overlaps.append(overlap_ratio)

        return np.mean(overlaps) if overlaps else 0.0

    @staticmethod
    def _string_overlap(str1: str, str2: str) -> int:
        """
        Calculate character overlap between two strings

        Args:
            str1: First string
            str2: Second string

        Returns:
            Number of overlapping characters
        """
        # Simple overlap detection
        max_overlap = 0

        for i in range(1, min(len(str1), len(str2))):
            if str1[-i:] == str2[:i]:
                max_overlap = i

        return max_overlap

    @staticmethod
    def analyze_distribution(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze chunk size distribution

        Args:
            chunks: List of chunks

        Returns:
            Distribution analysis
        """
        chunk_sizes = [len(chunk.get('content', '')) for chunk in chunks]

        # Create histogram bins
        bins = [0, 500, 1000, 1500, 2000, float('inf')]
        labels = ['0-500', '500-1000', '1000-1500', '1500-2000', '2000+']

        distribution = {}
        for i in range(len(bins) - 1):
            count = sum(1 for size in chunk_sizes if bins[i] <= size < bins[i + 1])
            distribution[labels[i]] = count

        return {
            'distribution': distribution,
            'percentiles': {
                '25th': np.percentile(chunk_sizes, 25),
                '50th': np.percentile(chunk_sizes, 50),
                '75th': np.percentile(chunk_sizes, 75),
                '90th': np.percentile(chunk_sizes, 90),
            }
        }

    @staticmethod
    def print_report(chunks: List[Dict[str, Any]]) -> None:
        """
        Print a formatted evaluation report

        Args:
            chunks: List of chunks
        """
        metrics = ChunkEvaluator.evaluate_chunks(chunks)
        overlap = ChunkEvaluator.calculate_overlap(chunks)
        distribution = ChunkEvaluator.analyze_distribution(chunks)

        print("\n=== Chunking Evaluation Report ===")
        print(f"Total Chunks: {metrics['chunk_count']}")
        print(f"Total Characters: {metrics['total_characters']}")

        print("\nChunk Size Statistics:")
        print(f"  Average: {metrics['avg_chunk_size']:.2f}")
        print(f"  Median: {metrics['median_chunk_size']:.2f}")
        print(f"  Min: {metrics['min_chunk_size']}")
        print(f"  Max: {metrics['max_chunk_size']}")
        print(f"  Std Dev: {metrics['std_chunk_size']:.2f}")

        print("\nOverlap Analysis:")
        print(f"  Average Overlap Ratio: {overlap:.2%}")

        print("\nSize Distribution:")
        for label, count in distribution['distribution'].items():
            percentage = (count / metrics['chunk_count'] * 100) if metrics['chunk_count'] > 0 else 0
            print(f"  {label}: {count} ({percentage:.1f}%)")

        print("\nPercentiles:")
        for percentile, value in distribution['percentiles'].items():
            print(f"  {percentile}: {value:.2f}")

        print("=" * 35 + "\n")
