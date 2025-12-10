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
    
    # LLM settings
    model_path: str = str(Path(__file__).parent.parent / "models" / "model.gguf")
    n_ctx: int = 4096  # Context window size
    n_gpu_layers: int = 0  # Set to -1 for full GPU offload, 0 for CPU only
    n_threads: int = 4
    temperature: float = 0.7
    max_tokens: int = 512
    
    # ChromaDB settings
    data_dir: str = str(Path(__file__).parent.parent / "data")
    chroma_persist_dir: str = str(Path(__file__).parent.parent / "data" / "chroma")
    collection_name: str = "documents"
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
