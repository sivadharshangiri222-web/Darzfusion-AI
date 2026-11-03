"""Embedding service supporting Google Gemini embeddings and deterministic fallback."""

import hashlib
import logging
import math
from typing import List, Union
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates vector embeddings for document chunks and queries."""

    def __init__(self):
        self.embedding_model = settings.EMBEDDING_MODEL
        self.is_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
        if self.is_configured:
            genai.configure(api_key=settings.GEMINI_API_KEY)

    def _fallback_embedding(self, text: str, dim: int = 768) -> List[float]:
        """Deterministic unit vector fallback for offline testing or when API key is unset."""
        vec = [0.0] * dim
        words = text.lower().split()
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec

    async def get_embedding(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """Generate embedding vector for a single string."""
        if not self.is_configured:
            return self._fallback_embedding(text)

        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type=task_type,
            )
            if "embedding" in result:
                return result["embedding"]
            return self._fallback_embedding(text)
        except Exception as e:
            logger.warning(f"Gemini embed_content failed ({e}), falling back to deterministic embedding.")
            return self._fallback_embedding(text)

    async def get_embeddings(
        self, texts: List[str], task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """Generate embeddings for a batch of strings."""
        if not texts:
            return []

        if not self.is_configured:
            return [self._fallback_embedding(t) for t in texts]

        try:
            # Batch embedding via Gemini API
            result = genai.embed_content(
                model=self.embedding_model,
                content=texts,
                task_type=task_type,
            )
            if "embedding" in result:
                # If single returned
                emb = result["embedding"]
                if emb and isinstance(emb[0], list):
                    return emb
                return [emb]
            return [self._fallback_embedding(t) for t in texts]
        except Exception as e:
            logger.warning(f"Batch embedding failed ({e}), falling back to local embeddings.")
            return [self._fallback_embedding(t) for t in texts]


embedding_service = EmbeddingService()
