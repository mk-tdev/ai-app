"""Document loader service for auto-loading documents on startup."""
import logging
import hashlib
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

from app.config import get_settings
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class DocumentLoaderService:
    """Service for loading documents from the data folder."""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.md'}
    LOADED_DOCS_FILE = ".loaded_docs"
    
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = Path(self.settings.data_dir)
        self.loaded_docs_path = self.data_dir / self.LOADED_DOCS_FILE
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate hash of file content for change detection."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _load_loaded_docs(self) -> dict[str, str]:
        """Load the registry of already loaded documents."""
        if not self.loaded_docs_path.exists():
            return {}
        
        loaded = {}
        try:
            with open(self.loaded_docs_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:
                        filename, hash_val = line.split(':', 1)
                        loaded[filename] = hash_val
        except Exception as e:
            logger.warning(f"Error reading loaded docs file: {e}")
            return {}
        return loaded
    
    def _save_loaded_docs(self, loaded: dict[str, str]) -> None:
        """Save the registry of loaded documents."""
        with open(self.loaded_docs_path, 'w') as f:
            for filename, hash_val in loaded.items():
                f.write(f"{filename}:{hash_val}\n")
    
    def _extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text content from a PDF file."""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            return ""
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """Extract text content from a file based on its extension."""
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif ext in {'.txt', '.md'}:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return ""
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []
        
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]
    
    def load_documents(self, force_reload: bool = False) -> int:
        """Load all documents from the data folder that haven't been loaded yet."""
        logger.info(f"Looking for documents in: {self.data_dir}")
        
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist")
            return 0
        
        loaded_docs = {} if force_reload else self._load_loaded_docs()
        new_docs_count = 0
        
        # List all files in data directory
        files_found = list(self.data_dir.iterdir())
        logger.info(f"Found {len(files_found)} items in data directory")
        
        for file_path in files_found:
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                logger.debug(f"Skipping unsupported file: {file_path.name}")
                continue
            
            filename = file_path.name
            file_hash = self._get_file_hash(file_path)
            
            logger.info(f"Processing file: {filename}")
            
            # Skip if already loaded with same hash
            if filename in loaded_docs and loaded_docs[filename] == file_hash:
                logger.info(f"Skipping already loaded document: {filename}")
                continue
            
            logger.info(f"Loading document: {filename}")
            
            # Extract text content
            text = self._extract_text_from_file(file_path)
            if not text:
                logger.warning(f"No text extracted from {filename}")
                continue
            
            logger.info(f"Extracted {len(text)} characters from {filename}")
            
            # Chunk the text
            chunks = self._chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            
            # Add each chunk to the RAG service
            for i, chunk in enumerate(chunks):
                rag_service.add_document(
                    content=chunk,
                    metadata={
                        "source": filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                )
            
            loaded_docs[filename] = file_hash
            new_docs_count += 1
            logger.info(f"Successfully loaded {len(chunks)} chunks from {filename}")
        
        # Save the updated registry
        self._save_loaded_docs(loaded_docs)
        
        logger.info(f"Document loading complete. New docs: {new_docs_count}, Total in RAG: {rag_service.get_document_count()}")
        
        return new_docs_count
    
    def clear_loaded_registry(self) -> None:
        """Clear the loaded documents registry to force reload on next startup."""
        if self.loaded_docs_path.exists():
            self.loaded_docs_path.unlink()
            logger.info("Cleared loaded documents registry")


# Global instance
document_loader = DocumentLoaderService()
