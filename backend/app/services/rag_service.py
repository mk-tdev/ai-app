"""RAG Service using ChromaDB."""
import logging
import uuid
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations with ChromaDB."""
    
    _instance: Optional["RAGService"] = None
    _client: Optional[chromadb.Client] = None
    _collection: Optional[chromadb.Collection] = None
    _embedder: Optional[SentenceTransformer] = None
    
    def __new__(cls) -> "RAGService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize ChromaDB and embedding model."""
        settings = get_settings()
        
        try:
            # Initialize embedding model
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._embedder = SentenceTransformer(settings.embedding_model)
            
            # Initialize ChromaDB with persistence
            logger.info(f"Initializing ChromaDB at {settings.chroma_persist_dir}")
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=settings.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"ChromaDB initialized. Collection '{settings.collection_name}' has {self._collection.count()} documents.")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    def add_document(self, content: str, metadata: Optional[dict] = None) -> str:
        """Add a document to the collection."""
        if not self._collection or not self._embedder:
            raise RuntimeError("RAG service not initialized. Call initialize() first.")
        
        doc_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self._embedder.encode(content).tolist()
        
        # Add to collection
        self._collection.add(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )
        
        logger.info(f"Added document {doc_id}")
        return doc_id
    
    def search(self, query: str, n_results: int = 3) -> list[dict]:
        """Search for relevant documents."""
        if not self._collection or not self._embedder:
            raise RuntimeError("RAG service not initialized. Call initialize() first.")
        
        # Generate query embedding
        query_embedding = self._embedder.encode(query).tolist()
        
        # Search collection
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        
        # Format results
        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "id": results["ids"][0][i] if results["ids"] else None,
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        
        return documents
    
    def get_context(self, query: str, n_results: int = 3) -> str:
        """Get context string for RAG prompt."""
        documents = self.search(query, n_results)
        
        if not documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Document {i}]\n{doc['content']}")
        
        return "\n\n".join(context_parts)
    
    def get_document_count(self) -> int:
        """Get the number of documents in the collection."""
        if not self._collection:
            return 0
        return self._collection.count()


# Global instance
rag_service = RAGService()
