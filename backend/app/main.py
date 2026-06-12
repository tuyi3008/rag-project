from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="RAG Document QA System",
    description="Intelligent document Q&A system based on RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI endpoint
    redoc_url="/redoc"     # ReDoc endpoint
)

# Configure CORS (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev server addresses
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Pydantic Models (Request/Response Schemas) ==========

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
async def upload_file(file: UploadFile = File(...)):
    """Upload document (placeholder - full implementation coming soon)
    
    - Accepts PDF, DOCX, TXT files
    - Stores file in MinIO
    - Extracts text and creates vector embeddings
    """
    return UploadResponse(
        document_id="temp_id",
        filename=file.filename,
        file_size=file.size or 0,
        status="received",
        message="File received, processing..."
    )

# ========== Server Configuration ==========

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )