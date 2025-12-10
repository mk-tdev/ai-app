"""LLM Service with multi-provider support."""
import logging
from typing import AsyncGenerator, Optional, Any

from app.config import get_settings
from app.services.providers import create_provider, BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM operations with pluggable providers."""
    
    _instance: Optional["LLMService"] = None
    _provider: Optional[BaseLLMProvider] = None
    
    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._provider is not None and self._provider.is_loaded
    
    def load_model(self) -> bool:
        """Load the LLM model using the configured provider."""
        settings = get_settings()
        
        try:
            # Create provider based on configuration
            logger.info(f"Initializing {settings.provider_type} provider...")
            self._provider = create_provider()
            
            # Load the model
            success = self._provider.load_model()
            
            if success:
                logger.info(f"Provider {settings.provider_type} initialized successfully!")
            else:
                logger.error(f"Failed to initialize provider {settings.provider_type}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to create provider: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The input prompt for the model.
            max_tokens: Maximum number of tokens to generate.
            
        Returns:
            str: The generated response.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        if not self._provider:
            raise RuntimeError("Provider not initialized. Call load_model() first.")
        
        return self._provider.generate(prompt, max_tokens)
    
    async def generate_stream(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM.
        
        Args:
            prompt: The input prompt for the model.
            max_tokens: Maximum number of tokens to generate.
            
        Yields:
            str: Token chunks as they are generated.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        if not self._provider:
            raise RuntimeError("Provider not initialized. Call load_model() first.")
        
        async for token in self._provider.generate_stream(prompt, max_tokens):
            yield token
    
    def get_langchain_llm(self) -> Any:
        """Get LangChain LLM wrapper for chain integration.
        
        Returns:
            Any: LangChain-compatible LLM instance.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        if not self._provider:
            raise RuntimeError("Provider not initialized. Call load_model() first.")
        
        return self._provider.get_langchain_llm()


# Global instance
llm_service = LLMService()
