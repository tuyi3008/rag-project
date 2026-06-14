"""RAG service for intelligent document Q&A using vector similarity search (pgvector)"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, Optional
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
        
        question_embedding = self.embedding_service.encode(question)
        embedding_str = str(question_embedding)
        
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
            print(f"No relevant chunks found for document {document_id}")
            return []
        
        print(f"Found {len(rows)} relevant chunks (similarity scores: {[round(row[1], 3) for row in rows]})")
        return [row[0] for row in rows]
    
    async def generate_answer(self, question: str, context_chunks: List[str], mode: str = "simple", history: List[Dict] = None) -> str:
        """Generate answer using Groq LLM based on retrieved context, mode, and conversation history"""
        if not context_chunks:
            if mode == "exact":
                return "No relevant content found in the document."
            else:
                return "I couldn't find any relevant information in the document to answer your question. Please try asking something else."
        
        context = "\n\n---\n\n".join(context_chunks)
        
        # Build conversation history string
        history_text = ""
        if history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
            history_text += f"\nCurrent question: {question}"
        else:
            history_text = f"Question: {question}"
        
        if mode == "exact":
            return context_chunks[0]
        
        elif mode == "deep":
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are an expert analyst. Provide a comprehensive, multi-angle answer to the question.

IMPORTANT RULES:
1. Use ONLY the information from the context below
2. Consider the conversation history to understand follow-up questions
3. Organize your answer with clear sections (e.g., Overview, Key Points, Analysis)
4. Be thorough and insightful
5. If information is missing, state what's not in the document"""),
                ("human", """Context from document:
{context}

{history_text}

Provide a detailed analysis:""")
            ])
        else:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """Answer the question in ONE short sentence (under 20 words). 
Be concise and direct. Use ONLY the context from the document.
Consider conversation history for follow-up questions like "more", "what else", "continue"."""),
                ("human", """Context from document:
{context}

{history_text}

One-sentence answer:""")
            ])
        
        chain = prompt_template | self.llm | StrOutputParser()
        
        answer = await chain.ainvoke({
            "context": context,
            "history_text": history_text
        })
        
        return answer
    
    async def ask(self, db: AsyncSession, document_id: str, question: str, mode: str = "simple", history: List[Dict] = None) -> Dict[str, Any]:
        """Main method to ask a question about a document with different answer modes and conversation history"""
        relevant_chunks = await self.get_relevant_chunks(db, document_id, question)
        answer = await self.generate_answer(question, relevant_chunks, mode, history)
        
        return {
            "answer": answer,
            "sources": relevant_chunks[:2] if relevant_chunks else []
        }