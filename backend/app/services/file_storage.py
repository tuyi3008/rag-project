"""MinIO file storage service"""
from minio import Minio
from minio.error import S3Error
from app.core.config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
import uuid
import io
from datetime import timedelta

class FileStorageService:
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure bucket exists"""
        if not self.client.bucket_exists(MINIO_BUCKET):
            self.client.make_bucket(MINIO_BUCKET)
    
    async def upload_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file to MinIO and return object name"""
        # Generate unique object name
        ext = filename.split(".")[-1] if "." in filename else "bin"
        object_name = f"{uuid.uuid4()}.{ext}"
        
        # Convert bytes to BytesIO (file-like object)
        file_stream = io.BytesIO(file_data)
        file_size = len(file_data)
        
        # Upload to MinIO - data must be a file-like object with .read()
        self.client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            data=file_stream,          # ← 改成 BytesIO 对象，不是 bytes
            length=file_size,
            content_type=content_type
        )
        
        return object_name
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """Get presigned URL for file access"""
        return self.client.presigned_get_object(
            bucket_name=MINIO_BUCKET,
            object_name=object_name,
            expires=expires
        )