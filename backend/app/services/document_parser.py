"""Document parsing service for PDF, DOCX, TXT files"""
import io
from typing import Optional
import PyPDF2
from docx import Document

class DocumentParserService:
    
    @staticmethod
    async def parse_pdf(content: bytes) -> str:
        """Parse PDF file and extract text"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    @staticmethod
    async def parse_docx(content: bytes) -> str:
        """Parse DOCX file and extract text"""
        try:
            doc = Document(io.BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to parse DOCX: {str(e)}")
    
    @staticmethod
    async def parse_txt(content: bytes) -> str:
        """Parse TXT file and extract text"""
        try:
            return content.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                return content.decode("latin-1").strip()
            except Exception as e:
                raise Exception(f"Failed to parse TXT: {str(e)}")
    
    async def parse_document(self, content: bytes, filename: str) -> str:
        """Route to appropriate parser based on file extension"""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        if ext == "pdf":
            return await self.parse_pdf(content)
        elif ext == "docx":
            return await self.parse_docx(content)
        elif ext == "txt":
            return await self.parse_txt(content)
        else:
            raise ValueError(f"Unsupported file type: {ext}")