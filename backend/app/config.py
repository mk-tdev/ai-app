"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    app_name: str = "AI Chat API"
    debug: bool = True
    verbose_llm: bool = False  # Control llama.cpp verbose output (ggml, metal, etc.)
    
    # Provider selection
    provider_type: str = "llamacpp"  # Options: llamacpp, ollama, huggingface
    
    # LLM settings (common across providers)
    temperature: float = 0.7
    max_tokens: int = 512
    
    # LlamaCPP-specific settings
    model_path: str = str(Path(__file__).parent.parent / "models" / "model.gguf")
    n_ctx: int = 4096  # Context window size
    n_gpu_layers: int = 0  # Set to -1 for full GPU offload, 0 for CPU only
    n_threads: int = 4
    
    # Ollama-specific settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"  # Default model name
    
    # HuggingFace-specific settings
    hf_model_name: str = "gpt2"  # HuggingFace model identifier
    hf_api_token: str | None = None  # Optional API token for private models
    
    # ChromaDB settings
    data_dir: str = str(Path(__file__).parent.parent / "data")
    chroma_persist_dir: str = str(Path(__file__).parent.parent / "data" / "chroma")
    collection_name: str = "documents"
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # OCR settings
    use_ocr: bool = True  # Enable/disable OCR for scanned PDFs
    extract_images: bool = True  # Enable/disable image extraction from PDFs
    ocr_language: str = "eng"  # Tesseract language code
    ocr_dpi: int = 300  # DPI for PDF to image conversion
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
