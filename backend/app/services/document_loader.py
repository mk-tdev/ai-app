"""Document loader service for auto-loading documents on startup."""
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Dict

from pypdf import PdfReader
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

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
        # OCR configuration
        self.use_ocr = getattr(self.settings, 'use_ocr', True)
        self.extract_images = getattr(self.settings, 'extract_images', True)
    
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
        """Extract comprehensive text content from PDF including tables and OCR."""
        content_parts = []
        
        try:
            # Try standard text extraction first
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            standard_text = "\n\n".join(text_parts)
            
            # Check if we need OCR
            if self._needs_ocr(file_path):
                logger.info(f"PDF appears to be scanned, using OCR: {file_path.name}")
                ocr_text = self._extract_text_with_ocr(file_path)
                if ocr_text:
                    content_parts.append(f"[TEXT CONTENT - OCR]\n{ocr_text}")
            else:
                if standard_text:
                    content_parts.append(f"[TEXT CONTENT]\n{standard_text}")
            
            # Extract tables with structure
            tables = self._extract_tables_from_pdf(file_path)
            if tables:
                content_parts.append(f"\n[TABLES]\n" + "\n\n".join(tables))
            
            # Extract and OCR images
            if self.extract_images:
                image_texts = self._extract_images_from_pdf(file_path)
                if image_texts:
                    content_parts.append(f"\n[IMAGES/SCREENSHOTS]\n" + "\n\n".join(image_texts))
            
            final_text = "\n\n".join(content_parts)
            
            if not final_text.strip():
                logger.warning(f"No text extracted from {file_path.name}")
            
            return final_text
        
        except Exception as e:
            logger.error(f"Failed to extract from PDF {file_path}: {e}")
            return ""
    
    def _needs_ocr(self, file_path: Path) -> bool:
        """Detect if PDF needs OCR (scanned/image-based)."""
        try:
            # Try extracting text normally
            reader = PdfReader(file_path)
            total_text = ""
            
            # Sample first 3 pages
            for page in reader.pages[:3]:
                total_text += page.extract_text() or ""
            
            # If very little text, likely scanned
            return len(total_text.strip()) < 50
        except Exception:
            return True  # If we can't read it, try OCR
    
    def _extract_text_with_ocr(self, file_path: Path) -> str:
        """Extract text from PDF using OCR for scanned documents."""
        if not self.use_ocr:
            return ""
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(file_path), dpi=300)
            
            ocr_text = []
            for i, image in enumerate(images, 1):
                logger.info(f"OCR processing page {i}/{len(images)} of {file_path.name}")
                
                # Perform OCR
                text = pytesseract.image_to_string(image, lang='eng')
                
                if text.strip():
                    ocr_text.append(f"[Page {i}]\n{text}")
            
            return "\n\n".join(ocr_text)
        
        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {e}")
            return ""
    
    def _extract_tables_from_pdf(self, file_path: Path) -> List[str]:
        """Extract tables from PDF and convert to markdown format."""
        tables_text = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if not table or not table[0]:
                            continue
                        
                        # Convert table to markdown
                        md_table = self._table_to_markdown(table)
                        if md_table:
                            tables_text.append(
                                f"[Page {page_num}, Table {table_idx + 1}]\n{md_table}\n"
                            )
        except Exception as e:
            logger.warning(f"Error extracting tables from {file_path}: {e}")
        
        return tables_text
    
    def _table_to_markdown(self, table: List[List]) -> str:
        """Convert table data to markdown format."""
        if not table:
            return ""
        
        # Filter out empty rows
        table = [row for row in table if any(cell for cell in row)]
        
        if not table:
            return ""
        
        # Build markdown table
        lines = []
        
        # Header
        header = table[0]
        lines.append("| " + " | ".join(str(cell or "").strip() for cell in header) + " |")
        lines.append("|" + "|".join("---" for _ in header) + "|")
        
        # Rows
        for row in table[1:]:
            lines.append("| " + " | ".join(str(cell or "").strip() for cell in row) + " |")
        
        return "\n".join(lines)
    
    def _extract_images_from_pdf(self, file_path: Path) -> List[str]:
        """Extract images from PDF and run OCR on them."""
        if not self.extract_images or not self.use_ocr:
            return []
        
        image_texts = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Get images from page
                    images = page.images
                    
                    for img_idx, img in enumerate(images):
                        try:
                            # Extract image coordinates and crop from page
                            x0, y0, x1, y1 = img['x0'], img['top'], img['x1'], img['bottom']
                            
                            # Get page as image and crop
                            page_img = page.to_image(resolution=300).original
                            cropped = page_img.crop((x0, y0, x1, y1))
                            
                            # Run OCR on cropped image
                            text = pytesseract.image_to_string(cropped)
                            
                            if text.strip():
                                image_texts.append(
                                    f"[Page {page_num}, Image {img_idx + 1}]\n{text.strip()}"
                                )
                        
                        except Exception as e:
                            logger.debug(f"Error processing image {img_idx} on page {page_num}: {e}")
        
        except Exception as e:
            logger.warning(f"Error extracting images from {file_path}: {e}")
        
        return image_texts
    
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
