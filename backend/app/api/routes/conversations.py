"""Conversation history API endpoint"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])

class ConversationResponse(BaseModel):
    id: str
    title: str
    document_id: str
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime

conv_service = ConversationService()

@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations"""
    conversations = await conv_service.get_user_conversations(db=db)
    return conversations

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get messages for a specific conversation"""
    messages = await conv_service.get_conversation_history(
        db=db,
        conversation_id=conversation_id
    )
    return messages