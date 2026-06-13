"""Add embedding column to document_chunks table"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def add_embedding_column():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        # Add embedding column (384 dimensions for all-MiniLM-L6-v2)
        await conn.execute(text("ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(384);"))
        print("✅ Embedding column added to document_chunks table")
    await engine.dispose()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(add_embedding_column())