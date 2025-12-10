"""Visualization router for ChromaDB embeddings."""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.services.visualization_service import visualization_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visualize", tags=["visualization"])


@router.get("/2d", response_class=HTMLResponse)
async def visualize_2d(perplexity: int = 30):
    """
    Generate and return a 2D t-SNE visualization of ChromaDB embeddings.
    
    Returns an interactive Plotly HTML visualization.
    """
    doc_count = rag_service.get_document_count()
    if doc_count < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 2 documents for visualization. Current count: {doc_count}"
        )
    
    html = visualization_service.generate_2d_visualization(perplexity=perplexity)
    
    if html is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate visualization"
        )
    
    return HTMLResponse(content=html)


@router.get("/3d", response_class=HTMLResponse)
async def visualize_3d(perplexity: int = 30):
    """
    Generate and return a 3D t-SNE visualization of ChromaDB embeddings.
    
    Returns an interactive Plotly HTML visualization.
    """
    doc_count = rag_service.get_document_count()
    if doc_count < 4:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 4 documents for 3D visualization. Current count: {doc_count}"
        )
    
    html = visualization_service.generate_3d_visualization(perplexity=perplexity)
    
    if html is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate visualization"
        )
    
    return HTMLResponse(content=html)


@router.get("/stats")
async def get_stats():
    """Get statistics about the ChromaDB collection."""
    return {
        "document_count": rag_service.get_document_count(),
        "collection_name": rag_service._collection.name if rag_service._collection else None,
    }
