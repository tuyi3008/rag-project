"""RAG service for intelligent document Q&A using vector similarity search (pgvector)"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any
import uuid
import os

from app.services.embedding_service import EmbeddingService

class RAGService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            groq_api_key=api_key
        )
        self.embedding_service = EmbeddingService()
    
    async def get_relevant_chunks(self, db: AsyncSession, document_id: str, question: str, k: int = 3) -> List[str]:
        """Retrieve relevant chunks using vector similarity search (pgvector)"""
        
        # Generate embedding for the question
        question_embedding = self.embedding_service.encode(question)
        
        # Convert to string format for pgvector
        embedding_str = str(question_embedding)
        
        # Vector similarity search using cosine distance (<=> operator)
        query = text("""
            SELECT content, 1 - (embedding <=> CAST(:embedding AS vector)) as similarity
            FROM document_chunks
            WHERE document_id = CAST(:document_id AS uuid)
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :k
        """)
        
        result = await db.execute(query, {
            "embedding": embedding_str,
            "document_id": document_id,
            "k": k
        })
        
        rows = result.fetchall()
        
        if not rows:
            print(f"⚠️ No relevant chunks found for document {document_id}")
            return []
        
        print(f"✅ Found {len(rows)} relevant chunks (similarity scores: {[round(row[1], 3) for row in rows]})")
        return [row[0] for row in rows]
    
    async def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generate answer using Groq LLM based on retrieved context"""
        if not context_chunks:
            return "I couldn't find any relevant information in the document to answer your question. Please try asking something else."
        
        context = "\n\n---\n\n".join(context_chunks)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions based on the provided document content.
            Use only the information from the context to answer the question.
            If the answer is not in the context, say "I cannot find that information in the document."
            Be concise and accurate.
            Answer in the same language as the question."""),
            ("human", """Context from document:
{context}

Question: {question}

Answer based only on the context above:""")
        ])
        
        chain = prompt_template | self.llm | StrOutputParser()
        
        answer = await chain.ainvoke({
            "context": context,
            "question": question
        })
        
        return answer
    
    async def ask(self, db: AsyncSession, document_id: str, question: str) -> Dict[str, Any]:
        """Main method to ask a question about a document"""
        # 1. Retrieve relevant chunks using vector search
        relevant_chunks = await self.get_relevant_chunks(db, document_id, question)
        
        # 2. Generate answer using LLM
        answer = await self.generate_answer(question, relevant_chunks)
        
        return {
            "answer": answer,
            "sources": relevant_chunks[:2]
        }