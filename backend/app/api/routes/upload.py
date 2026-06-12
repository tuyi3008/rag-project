"""File upload API endpoint"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.file_storage import FileStorageService
from app.services.document_parser import DocumentParserService
from app.services.db_service import DatabaseService
from app.services.chunking_service import ChunkingService
from app.core.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS
import hashlib

router = APIRouter(prefix="/upload", tags=["upload"])
file_storage = FileStorageService()
parser = DocumentParserService()
db_service = DatabaseService()
chunker = ChunkingService()

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document"""
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE // 1024 // 1024}MB")
    
    # Check file extension
    ext = "." + file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}")
    
    # Calculate file hash
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
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "file_size": len(content),
            "chunk_count": len(chunks),
            "status": "ready",
            "message": f"Document processed successfully. Extracted {len(chunks)} chunks."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")