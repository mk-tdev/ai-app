"""LangGraph workflow service for chat orchestration."""
import logging
import uuid
from typing import Annotated, AsyncGenerator, TypedDict
from operator import add

from langgraph.graph import StateGraph, END

from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.config import get_settings

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """State for the chat workflow."""
    conversation_id: str
    user_message: str
    context: str
    response: str
    use_rag: bool
    use_reasoning: bool  # Enable multi-hop reasoning
    max_hops: int  # Maximum reasoning steps
    sources: list[str]
    reasoning_chain: list[dict]  # Multi-hop reasoning steps
    conversation_history: list[dict]  # Chat history for context


def create_system_prompt(context: str = "", conversation_history: list[dict] = None) -> str:
    """Create the system prompt for the LLM."""
    base_prompt = """You are a helpful AI assistant. You provide clear, accurate, and helpful responses.
Be concise but thorough. If you don't know something, say so honestly."""
    
    # Add conversation history if available
    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        history_parts = ["Previous conversation:"]
        # Use only last 6 messages (3 exchanges) for context to reduce overhead
        for msg in conversation_history[-6:]:
            role = msg.get("role", "").capitalize()
            content = msg.get("content", "")
            history_parts.append(f"{role}: {content}")
        history_context = "\n".join(history_parts)
    
    if context:
        prompt = f"""{base_prompt}

{history_context}

Use the following context to help answer the user's question:

{context}

If the context doesn't contain relevant information, you can still answer based on your knowledge, but mention that the specific documents didn't contain relevant information."""
    elif history_context:
        prompt = f"""{base_prompt}

{history_context}"""
    else:
        prompt = base_prompt
    
    return prompt


def retrieve_context(state: ChatState) -> ChatState:
    """Retrieve relevant context from ChromaDB if RAG is enabled."""
    if not state["use_rag"]:
        return {**state, "context": "", "sources": [], "reasoning_chain": []}
    
    try:
        # Use multi-hop reasoning if enabled
        if state.get("use_reasoning", False):
            from app.services.reasoning_rag_service import reasoning_rag_service
            
            logger.info("Using multi-hop reasoning for retrieval")
            result = reasoning_rag_service.intelligent_search(
                query=state["user_message"],
                strategy="auto",
                n_results=3,
                max_hops=state.get("max_hops", 3),
            )
            
            documents = result.get("documents", [])
            reasoning_chain = result.get("reasoning_chain", [])
            
            if documents:
                context_parts = []
                sources = []
                for i, doc in enumerate(documents, 1):
                    context_parts.append(f"[Document {i}]\n{doc['content']}")
                    sources.append(doc.get("id", f"doc_{i}"))
                
                # Add reasoning chain to context if available
                if reasoning_chain:
                    reasoning_summary = "\n\nReasoning Chain:\n" + "\n".join([
                        f"Step {step['step_number']}: {step['question']} -> {step['answer']}"
                        for step in reasoning_chain
                    ])
                    context_parts.append(reasoning_summary)
                
                return {
                    **state,
                    "context": "\n\n".join(context_parts),
                    "sources": sources,
                    "reasoning_chain": reasoning_chain,
                }
        else:
            # Simple vector search
            documents = rag_service.search(state["user_message"], n_results=3)
            
            if documents:
                context_parts = []
                sources = []
                for i, doc in enumerate(documents, 1):
                    context_parts.append(f"[Document {i}]\n{doc['content']}")
                    sources.append(doc.get("id", f"doc_{i}"))
                
                return {
                    **state,
                    "context": "\n\n".join(context_parts),
                    "sources": sources,
                    "reasoning_chain": [],
                }
    except Exception as e:
        logger.warning(f"Failed to retrieve context: {e}")
    
    return {**state, "context": "", "sources": [], "reasoning_chain": []}


def generate_response(state: ChatState) -> ChatState:
    """Generate response using the LLM."""
    system_prompt = create_system_prompt(
        state.get("context", ""),
        state.get("conversation_history", [])
    )
    
    prompt = f"""{system_prompt}

User: {state["user_message"]}
Assistant:"""
    
    try:
        response = llm_service.generate(prompt)
        return {**state, "response": response}
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        return {**state, "response": "I apologize, but I encountered an error generating a response."}


def create_chat_graph() -> StateGraph:
    """Create the LangGraph workflow for chat."""
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)
    
    # Define edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()


class GraphService:
    """Service for managing LangGraph chat workflow."""
    
    _graph = None
    
    @classmethod
    def get_graph(cls):
        """Get or create the chat graph."""
        if cls._graph is None:
            cls._graph = create_chat_graph()
        return cls._graph
    
    @classmethod
    def chat(
        cls,
        message: str,
        conversation_id: str = None,
        use_rag: bool = False,
        use_reasoning: bool = False,
        max_hops: int = 3,
    ) -> dict:
        """Run a chat through the graph."""
        from app.services.session_service import session_service
        
        graph = cls.get_graph()
        
        conv_id = conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = []
        if conversation_id:
            conversation_history = session_service.get_conversation_history(conversation_id, limit=6)
        
        initial_state: ChatState = {
            "conversation_id": conv_id,
            "user_message": message,
            "context": "",
            "response": "",
            "use_rag": use_rag,
            "use_reasoning": use_reasoning,
            "max_hops": max_hops,
            "sources": [],
            "reasoning_chain": [],
            "conversation_history": conversation_history,
        }
        
        result = graph.invoke(initial_state)
        
        # Save messages to session
        session_service.add_message(conv_id, "user", message)
        session_service.add_message(conv_id, "assistant", result["response"])
        
        return {
            "message": result["response"],
            "conversation_id": result["conversation_id"],
            "sources": result.get("sources", []) if use_rag else None,
            "reasoning_chain": result.get("reasoning_chain", []) if use_reasoning else None,
            "strategy_used": "multi_hop" if use_reasoning and result.get("reasoning_chain") else "simple",
        }
    
    @classmethod
    async def chat_stream(
        cls,
        message: str,
        conversation_id: str = None,
        use_rag: bool = False,
        use_reasoning: bool = False,
        max_hops: int = 3,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response."""
        from app.services.session_service import session_service
        from app.services.reasoning_rag_service import reasoning_rag_service
        
        conv_id = conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = []
        if conversation_id:
            conversation_history = session_service.get_conversation_history(conversation_id, limit=6)
        
        # Get context if RAG is enabled
        context = ""
        reasoning_context = ""
        if use_rag:
            try:
                if use_reasoning:
                    # Use intelligent search with multi-hop reasoning
                    result = reasoning_rag_service.intelligent_search(
                        query=message,
                        max_hops=max_hops,
                        force_strategy="multi_hop" if use_reasoning else None
                    )
                    context = result.get("context", "")
                    
                    # Add reasoning chain to context if available
                    if result.get("reasoning_chain"):
                        reasoning_steps = []
                        for step in result["reasoning_chain"]:
                            reasoning_steps.append(
                                f"Step {step['step_number']}: {step['question']}\n"
                                f"Finding: {step['answer'][:200]}..."
                            )
                        reasoning_context = "\n\n[Reasoning Process]\n" + "\n\n".join(reasoning_steps)
                else:
                    # Use simple RAG
                    context = rag_service.get_context(message, n_results=3)
            except Exception as e:
                logger.warning(f"Failed to get RAG context: {e}")
        
        # Create prompt with conversation history and reasoning
        full_context = context + reasoning_context if reasoning_context else context
        system_prompt = create_system_prompt(full_context, conversation_history)
        prompt = f"""{system_prompt}

User: {message}
Assistant:"""
        
        # Save user message
        session_service.add_message(conv_id, "user", message)
        
        # Stream response and collect it
        full_response = ""
        try:
            async for token in llm_service.generate_stream(prompt):
                full_response += token
                yield token
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_msg = "I apologize, but I encountered an error."
            full_response = error_msg
            yield error_msg
        
        # Save assistant response
        session_service.add_message(conv_id, "assistant", full_response)


# Global instance
graph_service = GraphService()
