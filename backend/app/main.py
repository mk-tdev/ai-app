"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat
from app.routers import visualization
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.document_loader import document_loader
from app.models.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    
    # Initialize RAG service
    try:
        rag_service.initialize()
        logger.info("RAG service initialized successfully")
        
        # Auto-load documents from data folder
        new_docs = document_loader.load_documents()
        if new_docs > 0:
            logger.info(f"Loaded {new_docs} new documents into RAG")
        else:
            logger.info("No new documents to load")
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
    
    # Initialize Session service
    try:
        from app.services.session_service import session_service
        session_service.initialize()
        logger.info("Session service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Session service: {e}")
    
    # Load LLM model
    if llm_service.load_model():
        logger.info("LLM model loaded successfully")
    else:
        logger.warning("LLM model not loaded. Chat functionality will be limited.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="AI Chat API with llama.cpp, LangGraph, LangChain, and ChromaDB",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(chat.router)
    app.include_router(visualization.router)
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            model_loaded=llm_service.is_loaded,
        )
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "AI Chat API",
            "docs": "/docs",
            "health": "/health",
            "visualize_2d": "/api/visualize/2d",
            "visualize_3d": "/api/visualize/3d",
        }
    
    return app


# Create application instance
app = create_app()

