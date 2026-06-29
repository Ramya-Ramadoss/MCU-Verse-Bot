import os
import pickle
from dataclasses import dataclass
from typing import List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.models.document import Document
from backend.app.db.models.embedding import EmbeddingTrack


@dataclass
class IndexedChunk:
    document_id: str
    chunk_index: int
    text: str
    title: str
    category: str


class EmbeddingService:
    _model: Optional[SentenceTransformer] = None

    def __init__(self) -> None:
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.index_path = settings.FAISS_INDEX_PATH
        self.meta_path = f"{self.index_path}_meta.pkl"
        self._index: Optional[faiss.IndexFlatIP] = None
        self._chunks: List[IndexedChunk] = []

    @property
    def model(self) -> SentenceTransformer:
        if EmbeddingService._model is None:
            EmbeddingService._model = SentenceTransformer(self.model_name)
        return EmbeddingService._model

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        vectors = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.array(vectors, dtype=np.float32)

    def chunk_document(self, doc: Document, chunk_size: int = 500) -> List[str]:
        content = doc.content or ""
        if len(content) <= chunk_size:
            return [content]
        chunks = []
        words = content.split()
        current: List[str] = []
        length = 0
        for word in words:
            current.append(word)
            length += len(word) + 1
            if length >= chunk_size:
                chunks.append(" ".join(current))
                current = []
                length = 0
        if current:
            chunks.append(" ".join(current))
        return chunks

    def build_index(self, db: Session) -> dict:
        documents = db.query(Document).all()
        all_chunks: List[IndexedChunk] = []
        texts: List[str] = []

        db.query(EmbeddingTrack).delete()
        db.commit()

        for doc in documents:
            chunks = self.chunk_document(doc)
            for idx, chunk in enumerate(chunks):
                all_chunks.append(
                    IndexedChunk(
                        document_id=doc.id,
                        chunk_index=idx,
                        text=chunk,
                        title=doc.title,
                        category=doc.category,
                    )
                )
                texts.append(chunk)
                track = EmbeddingTrack(
                    document_id=doc.id,
                    chunk_index=idx,
                    embedding_model=self.model_name,
                    embedding_version="1.0",
                )
                db.add(track)

        if not texts:
            self._index = None
            self._chunks = []
            return {"chunks": 0, "documents": len(documents)}

        vectors = self.embed_texts(texts)
        dim = vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vectors)
        self._index = index
        self._chunks = all_chunks
        self._save_index(index, all_chunks)
        db.commit()
        return {"chunks": len(all_chunks), "documents": len(documents), "dimension": dim}

    def _save_index(self, index: faiss.IndexFlatIP, chunks: List[IndexedChunk]) -> None:
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(chunks, f)

    def load_index(self) -> bool:
        if not os.path.exists(self.index_path) or not os.path.exists(self.meta_path):
            return False
        self._index = faiss.read_index(self.index_path)
        with open(self.meta_path, "rb") as f:
            self._chunks = pickle.load(f)
        return True

    def search(self, query: str, top_k: int = 5) -> List[Tuple[IndexedChunk, float]]:
        if self._index is None and not self.load_index():
            return []
        if self._index is None or not self._chunks:
            return []
        vector = self.embed_texts([query])
        scores, indices = self._index.search(vector, min(top_k, len(self._chunks)))
        results: List[Tuple[IndexedChunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._chunks):
                continue
            results.append((self._chunks[idx], float(score)))
        return results

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)
