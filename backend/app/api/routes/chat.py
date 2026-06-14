"""Chat API endpoint for RAG question answering"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.rag_service import RAGService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    document_id: str
    question: str
    mode: str = "simple"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    conversation_id: str

rag_service = RAGService()
conv_service = ConversationService()

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Create or get conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create new conversation
            conversation_id = await conv_service.create_conversation(
                db=db,
                document_id=request.document_id,
                title=request.question[:50]  # Use first 50 chars as title
            )
        
        # Save user message
        await conv_service.add_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=request.question
        )
        
        # Get answer from RAG
        result = await rag_service.ask(
            db=db,
            document_id=request.document_id,
            question=request.question,
            mode=request.mode
        )
        
        # Save assistant message
        await conv_service.add_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=result["answer"]
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")