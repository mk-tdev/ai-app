"""Base provider interface for LLM implementations."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Any


class BaseLLMProvider(ABC):
    """Abstract base class defining the interface for all LLM providers."""
    
    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready to use.
        
        Returns:
            bool: True if model is loaded, False otherwise.
        """
        pass
    
    @abstractmethod
    def load_model(self) -> bool:
        """Load the LLM model.
        
        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The input prompt for the model.
            max_tokens: Maximum number of tokens to generate. If None, uses default.
            
        Returns:
            str: The generated response text.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM.
        
        Args:
            prompt: The input prompt for the model.
            max_tokens: Maximum number of tokens to generate. If None, uses default.
            
        Yields:
            str: Token chunks as they are generated.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        pass
    
    @abstractmethod
    def get_langchain_llm(self) -> Any:
        """Get LangChain-compatible LLM wrapper for chain integration.
        
        Returns:
            Any: LangChain-compatible LLM instance.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        pass
