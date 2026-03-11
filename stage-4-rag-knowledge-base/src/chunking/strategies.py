"""
Chunking Strategies for Document Processing
Implements various document chunking strategies for RAG systems
"""

import re
import logging
from typing import List, Dict, Any
import os

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Base class for chunking strategies"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize chunking strategy

        Args:
            chunk_size: Target size for each chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks

        Args:
            text: Input text

        Returns:
            List of chunks with metadata
        """
        raise NotImplementedError("Subclasses must implement chunk method")


class FixedSizeChunking(ChunkingStrategy):
    """Fixed-size chunking strategy"""

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into fixed-size chunks

        Args:
            text: Input text

        Returns:
            List of chunks with metadata
        """
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append({
                'id': f'chunk_{chunk_id}',
                'content': chunk_text,
                'metadata': {
                    'start_pos': start,
                    'end_pos': end,
                    'chunk_size': len(chunk_text),
                    'strategy': 'fixed_size'
                }
            })

            start = end - self.chunk_overlap
            chunk_id += 1

        logger.info(f"Created {len(chunks)} fixed-size chunks")
        return chunks


class SemanticChunking(ChunkingStrategy):
    """Semantic chunking based on sentence boundaries"""

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into semantic chunks based on sentences

        Args:
            text: Input text

        Returns:
            List of chunks with metadata
        """
        # Split into sentences
        sentences = self._split_sentences(text)

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If sentence is too long, split it
            if sentence_length > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_id))
                    chunk_id += 1
                    current_chunk = []
                    current_size = 0

                # Split long sentence
                sub_chunks = self._split_long_sentence(sentence)
                for sub_chunk in sub_chunks:
                    chunks.append(self._create_chunk([sub_chunk], chunk_id))
                    chunk_id += 1
                continue

            # Check if adding sentence would exceed chunk size
            if current_size + sentence_length > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(current_chunk, chunk_id))
                chunk_id += 1
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_length

        # Add remaining sentences
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_id))

        logger.info(f"Created {len(chunks)} semantic chunks")
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting based on punctuation
        # In production, use NLP libraries like spaCy
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        Split a long sentence into smaller parts

        Args:
            sentence: Long sentence

        Returns:
            List of sentence parts
        """
        parts = []
        start = 0

        while start < len(sentence):
            end = start + self.chunk_size
            part = sentence[start:end]
            parts.append(part)
            start = end - self.chunk_overlap

        return parts

    def _create_chunk(self, sentences: List[str], chunk_id: int) -> Dict[str, Any]:
        """
        Create a chunk from sentences

        Args:
            sentences: List of sentences
            chunk_id: Chunk ID

        Returns:
            Chunk dictionary
        """
        content = ' '.join(sentences)
        return {
            'id': f'chunk_{chunk_id}',
            'content': content,
            'metadata': {
                'sentence_count': len(sentences),
                'chunk_size': len(content),
                'strategy': 'semantic'
            }
        }


class HybridChunking(ChunkingStrategy):
    """Hybrid chunking combining fixed-size and semantic approaches"""

    def chunk(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text using hybrid approach

        Args:
            text: Input text

        Returns:
            List of chunks with metadata
        """
        # First, split into paragraphs
        paragraphs = self._split_paragraphs(text)

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0

        for paragraph in paragraphs:
            para_length = len(paragraph)

            # If paragraph is too long, use fixed-size chunking
            if para_length > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_id))
                    chunk_id += 1
                    current_chunk = []
                    current_size = 0

                # Split long paragraph
                sub_chunks = self._split_long_paragraph(paragraph)
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
                continue

            # Check if adding paragraph would exceed chunk size
            if current_size + para_length > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(current_chunk, chunk_id))
                chunk_id += 1
                current_chunk = []
                current_size = 0

            current_chunk.append(paragraph)
            current_size += para_length

        # Add remaining paragraphs
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_id))

        logger.info(f"Created {len(chunks)} hybrid chunks")
        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs

        Args:
            text: Input text

        Returns:
            List of paragraphs
        """
        paragraphs = re.split(r'\n\n+', text.strip())

        # Filter out empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _split_long_paragraph(self, paragraph: str) -> List[Dict[str, Any]]:
        """
        Split a long paragraph using fixed-size strategy

        Args:
            paragraph: Long paragraph

        Returns:
            List of chunks
        """
        fixed_strategy = FixedSizeChunking(self.chunk_size, self.chunk_overlap)
        return fixed_strategy.chunk(paragraph)

    def _create_chunk(self, paragraphs: List[str], chunk_id: int) -> Dict[str, Any]:
        """
        Create a chunk from paragraphs

        Args:
            paragraphs: List of paragraphs
            chunk_id: Chunk ID

        Returns:
            Chunk dictionary
        """
        content = '\n\n'.join(paragraphs)
        return {
            'id': f'chunk_{chunk_id}',
            'content': content,
            'metadata': {
                'paragraph_count': len(paragraphs),
                'chunk_size': len(content),
                'strategy': 'hybrid'
            }
        }


def create_chunking_strategy(strategy_type: str = 'hybrid',
                             chunk_size: int = None,
                             chunk_overlap: int = None) -> ChunkingStrategy:
    """
    Factory function to create a chunking strategy

    Args:
        strategy_type: Type of strategy ('fixed', 'semantic', 'hybrid')
        chunk_size: Target chunk size
        chunk_overlap: Chunk overlap

    Returns:
        ChunkingStrategy instance
    """
    chunk_size = chunk_size or int(os.getenv('CHUNK_SIZE', 1000))
    chunk_overlap = chunk_overlap or int(os.getenv('CHUNK_OVERLAP', 200))

    if strategy_type == 'fixed':
        return FixedSizeChunking(chunk_size, chunk_overlap)
    elif strategy_type == 'semantic':
        return SemanticChunking(chunk_size, chunk_overlap)
    elif strategy_type == 'hybrid':
        return HybridChunking(chunk_size, chunk_overlap)
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
