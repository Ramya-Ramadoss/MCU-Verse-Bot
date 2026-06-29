import torch
from sentence_transformers import SentenceTransformer
from typing import List
import hashlib
import numpy as np
from backend.app.core.config import settings


class HashingEmbeddingModel:
    """Small deterministic fallback used when the configured model is unavailable."""

    dimension = 384

    def get_sentence_embedding_dimension(self) -> int:
        return self.dimension

    def get_embedding_dimension(self) -> int:
        return self.dimension

    def encode(self, texts, convert_to_numpy=True):
        single = isinstance(texts, str)
        items = [texts] if single else list(texts)
        vectors = [self._encode_one(item) for item in items]
        array = np.array(vectors, dtype="float32")
        return array[0] if single else array

    def _encode_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype="float32")
        for token in str(text).lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

class EmbedderService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbedderService, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # Detect device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing EmbedderService: Loading {settings.EMBEDDING_MODEL_NAME} on {self.device}...")
        
        # Load model locally; fall back to deterministic embeddings if the model
        # cannot be downloaded in constrained CI/offline environments.
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device=self.device)
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print("Falling back to deterministic HashingEmbeddingModel.")
            self.model = HashingEmbeddingModel()
        self._initialized = True

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates embedding vector for a single text.
        """
        # Ensure single string input
        if not isinstance(text, str):
            text = str(text)
        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embedding vectors for a list of texts in batch.
        """
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

# Global Singleton
embedder_service = None

def get_embedder() -> EmbedderService:
    global embedder_service
    if embedder_service is None:
        embedder_service = EmbedderService()
    return embedder_service
