"""Embedding service for generating vector embeddings using sentence-transformers"""
from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self._initialized = True
        print(f"✅ EmbeddingService initialized (dimension: {self.dimension})")
    
    def encode(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()