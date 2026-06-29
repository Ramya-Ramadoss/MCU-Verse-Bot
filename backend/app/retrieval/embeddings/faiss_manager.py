import os
import faiss
import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple

from backend.app.core.config import settings
from backend.app.db.models.document import Document
from backend.app.db.models.embedding import EmbeddingTrack
from backend.app.retrieval.embeddings.embedder import get_embedder

INDEX_FILE = os.path.join(settings.FAISS_INDEX_PATH, "index.faiss")

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    """
    Splits text into chunks with overlap for better retrieval coverage.
    """
    if len(text) <= max_chars:
        return [text]
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks

class FAISSIndexManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FAISSIndexManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.index = None
        return cls._instance

    def _get_index_dir(self) -> str:
        return os.path.dirname(INDEX_FILE)

    def load_index(self):
        """
        Loads the FAISS index from disk or initializes a new one.
        """
        if self.index is not None:
            return

        index_dir = self._get_index_dir()
        if not os.path.exists(index_dir):
            os.makedirs(index_dir, exist_ok=True)

        if os.path.exists(INDEX_FILE):
            print(f"Loading FAISS index from {INDEX_FILE}...")
            try:
                self.index = faiss.read_index(INDEX_FILE)
            except Exception as e:
                print(f"Failed to load FAISS index: {e}. Reinitializing.")
                self.index = None

        if self.index is None:
            # Initialize new L2 index using dimension from local embedder
            embedder = get_embedder()
            dimension = getattr(embedder.model, "get_embedding_dimension", embedder.model.get_sentence_embedding_dimension)()
            print(f"Initializing new FAISS L2 index with dimension {dimension}...")
            self.index = faiss.IndexFlatL2(dimension)

    def save_index(self):
        """
        Saves the FAISS index to disk.
        """
        if self.index is None:
            return
        index_dir = self._get_index_dir()
        os.makedirs(index_dir, exist_ok=True)
        faiss.write_index(self.index, INDEX_FILE)
        print(f"FAISS index successfully saved to {INDEX_FILE}.")

    def rebuild_index(self, db: Session) -> int:
        """
        Clears the current index, chunks all documents from database,
        generates embeddings, populates FAISS index, and updates DB tracking.
        """
        print("Rebuilding FAISS index from DB documents...")
        embedder = get_embedder()
        dimension = getattr(embedder.model, "get_embedding_dimension", embedder.model.get_sentence_embedding_dimension)()
        
        # Initialize a fresh index
        new_index = faiss.IndexFlatL2(dimension)
        
        # Delete old embedding tracks
        db.query(EmbeddingTrack).delete()
        db.commit()

        documents = db.query(Document).all()
        all_chunks = []
        doc_mappings = []  # List of tuples: (doc_id, chunk_index, text)
        
        for doc in documents:
            chunks = chunk_text(doc.content)
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                doc_mappings.append((doc.id, idx))

        if not all_chunks:
            print("No documents found to index.")
            self.index = new_index
            self.save_index()
            return 0

        # Generate embeddings in batch
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = embedder.get_embeddings(all_chunks)
        embeddings_np = np.array(embeddings).astype("float32")
        
        # Add to FAISS index
        new_index.add(embeddings_np)
        
        # Save tracks to DB
        for i, (doc_id, chunk_idx) in enumerate(doc_mappings):
            track = EmbeddingTrack(
                document_id=doc_id,
                chunk_index=chunk_idx,
                faiss_index_pos=i,
                embedding_model=settings.EMBEDDING_MODEL_NAME,
                embedding_version="1.0"
            )
            db.add(track)
            
        db.commit()
        
        self.index = new_index
        self.save_index()
        return len(all_chunks)

    def search(self, query: str, top_k: int, db: Session) -> List[Tuple[Document, float]]:
        """
        Searches the FAISS index and returns matching Document records along with distance scores.
        """
        self.load_index()
        if self.index is None or self.index.ntotal == 0:
            return []

        embedder = get_embedder()
        query_vector = np.array([embedder.get_embedding(query)]).astype("float32")
        
        # Run search
        # D: distances, I: index positions
        k = min(top_k, self.index.ntotal)
        D, I = self.index.search(query_vector, k)
        
        results = []
        for dist, pos in zip(D[0], I[0]):
            if pos == -1:
                continue
                
            # Find document ID using pos mapping
            track = db.query(EmbeddingTrack).filter(EmbeddingTrack.faiss_index_pos == int(pos)).first()
            if track:
                doc = db.query(Document).filter(Document.id == track.document_id).first()
                if doc:
                    # Convert L2 distance to a pseudo-similarity score (closer to 1.0 means closer match)
                    similarity = float(1.0 / (1.0 + dist))
                    results.append((doc, similarity))
                    
        return results

# Singleton instance getter
faiss_manager = FAISSIndexManager()

def get_faiss_manager() -> FAISSIndexManager:
    return faiss_manager
