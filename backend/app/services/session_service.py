"""Optimized session service with async support and caching."""
import json
import logging
from datetime import datetime
from typing import Optional
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing chat sessions and conversation history."""
    
    _instance: Optional["SessionService"] = None
    _client: Optional[chromadb.Client] = None
    _collection: Optional[chromadb.Collection] = None
    _history_cache: dict[str, list[dict]] = {}  # In-memory cache for recent histories
    _cache_max_size: int = 100
    
    def __new__(cls) -> "SessionService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize ChromaDB for session storage."""
        settings = get_settings()
        
        try:
            # Initialize ChromaDB with persistence
            logger.info(f"Initializing Session Service with ChromaDB at {settings.chroma_persist_dir}")
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            
            # Get or create sessions collection
            self._collection = self._client.get_or_create_collection(
                name="chat_sessions",
                metadata={"description": "Conversation history storage"}
            )
            
            logger.info(f"Session Service initialized. Sessions collection has {self._collection.count()} entries.")
            
        except Exception as e:
            logger.error(f"Failed to initialize Session Service: {e}")
            raise
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata for the message
        """
        if not self._collection:
            raise RuntimeError("Session service not initialized. Call initialize() first.")
        
        # Create unique message ID
        timestamp = datetime.utcnow().isoformat()
        message_id = f"{session_id}_{timestamp}_{role}"
        
        # Prepare message data
        message_data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
            **(metadata or {})
        }
        
        # Store in ChromaDB
        self._collection.add(
            ids=[message_id],
            documents=[content],
            metadatas=[message_data]
        )
        
        # Invalidate cache for this session
        if session_id in self._history_cache:
            del self._history_cache[session_id]
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = 10  # Default to last 10 messages for better performance
    ) -> list[dict]:
        """
        Retrieve conversation history for a session with caching.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve (most recent)
        
        Returns:
            List of messages in chronological order
        """
        if not self._collection:
            raise RuntimeError("Session service not initialized. Call initialize() first.")
        
        # Check cache first
        cache_key = f"{session_id}_{limit}"
        if cache_key in self._history_cache:
            logger.debug(f"Cache hit for session {session_id}")
            return self._history_cache[cache_key]
        
        try:
            # Query messages for this session
            results = self._collection.get(
                where={"session_id": session_id}
            )
            
            if not results["ids"]:
                return []
            
            # Combine results into message list
            messages = []
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i]
                messages.append({
                    "role": metadata.get("role"),
                    "content": metadata.get("content"),
                    "timestamp": metadata.get("timestamp"),
                })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x["timestamp"])
            
            # Apply limit if specified (keep most recent)
            if limit and len(messages) > limit:
                messages = messages[-limit:]
            
            # Cache the result
            self._cache_session_history(cache_key, messages)
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def _cache_session_history(self, cache_key: str, messages: list[dict]) -> None:
        """Cache session history with LRU-like eviction."""
        # Simple LRU: if cache is full, remove oldest entry
        if len(self._history_cache) >= self._cache_max_size:
            # Remove first (oldest) item
            oldest_key = next(iter(self._history_cache))
            del self._history_cache[oldest_key]
        
        self._history_cache[cache_key] = messages
    
    def clear_cache(self, session_id: Optional[str] = None) -> None:
        """Clear cache for a specific session or all sessions."""
        if session_id:
            # Clear all cache entries for this session
            to_remove = [k for k in self._history_cache.keys() if k.startswith(session_id)]
            for key in to_remove:
                del self._history_cache[key]
        else:
            self._history_cache.clear()
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete all messages for a session.
        
        Args:
            session_id: Session identifier to delete
        
        Returns:
            True if successful, False otherwise
        """
        if not self._collection:
            raise RuntimeError("Session service not initialized. Call initialize() first.")
        
        try:
            # Get all message IDs for this session
            results = self._collection.get(
                where={"session_id": session_id}
            )
            
            if results["ids"]:
                self._collection.delete(ids=results["ids"])
                logger.info(f"Deleted session {session_id} with {len(results['ids'])} messages")
                
                # Clear cache
                self.clear_cache(session_id)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def get_session_count(self) -> int:
        """Get total number of unique sessions."""
        if not self._collection:
            return 0
        
        try:
            # Get all sessions and count unique session_ids
            results = self._collection.get()
            if not results["metadatas"]:
                return 0
            
            session_ids = set(m.get("session_id") for m in results["metadatas"])
            return len(session_ids)
            
        except Exception as e:
            logger.error(f"Failed to get session count: {e}")
            return 0


# Global instance
session_service = SessionService()
