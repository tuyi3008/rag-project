"""RAG service for intelligent document Q&A using Groq API"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any
import uuid
import os

from app.models.sqlalchemy_models import DocumentChunk

class RAGService:
    def __init__(self):
        # Initialize Groq LLM with API key from environment variable
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",  # Use a versatile model suitable for Q&A tasks
            temperature=0.3,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    
    async def get_relevant_chunks(self, db: AsyncSession, document_id: str, question: str, k: int = 3) -> List[str]:
        """Retrieve relevant chunks from database using simple keyword matching"""
        query = select(DocumentChunk).where(
            DocumentChunk.document_id == uuid.UUID(document_id)
        )
        result = await db.execute(query)
        chunks = result.scalars().all()
        
        # Simple relevance scoring (word matching)
        question_words = set(question.lower().split())
        scored_chunks = []
        for chunk in chunks:
            chunk_words = set(chunk.content.lower().split())
            score = len(question_words.intersection(chunk_words))
            scored_chunks.append((score, chunk.content))
        
        # Sort by relevance and return top k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:k] if score > 0]
    
    async def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generate answer using Groq LLM based on retrieved context"""
        if not context_chunks:
            return "I couldn't find any relevant information in the document to answer your question. Please try asking something else."
        
        # Combine chunks into context
        context = "\n\n---\n\n".join(context_chunks)
        
        # Create prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions based on the provided document content.
            Use only the information from the context to answer the question.
            If the answer is not in the context, say "I don't have enough information to answer that question."
            Be concise and accurate."""),
            ("human", """Context from document:
{context}

Question: {question}

Answer based only on the context above:""")
        ])
        
        # Create chain
        chain = prompt_template | self.llm | StrOutputParser()
        
        # Generate answer
        answer = await chain.ainvoke({
            "context": context,
            "question": question
        })
        
        return answer
    
    async def ask(self, db: AsyncSession, document_id: str, question: str) -> Dict[str, Any]:
        """Main method to ask a question about a document"""
        # 1. Retrieve relevant chunks
        relevant_chunks = await self.get_relevant_chunks(db, document_id, question)
        
        # 2. Generate answer using LLM
        answer = await self.generate_answer(question, relevant_chunks)
        
        # 3. Return response
        return {
            "answer": answer,
            "sources": relevant_chunks[:2]  # Return top 2 sources for citation
        }