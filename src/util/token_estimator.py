"""Token estimation tool for chunking with model-specific encoders."""

import logging
from typing import Dict, List, Optional, Union, Any
import tiktoken

logger = logging.getLogger(__name__)

# Model configurations (extended from scoring.py)
MODEL_CONFIGS = {
    "gpt-4o-mini": {
        "max_tokens": 128000,
        "encoding": "cl100k_base",
        "output_tokens": 16384
    },
    "gpt-4o": {
        "max_tokens": 128000,
        "encoding": "cl100k_base",
        "output_tokens": 4096
    },
    "gpt-4-turbo": {
        "max_tokens": 128000,
        "encoding": "cl100k_base",
        "output_tokens": 4096
    },
    "gpt-4": {
        "max_tokens": 8192,
        "encoding": "cl100k_base",
        "output_tokens": 4096
    },
    "gpt-3.5-turbo": {
        "max_tokens": 16385,
        "encoding": "cl100k_base",
        "output_tokens": 4096
    },
    "claude-3-opus": {
        "max_tokens": 200000,
        "encoding": "cl100k_base",  # approximation
        "output_tokens": 4096
    },
    "claude-3-sonnet": {
        "max_tokens": 200000,
        "encoding": "cl100k_base",  # approximation
        "output_tokens": 4096
    },
    "claude-3-haiku": {
        "max_tokens": 200000,
        "encoding": "cl100k_base",  # approximation
        "output_tokens": 4096
    }
}


class TokenEstimator:
    """Token estimation tool for various LLM models."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize token estimator for specific model.
        
        Args:
            model: Model name to use for token estimation
        """
        self.model = model
        self.config = MODEL_CONFIGS.get(model, MODEL_CONFIGS["gpt-4o-mini"])
        
        try:
            self.encoding = tiktoken.get_encoding(self.config["encoding"])
        except Exception as e:
            logger.warning(f"Failed to load encoding for {model}: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for given text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated number of tokens
        """
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token estimation failed: {e}, using character-based estimate")
            # 한국어/영어 혼합 텍스트의 경우 대략적인 추정 (from scoring.py)
            return len(text) // 3
    
    def estimate_tokens_batch(self, texts: List[str]) -> List[int]:
        """
        Estimate token count for multiple texts.
        
        Args:
            texts: List of texts to estimate tokens for
            
        Returns:
            List of estimated token counts
        """
        return [self.estimate_tokens(text) for text in texts]
    
    def get_max_tokens(self) -> int:
        """Get maximum token limit for the model."""
        return self.config["max_tokens"]
    
    def get_output_tokens(self) -> int:
        """Get maximum output tokens for the model."""
        return self.config["output_tokens"]
    
    def get_available_tokens(self, prompt_tokens: int = 0) -> int:
        """
        Get available tokens for content after reserving space for prompt and output.
        
        Args:
            prompt_tokens: Number of tokens used for prompt
            
        Returns:
            Available tokens for content
        """
        total_tokens = self.get_max_tokens()
        output_tokens = self.get_output_tokens()
        return max(0, total_tokens - prompt_tokens - output_tokens)


def estimate_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Estimate token count for given text and model (compatible with scoring.py).
    
    Args:
        text: Text to estimate tokens for
        model: Model name to use for estimation
        
    Returns:
        Estimated number of tokens
    """
    try:
        config = MODEL_CONFIGS.get(model, MODEL_CONFIGS["gpt-4o-mini"])
        encoding = tiktoken.get_encoding(config["encoding"])
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token estimation failed: {e}, using character-based estimate")
        # 한국어/영어 혼합 텍스트의 경우 대략적인 추정
        return len(text) // 3


class TextChunker:
    """Text chunking tool with token-aware splitting."""
    
    def __init__(
        self, 
        model: str = "gpt-4o-mini",
        max_chunk_tokens: int = 8000,
        chunk_overlap_tokens: int = 200
    ):
        """
        Initialize text chunker.
        
        Args:
            model: Model name to use for token estimation
            max_chunk_tokens: Maximum tokens per chunk
            chunk_overlap_tokens: Overlap tokens between chunks
        """
        self.estimator = TokenEstimator(model)
        self.max_chunk_tokens = max_chunk_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
    
    def chunk_text(self, text: str, preserve_sentences: bool = True) -> List[str]:
        """
        Split text into chunks based on token limits.
        
        Args:
            text: Text to chunk
            preserve_sentences: Whether to try to preserve sentence boundaries
            
        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []
        
        total_tokens = self.estimator.estimate_tokens(text)
        
        # If text is small enough, return as single chunk
        if total_tokens <= self.max_chunk_tokens:
            return [text]
        
        # Split into chunks
        if preserve_sentences:
            return self._chunk_by_sentences(text)
        else:
            return self._chunk_by_tokens(text)
    
    def chunk_documents(
        self, 
        documents: List[Dict[str, Any]], 
        text_field: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents while preserving metadata.
        
        Args:
            documents: List of documents with text and metadata
            text_field: Field name containing the text content
            
        Returns:
            List of document chunks with preserved metadata
        """
        chunked_docs = []
        
        for doc_idx, doc in enumerate(documents):
            text = doc.get(text_field, "")
            if not text:
                continue
                
            chunks = self.chunk_text(text)
            
            for chunk_idx, chunk in enumerate(chunks):
                chunked_doc = doc.copy()  # Preserve metadata
                chunked_doc[text_field] = chunk
                chunked_doc["chunk_id"] = f"{doc.get('id', doc_idx)}_{chunk_idx}"
                chunked_doc["chunk_index"] = chunk_idx
                chunked_doc["total_chunks"] = len(chunks)
                chunked_doc["original_doc_id"] = doc.get('id', doc_idx)
                chunked_docs.append(chunked_doc)
        
        return chunked_docs
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text by sentences while respecting token limits."""
        # Split by sentence boundaries
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.estimator.estimate_tokens(sentence)
            
            # If single sentence exceeds limit, split it further
            if sentence_tokens > self.max_chunk_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0
                
                # Split long sentence by words or characters
                sentence_chunks = self._chunk_by_tokens(sentence)
                chunks.extend(sentence_chunks[:-1])  # Add all but last
                
                # Start new chunk with last part
                if sentence_chunks:
                    current_chunk = sentence_chunks[-1]
                    current_tokens = self.estimator.estimate_tokens(current_chunk)
                
                continue
            
            # Check if adding sentence exceeds limit
            if current_tokens + sentence_tokens > self.max_chunk_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Add overlaps if requested
        if self.chunk_overlap_tokens > 0 and len(chunks) > 1:
            chunks = self._add_overlaps(chunks)
        
        return chunks
    
    def _chunk_by_tokens(self, text: str) -> List[str]:
        """Chunk text by token count, splitting at word boundaries when possible."""
        words = text.split()
        chunks = []
        current_chunk_words = []
        current_tokens = 0
        
        for word in words:
            word_tokens = self.estimator.estimate_tokens(word + " ")
            
            if current_tokens + word_tokens > self.max_chunk_tokens and current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                chunks.append(chunk_text)
                current_chunk_words = [word]
                current_tokens = word_tokens
            else:
                current_chunk_words.append(word)
                current_tokens += word_tokens
        
        # Add remaining chunk
        if current_chunk_words:
            chunk_text = " ".join(current_chunk_words)
            chunks.append(chunk_text)
        
        # Add overlaps if requested
        if self.chunk_overlap_tokens > 0 and len(chunks) > 1:
            chunks = self._add_overlaps(chunks)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be enhanced with proper sentence boundary detection
        import re
        
        # Split on sentence endings, but be careful with abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _add_overlaps(self, chunks: List[str]) -> List[str]:
        """Add overlaps between chunks."""
        if not chunks or len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]  # First chunk unchanged
        
        for i in range(1, len(chunks)):
            # Get overlap from previous chunk
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # Try to get last part of previous chunk for overlap
            prev_words = prev_chunk.split()
            overlap_words = []
            overlap_tokens = 0
            
            # Add words from end of previous chunk until we reach overlap limit
            for word in reversed(prev_words):
                word_tokens = self.estimator.estimate_tokens(word + " ")
                if overlap_tokens + word_tokens <= self.chunk_overlap_tokens:
                    overlap_words.insert(0, word)
                    overlap_tokens += word_tokens
                else:
                    break
            
            # Combine overlap with current chunk
            if overlap_words:
                overlap_text = " ".join(overlap_words)
                combined_chunk = overlap_text + " " + current_chunk
                overlapped_chunks.append(combined_chunk)
            else:
                overlapped_chunks.append(current_chunk)
        
        return overlapped_chunks


def create_chunks_for_model(
    texts: List[str], 
    model: str = "gpt-4o-mini",
    max_chunk_tokens: int = 8000,
    preserve_sentences: bool = True
) -> List[List[str]]:
    """
    Create chunks for multiple texts optimized for specific model.
    
    Args:
        texts: List of texts to chunk
        model: Model name to optimize for
        max_chunk_tokens: Maximum tokens per chunk
        preserve_sentences: Whether to preserve sentence boundaries
        
    Returns:
        List of chunk lists (one list per input text)
    """
    chunker = TextChunker(model, max_chunk_tokens)
    return [chunker.chunk_text(text, preserve_sentences) for text in texts]


def estimate_chunk_count(text: str, model: str = "gpt-4o-mini", max_chunk_tokens: int = 8000) -> int:
    """
    Estimate how many chunks a text will be split into.
    
    Args:
        text: Text to estimate chunks for
        model: Model name to use for token estimation
        max_chunk_tokens: Maximum tokens per chunk
        
    Returns:
        Estimated number of chunks
    """
    total_tokens = estimate_tokens(text, model)
    return max(1, (total_tokens + max_chunk_tokens - 1) // max_chunk_tokens)  # Ceiling division


def get_optimal_chunk_size(
    model: str = "gpt-4o-mini", 
    prompt_tokens: int = 1000,
    buffer_tokens: int = 500
) -> int:
    """
    Get optimal chunk size for a model given prompt overhead.
    
    Args:
        model: Model name
        prompt_tokens: Tokens used for prompt template
        buffer_tokens: Safety buffer tokens
        
    Returns:
        Optimal chunk size in tokens
    """
    estimator = TokenEstimator(model)
    available_tokens = estimator.get_available_tokens(prompt_tokens)
    return max(1000, available_tokens - buffer_tokens)  # Minimum 1000 tokens per chunk