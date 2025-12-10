"""Visualization service for ChromaDB embeddings."""
import logging
from typing import Optional

import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import plotly.express as px

from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class VisualizationService:
    """Service for visualizing ChromaDB embeddings."""
    
    def get_embeddings_data(self) -> tuple[Optional[np.ndarray], Optional[list[dict]], Optional[list[str]]]:
        """Get embeddings, metadata, and documents from ChromaDB."""
        if not rag_service._collection:
            logger.warning("ChromaDB collection not initialized")
            return None, None, None
        
        try:
            # Get all items from collection
            result = rag_service._collection.get(
                include=["embeddings", "metadatas", "documents"]
            )
            
            # Check if embeddings exist (handle None and empty list)
            embeddings_list = result.get("embeddings")
            if embeddings_list is None or len(embeddings_list) == 0:
                logger.warning("No embeddings found in collection")
                return None, None, None
            
            embeddings = np.array(embeddings_list)
            metadatas = result.get("metadatas") or [{}] * len(embeddings)
            documents = result.get("documents") or [""] * len(embeddings)
            
            logger.info(f"Retrieved {len(embeddings)} embeddings for visualization")
            return embeddings, metadatas, documents
            
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            return None, None, None
    
    def generate_2d_visualization(self, perplexity: int = 30) -> Optional[str]:
        """Generate 2D t-SNE visualization as HTML."""
        embeddings, metadatas, documents = self.get_embeddings_data()
        
        if embeddings is None or len(embeddings) < 2:
            return None
        
        # Adjust perplexity for small datasets
        n_samples = len(embeddings)
        perplexity = min(perplexity, max(5, n_samples - 1))
        
        try:
            # Perform t-SNE
            tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
            embeddings_2d = tsne.fit_transform(embeddings)
            
            # Extract source labels for coloring
            sources = [m.get("source", "unknown") for m in metadatas]
            
            # Create hover text (truncated documents)
            hover_texts = [
                f"Source: {sources[i]}<br>Content: {documents[i][:100]}..."
                for i in range(len(documents))
            ]
            
            # Create plotly figure
            fig = go.Figure()
            
            # Get unique sources for coloring
            unique_sources = list(set(sources))
            colors = px.colors.qualitative.Set1[:len(unique_sources)]
            color_map = {src: colors[i % len(colors)] for i, src in enumerate(unique_sources)}
            
            for source in unique_sources:
                mask = [s == source for s in sources]
                indices = [i for i, m in enumerate(mask) if m]
                
                fig.add_trace(go.Scatter(
                    x=embeddings_2d[indices, 0],
                    y=embeddings_2d[indices, 1],
                    mode='markers',
                    name=source[:30],
                    marker=dict(size=8, color=color_map[source]),
                    hovertext=[hover_texts[i] for i in indices],
                    hoverinfo='text',
                ))
            
            fig.update_layout(
                title="ChromaDB Embeddings - 2D t-SNE Visualization",
                xaxis_title="t-SNE Dimension 1",
                yaxis_title="t-SNE Dimension 2",
                template="plotly_dark",
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
                width=900,
                height=700,
            )
            
            return fig.to_html(full_html=True, include_plotlyjs='cdn')
            
        except Exception as e:
            logger.error(f"Failed to generate 2D visualization: {e}")
            return None
    
    def generate_3d_visualization(self, perplexity: int = 30) -> Optional[str]:
        """Generate 3D t-SNE visualization as HTML."""
        embeddings, metadatas, documents = self.get_embeddings_data()
        
        if embeddings is None or len(embeddings) < 4:
            return None
        
        # Adjust perplexity for small datasets
        n_samples = len(embeddings)
        perplexity = min(perplexity, max(5, n_samples - 1))
        
        try:
            # Perform t-SNE
            tsne = TSNE(n_components=3, perplexity=perplexity, random_state=42)
            embeddings_3d = tsne.fit_transform(embeddings)
            
            # Extract source labels for coloring
            sources = [m.get("source", "unknown") for m in metadatas]
            
            # Create hover text (truncated documents)
            hover_texts = [
                f"Source: {sources[i]}<br>Content: {documents[i][:100]}..."
                for i in range(len(documents))
            ]
            
            # Create plotly figure
            fig = go.Figure()
            
            # Get unique sources for coloring
            unique_sources = list(set(sources))
            colors = px.colors.qualitative.Set1[:len(unique_sources)]
            color_map = {src: colors[i % len(colors)] for i, src in enumerate(unique_sources)}
            
            for source in unique_sources:
                mask = [s == source for s in sources]
                indices = [i for i, m in enumerate(mask) if m]
                
                fig.add_trace(go.Scatter3d(
                    x=embeddings_3d[indices, 0],
                    y=embeddings_3d[indices, 1],
                    z=embeddings_3d[indices, 2],
                    mode='markers',
                    name=source[:30],
                    marker=dict(size=5, color=color_map[source]),
                    hovertext=[hover_texts[i] for i in indices],
                    hoverinfo='text',
                ))
            
            fig.update_layout(
                title="ChromaDB Embeddings - 3D t-SNE Visualization",
                scene=dict(
                    xaxis_title="t-SNE Dimension 1",
                    yaxis_title="t-SNE Dimension 2",
                    zaxis_title="t-SNE Dimension 3",
                ),
                template="plotly_dark",
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
                width=900,
                height=700,
            )
            
            return fig.to_html(full_html=True, include_plotlyjs='cdn')
            
        except Exception as e:
            logger.error(f"Failed to generate 3D visualization: {e}")
            return None


# Global instance
visualization_service = VisualizationService()
