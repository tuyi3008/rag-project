import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.sqlalchemy_models import Base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragdb"

async def init_db():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())