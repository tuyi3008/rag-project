"""Conversation service for storing chat history"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.sqlalchemy_models import Conversation, Message
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class ConversationService:
    
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        document_id: str,
        title: str = None
    ) -> str:
        """Create a new conversation and return conversation ID"""
        conversation_id = uuid.uuid4()
        conversation = Conversation(
            id=conversation_id,
            document_id=uuid.UUID(document_id),
            title=title or "New Conversation",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return str(conversation_id)
    
    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:
        """Add a message to a conversation"""
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role=role,
            content=content,
            created_at=datetime.utcnow()
        )
        db.add(message)
        
        # Update conversation updated_at
        stmt = select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
        result = await db.execute(stmt)
        conversation = result.scalar_one()
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
    
    @staticmethod
    async def get_conversation_history(
        db: AsyncSession,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent messages from a conversation"""
        stmt = select(Message).where(
            Message.conversation_id == uuid.UUID(conversation_id)
        ).order_by(Message.created_at).limit(limit)
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.created_at}
            for msg in messages
        ]
    
    @staticmethod
    async def get_user_conversations(
        db: AsyncSession,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent conversations (simplified - no user auth yet)"""
        stmt = select(Conversation).order_by(
            desc(Conversation.updated_at)
        ).limit(limit)
        
        result = await db.execute(stmt)
        conversations = result.scalars().all()
        
        return [
            {
                "id": str(conv.id),
                "title": conv.title,
                "document_id": str(conv.document_id),
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            }
            for conv in conversations
        ]