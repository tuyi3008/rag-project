"""Text chunking service for RAG using LangChain recursive splitter"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ChunkingService:
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize recursive character text splitter.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",      # Paragraphs
                "\n",        # New lines
                ". ",        # English sentences
                "! ",
                "? ",
                "; ",
                ", ",        # English clauses
                " ",         # Spaces
                ""           # Characters
            ]
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks using recursive method.
        Preserves semantic boundaries (paragraphs -> sentences -> words).
        """
        if not text or not text.strip():
            return []
        
        chunks = self.splitter.split_text(text)
        
        # Filter out empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        return chunks