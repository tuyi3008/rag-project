"""Chat API endpoint for RAG question answering"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    document_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

# Initialize RAG service
rag_service = RAGService()

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question about a document.
    Uses RAG (Retrieval-Augmented Generation) to provide accurate answers.
    """
    try:
        result = await rag_service.ask(
            db=db,
            document_id=request.document_id,
            question=request.question
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")