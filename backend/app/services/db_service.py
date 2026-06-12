"""Database service for document operations"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sqlalchemy_models import Document, DocumentChunk
import uuid
from datetime import datetime

class DatabaseService:
    
    @staticmethod
    async def create_document(
        db: AsyncSession,
        filename: str,
        file_size: int,
        file_hash: str,
        object_name: str
    ) -> str:
        """Create document record and return document ID"""
        document_id = uuid.uuid4()
        document = Document(
            id=document_id,
            filename=filename,
            file_size=file_size,
            file_hash=file_hash,
            extra_metadata={"object_name": object_name},
            status="processing",
            created_at=datetime.utcnow()
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return str(document_id)
    
    @staticmethod
    async def update_document_status(db: AsyncSession, document_id: str, status: str, chunk_count: int = 0):
        """Update document status"""
        stmt = select(Document).where(Document.id == uuid.UUID(document_id))
        result = await db.execute(stmt)
        document = result.scalar_one()
        document.status = status
        document.chunk_count = chunk_count
        await db.commit()
    
    @staticmethod
    async def save_chunks(db: AsyncSession, document_id: str, chunks: list):
        """Save document chunks to database"""
        for i, chunk in enumerate(chunks):
            chunk_record = DocumentChunk(
                document_id=uuid.UUID(document_id),
                content=chunk,
                chunk_index=i,
                extra_metadata={"source": "parsed"}
            )
            db.add(chunk_record)
        await db.commit()