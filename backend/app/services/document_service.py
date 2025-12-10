"""Document service for handling file uploads with deduplication."""
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from fastapi import UploadFile

from app.config import get_settings
from app.services.rag_service import rag_service
from app.services.document_loader import DocumentLoaderService

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of a document upload operation."""
    id: str
    filename: str
    status: str  # "uploaded", "duplicate", "error"
    message: str
    chunks_created: int = 0


class DocumentService:
    """Service for handling document uploads with hash-based deduplication."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md'}
    HASH_REGISTRY_FILE = ".document_hashes.json"
    
    def __init__(self):
        self.settings = get_settings()
        self.uploads_dir = Path(self.settings.data_dir).parent / "uploads"
        self.hash_registry_path = self.uploads_dir / self.HASH_REGISTRY_FILE
        self._document_loader = DocumentLoaderService()
        self._ensure_uploads_dir()
    
    def _ensure_uploads_dir(self) -> None:
        """Ensure the uploads directory exists."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_hash_registry(self) -> dict[str, dict]:
        """Load the registry of document hashes."""
        if not self.hash_registry_path.exists():
            return {}
        
        try:
            with open(self.hash_registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading hash registry: {e}")
            return {}
    
    def _save_hash_registry(self, registry: dict[str, dict]) -> None:
        """Save the registry of document hashes."""
        with open(self.hash_registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def _calculate_content_hash(self, content: bytes) -> str:
        """Generate MD5 hash of document content."""
        return hashlib.md5(content).hexdigest()
    
    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if a document with this hash already exists."""
        registry = self._load_hash_registry()
        return content_hash in registry
    
    def _get_file_extension(self, filename: str) -> str:
        """Get lowercase file extension."""
        return Path(filename).suffix.lower()
    
    async def upload_document(self, file: UploadFile) -> UploadResult:
        """
        Upload and process a document for RAG.
        
        Args:
            file: The uploaded file
            
        Returns:
            UploadResult with status and details
        """
        filename = file.filename or "unknown"
        
        # Validate file extension
        ext = self._get_file_extension(filename)
        if ext not in self.SUPPORTED_EXTENSIONS:
            return UploadResult(
                id="",
                filename=filename,
                status="error",
                message=f"Unsupported file type: {ext}. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
        
        try:
            # Read file content
            content = await file.read()
            
            if not content:
                return UploadResult(
                    id="",
                    filename=filename,
                    status="error",
                    message="Empty file"
                )
            
            # Calculate content hash
            content_hash = self._calculate_content_hash(content)
            
            # Check for duplicates
            if self._is_duplicate(content_hash):
                registry = self._load_hash_registry()
                existing = registry[content_hash]
                return UploadResult(
                    id=existing.get("doc_ids", [""])[0],
                    filename=filename,
                    status="duplicate",
                    message=f"Document already exists (uploaded as '{existing.get('filename', 'unknown')}')",
                    chunks_created=0
                )
            
            # Save file to disk
            safe_filename = self._sanitize_filename(filename)
            file_path = self.uploads_dir / f"{content_hash[:8]}_{safe_filename}"
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"Saved file to {file_path}")
            
            # Extract text content
            text = self._document_loader._extract_text_from_file(file_path)
            
            if not text:
                return UploadResult(
                    id="",
                    filename=filename,
                    status="error",
                    message="Could not extract text from document"
                )
            
            # Chunk the text
            chunks = self._document_loader._chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            
            # Add each chunk to RAG
            doc_ids = []
            for i, chunk in enumerate(chunks):
                doc_id = rag_service.add_document(
                    content=chunk,
                    metadata={
                        "source": filename,
                        "file_path": str(file_path),
                        "content_hash": content_hash,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "upload_type": "user_upload",
                    }
                )
                doc_ids.append(doc_id)
            
            # Update hash registry
            registry = self._load_hash_registry()
            registry[content_hash] = {
                "filename": filename,
                "file_path": str(file_path),
                "doc_ids": doc_ids,
                "chunks": len(chunks),
            }
            self._save_hash_registry(registry)
            
            return UploadResult(
                id=doc_ids[0] if doc_ids else "",
                filename=filename,
                status="uploaded",
                message=f"Successfully processed document into {len(chunks)} chunks",
                chunks_created=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {e}")
            return UploadResult(
                id="",
                filename=filename,
                status="error",
                message=str(e)
            )
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be safe for filesystem."""
        # Keep only alphanumeric, dots, underscores, and hyphens
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
        sanitized = "".join(c if c in safe_chars else "_" for c in filename)
        return sanitized or "document"
    
    def list_documents(self) -> list[dict]:
        """List all uploaded documents."""
        registry = self._load_hash_registry()
        documents = []
        
        for content_hash, info in registry.items():
            documents.append({
                "content_hash": content_hash,
                "filename": info.get("filename", "unknown"),
                "chunks": info.get("chunks", 0),
                "file_path": info.get("file_path", ""),
            })
        
        return documents
    
    def delete_document(self, content_hash: str) -> bool:
        """Delete a document by its content hash."""
        registry = self._load_hash_registry()
        
        if content_hash not in registry:
            return False
        
        info = registry[content_hash]
        
        # Delete the file
        file_path = Path(info.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        # Note: We can't easily delete from ChromaDB without storing doc IDs
        # The documents will remain in ChromaDB but won't be re-indexed
        
        del registry[content_hash]
        self._save_hash_registry(registry)
        
        return True


# Global instance
document_service = DocumentService()
