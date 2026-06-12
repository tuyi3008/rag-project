from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from app.core.database import get_db
from app.services.file_storage import FileStorageService
from app.services.document_parser import DocumentParserService
from app.services.db_service import DatabaseService
from app.services.chunking_service import ChunkingService
from app.core.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
import hashlib

# Create FastAPI application
app = FastAPI(
    title="RAG Document QA System",
    description="Intelligent document Q&A system based on RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_storage = FileStorageService()
parser = DocumentParserService()
db_service = DatabaseService()
chunker = ChunkingService(chunk_size=512, chunk_overlap=50)

# ========== Pydantic Models ==========

class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: str

class UploadResponse(BaseModel):
    """File upload response schema"""
    document_id: str
    filename: str
    file_size: int
    chunk_count: int
    status: str
    message: str

# ========== API Endpoints ==========

@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Welcome to RAG Document QA System",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document"""
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE // 1024 // 1024}MB")
    
    # Check file extension
    ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")
    
    # Calculate file hash for deduplication (optional)
    file_hash = hashlib.sha256(content).hexdigest()
    
    try:
        # 1. Upload to MinIO
        object_name = await file_storage.upload_file(
            content, 
            file.filename, 
            file.content_type or "application/octet-stream"
        )
        
        # 2. Parse document and extract text
        extracted_text = await parser.parse_document(content, file.filename)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No text content found in document")
        
        # 3. Create document record in database
        document_id = await db_service.create_document(
            db, 
            file.filename, 
            len(content), 
            file_hash,
            object_name
        )
        
        # 4. Chunk the text
        chunks = chunker.chunk_text(extracted_text)
        
        # 5. Save chunks to database
        await db_service.save_chunks(db, document_id, chunks)
        
        # 6. Update document status
        await db_service.update_document_status(db, document_id, "ready", len(chunks))
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=len(content),
            chunk_count=len(chunks),
            status="ready",
            message=f"Document processed successfully. Extracted {len(chunks)} chunks."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# ========== Server Configuration ==========

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )