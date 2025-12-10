"""Provider factory and exports."""
import logging
from typing import Literal

from app.config import get_settings
from app.services.providers.base_provider import LLMProvider
from app.services.providers.llamacpp_provider import LlamaCppProvider
from app.services.providers.ollama_provider import OllamaProvider
from app.services.providers.huggingface_provider import HuggingFaceProvider

logger = logging.getLogger(__name__)

# Type for provider selection
ProviderType = Literal["llamacpp", "ollama", "huggingface"]


def create_provider(provider_type: str | None = None) -> LLMProvider:
    """Factory function to create the appropriate LLM provider.
    
    Args:
        provider_type: Type of provider to create. If None, uses config setting.
                      Options: "llamacpp", "ollama", "huggingface"
    
    Returns:
        LLMProvider: Instance of the requested provider (satisfies Protocol).
        
    Raises:
        ValueError: If provider_type is not recognized.
    """
    settings = get_settings()
    provider_type = provider_type or settings.provider_type
    provider_type = provider_type.lower()
    
    logger.info(f"Creating LLM provider: {provider_type}")
    
    if provider_type == "llamacpp":
        return LlamaCppProvider()
    elif provider_type == "ollama":
        return OllamaProvider()
    elif provider_type == "huggingface":
        return HuggingFaceProvider()
    else:
        raise ValueError(
            f"Unknown provider type: {provider_type}. "
            f"Valid options are: llamacpp, ollama, huggingface"
        )


__all__ = [
    "LLMProvider",
    "LlamaCppProvider",
    "OllamaProvider",
    "HuggingFaceProvider",
    "create_provider",
    "ProviderType",
]
