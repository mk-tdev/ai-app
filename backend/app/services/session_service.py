"""Session service for managing conversation history in ChromaDB."""
import json
import logging
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing chat sessions and conversation history."""
    
    _instance: Optional["SessionService"] = None
    _client: Optional[chromadb.Client] = None
    _collection: Optional[chromadb.Collection] = None
    
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
        # We use the content as the document and store metadata as JSON
        self._collection.add(
            ids=[message_id],
            documents=[content],
            metadatas=[message_data]
        )
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve (most recent)
        
        Returns:
            List of messages in chronological order
        """
        if not self._collection:
            raise RuntimeError("Session service not initialized. Call initialize() first.")
        
        try:
            # Query all messages for this session
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
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
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
