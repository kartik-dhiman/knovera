from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer

from app.core.config import settings


class Embedder:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.embedding_model)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        from app.core.utils import normalize_text
        norm = [normalize_text(t) for t in texts]
        vectors = self.model.encode(norm, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        from app.core.utils import normalize_text
        norm = normalize_text(text)
        vector = self.model.encode([norm], normalize_embeddings=True, show_progress_bar=False)
        return vector[0].tolist()
