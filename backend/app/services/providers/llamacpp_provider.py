"""LlamaCPP provider implementation."""
import logging
from pathlib import Path
from typing import AsyncGenerator, Optional

from llama_cpp import Llama
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler

from app.config import get_settings

logger = logging.getLogger(__name__)


class LlamaCppProvider:
    """LLM provider using llama-cpp-python for GGUF models."""
    
    def __init__(self):
        """Initialize the LlamaCPP provider."""
        self._llm: Optional[Llama] = None
        self._langchain_llm: Optional[LlamaCpp] = None
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._llm is not None
    
    def load_model(self) -> bool:
        """Load the LLM model from GGUF file."""
        settings = get_settings()
        model_path = Path(settings.model_path)
        
        if not model_path.exists():
            logger.warning(f"Model not found at {model_path}. Please download a GGUF model.")
            return False
        
        try:
            logger.info(f"Loading LlamaCPP model from {model_path}...")
            
            # Load native llama-cpp model for direct use
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=settings.n_ctx,
                n_gpu_layers=settings.n_gpu_layers,
                n_threads=settings.n_threads,
                verbose=settings.verbose_llm,
            )
            
            # Load LangChain wrapper for integration
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            self._langchain_llm = LlamaCpp(
                model_path=str(model_path),
                n_ctx=settings.n_ctx,
                n_gpu_layers=settings.n_gpu_layers,
                n_threads=settings.n_threads,
                callback_manager=callback_manager,
                verbose=settings.verbose_llm,
                streaming=True,
            )
            
            logger.info("LlamaCPP model loaded successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LlamaCPP model: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate a response from the LLM."""
        if not self._llm:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        settings = get_settings()
        max_tokens = max_tokens or settings.max_tokens
        
        response = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=settings.temperature,
            stop=["User:", "\n\nUser:", "Human:", "\n\nHuman:"],
        )
        
        return response["choices"][0]["text"].strip()
    
    async def generate_stream(
        self, prompt: str, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM."""
        if not self._llm:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        settings = get_settings()
        max_tokens = max_tokens or settings.max_tokens
        
        stream = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=settings.temperature,
            stop=["User:", "\n\nUser:", "Human:", "\n\nHuman:"],
            stream=True,
        )
        
        for output in stream:
            token = output["choices"][0]["text"]
            if token:
                yield token
    
    def get_langchain_llm(self) -> LlamaCpp:
        """Get LangChain LLM wrapper for chain integration."""
        if not self._langchain_llm:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        return self._langchain_llm
