"""Ollama provider implementation."""
import logging
from typing import AsyncGenerator, Optional

from langchain_ollama import OllamaLLM

from app.config import get_settings
from app.services.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """LLM provider using Ollama for locally running models."""
    
    def __init__(self):
        """Initialize the Ollama provider."""
        self._llm: Optional[OllamaLLM] = None
        self._model_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded
    
    def load_model(self) -> bool:
        """Initialize connection to Ollama API."""
        settings = get_settings()
        
        try:
            logger.info(f"Connecting to Ollama at {settings.ollama_base_url}...")
            logger.info(f"Using model: {settings.ollama_model}")
            
            # Create Ollama LLM instance
            self._llm = OllamaLLM(
                model=settings.ollama_model,
                base_url=settings.ollama_base_url,
                temperature=settings.temperature,
            )
            
            # Test connection with a simple prompt
            try:
                _ = self._llm.invoke("test")
                self._model_loaded = True
                logger.info("Ollama model loaded successfully!")
                return True
            except Exception as test_error:
                logger.error(f"Ollama connection test failed: {test_error}")
                logger.error("Make sure Ollama is running and the model is available")
                return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response from the LLM."""
        if not self._llm or not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            response = self._llm.invoke(prompt)
            return response.strip() if isinstance(response, str) else str(response).strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Generation failed: {e}")
    
    async def generate_stream(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        if not self._llm or not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            # Ollama supports streaming through LangChain
            async for chunk in self._llm.astream(prompt):
                if chunk:
                    yield str(chunk)
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise RuntimeError(f"Streaming failed: {e}")
    
    def get_langchain_llm(self) -> OllamaLLM:
        """Get LangChain LLM wrapper for chain integration."""
        if not self._llm or not self._model_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        return self._llm
