"""Protocol-based provider interface for LLM implementations.

This module defines a Protocol (PEP 544) for LLM providers, enabling structural
subtyping rather than nominal subtyping. Providers don't need to explicitly inherit
from this Protocol - they just need to implement the required methods.
"""
from typing import Protocol, AsyncGenerator, Optional, Any, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers.
    
    This uses Python's Protocol for structural typing (duck typing with type hints).
    Any class that implements these methods will be considered a valid LLMProvider,
    even without explicit inheritance.
    
    The @runtime_checkable decorator allows isinstance() checks at runtime.
    """
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded and ready to use.
        
        Returns:
            bool: True if model is loaded, False otherwise.
        """
        ...
    
    def load_model(self) -> bool:
        """Load the LLM model.
        
        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        ...
    
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
        ...
    
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
        ...
    
    def get_langchain_llm(self) -> Any:
        """Get LangChain-compatible LLM wrapper for chain integration.
        
        Returns:
            Any: LangChain-compatible LLM instance.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        ...
