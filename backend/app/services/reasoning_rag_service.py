"""Enhanced RAG Service with Multi-Hop Reasoning Capabilities."""
import logging
import json
import re
from typing import Optional, Literal
from pydantic import BaseModel

from app.services.rag_service import RAGService
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ReasoningStep(BaseModel):
    """A single step in multi-hop reasoning."""
    step_number: int
    question: str
    answer: str
    sources: list[dict]
    confidence: float = 0.0


class MultiHopResult(BaseModel):
    """Result from multi-hop reasoning."""
    query: str
    needs_multi_hop: bool
    reasoning_steps: list[ReasoningStep]
    final_answer: str
    all_sources: list[dict]
    strategy_used: str


class ReasoningRAGService(RAGService):
    """RAG service enhanced with multi-hop reasoning capabilities."""
    
    def intelligent_search(
        self,
        query: str,
        strategy: Literal["auto", "simple", "multi_hop"] = "auto",
        n_results: int = 3,
        max_hops: int = 3,
    ) -> dict:
        """
        Intelligent search with automatic strategy selection.
        
        Args:
            query: User's question
            strategy: Search strategy to use
            n_results: Number of results per retrieval
            max_hops: Maximum reasoning steps for multi-hop
            
        Returns:
            Dictionary with documents, strategy used, and reasoning chain
        """
        # Auto-select strategy if needed
        if strategy == "auto":
            strategy = self._select_strategy(query)
        
        logger.info(f"Using strategy: {strategy} for query: {query[:50]}...")
        
        if strategy == "multi_hop":
            result = self.multi_hop_reasoning(query, max_hops=max_hops, n_results=n_results)
            return {
                "documents": result.all_sources[:n_results],
                "strategy_used": "multi_hop",
                "reasoning_chain": [step.dict() for step in result.reasoning_steps],
                "needs_multi_hop": result.needs_multi_hop,
                "final_answer": result.final_answer,
            }
        else:
            # Simple vector search
            documents = self.search(query, n_results)
            return {
                "documents": documents,
                "strategy_used": "simple",
                "reasoning_chain": [],
                "needs_multi_hop": False,
            }
    
    def _select_strategy(self, query: str) -> str:
        """
        Determine if query needs multi-hop reasoning.
        
        Heuristics for multi-hop:
        - Contains multiple entities/concepts
        - Has comparative elements
        - Requires connecting information
        - Contains complex question words
        """
        query_lower = query.lower()
        
        # Keywords that suggest multi-hop reasoning
        multi_hop_indicators = [
            "compare", "difference between", "relationship between",
            "how does X affect Y", "what is the connection",
            "who is the", "which", "that", "whose",
            "before", "after", "because", "therefore",
            "as a result", "leads to", "causes",
        ]
        
        # Check for multiple question words or complex structure
        question_words = ["what", "who", "where", "when", "why", "how", "which"]
        question_count = sum(1 for word in question_words if word in query_lower)
        
        # Long queries often need multi-hop
        word_count = len(query.split())
        
        # Decision logic
        if any(indicator in query_lower for indicator in multi_hop_indicators):
            return "multi_hop"
        elif question_count >= 2:
            return "multi_hop"
        elif word_count > 20:
            return "multi_hop"
        else:
            return "simple"
    
    def multi_hop_reasoning(
        self,
        query: str,
        max_hops: int = 3,
        n_results: int = 3,
    ) -> MultiHopResult:
        """
        Perform multi-hop reasoning to answer complex queries.
        
        Process:
        1. Analyze if multi-hop is needed
        2. Decompose into reasoning steps
        3. Execute each step with retrieval
        4. Synthesize final answer
        
        Args:
            query: Complex question to answer
            max_hops: Maximum number of reasoning hops
            n_results: Documents to retrieve per hop
            
        Returns:
            MultiHopResult with reasoning chain and answer
        """
        logger.info(f"Starting multi-hop reasoning for: {query}")
        
        # Step 1: Analyze if multi-hop is needed and decompose
        decomposition = self._decompose_query(query)
        
        if not decomposition.get("needs_multi_hop", False):
            # Fall back to simple search
            logger.info("Query doesn't need multi-hop, using simple search")
            docs = self.search(query, n_results)
            return MultiHopResult(
                query=query,
                needs_multi_hop=False,
                reasoning_steps=[],
                final_answer=self._extract_answer_from_docs(query, docs),
                all_sources=docs,
                strategy_used="simple_fallback",
            )
        
        # Step 2: Execute multi-hop reasoning
        reasoning_steps = []
        all_documents = []
        context = {}  # Store intermediate answers
        
        steps = decomposition.get("reasoning_steps", [])[:max_hops]
        
        for i, step_info in enumerate(steps):
            step_num = i + 1
            step_question = step_info.get("question", "")
            
            # Replace placeholders with previous answers
            for placeholder, value in context.items():
                step_question = step_question.replace(f"{{{placeholder}}}", value)
            
            logger.info(f"Hop {step_num}/{len(steps)}: {step_question}")
            
            # Retrieve documents for this step
            step_docs = self.search(step_question, n_results=n_results)
            all_documents.extend(step_docs)
            
            # Extract answer for this hop
            step_answer = self._extract_answer_from_docs(step_question, step_docs)
            
            # Store answer for future steps
            placeholder = step_info.get("answer_placeholder", f"answer_{step_num}")
            context[placeholder] = step_answer
            
            reasoning_steps.append(ReasoningStep(
                step_number=step_num,
                question=step_question,
                answer=step_answer,
                sources=step_docs,
                confidence=self._calculate_confidence(step_docs),
            ))
            
            logger.info(f"  Answer: {step_answer[:100]}...")
        
        # Step 3: Synthesize final answer
        final_answer = self._synthesize_final_answer(query, reasoning_steps, context)
        
        # Deduplicate sources
        unique_sources = self._deduplicate_documents(all_documents)
        
        return MultiHopResult(
            query=query,
            needs_multi_hop=True,
            reasoning_steps=reasoning_steps,
            final_answer=final_answer,
            all_sources=unique_sources,
            strategy_used="multi_hop",
        )
    
    def _decompose_query(self, query: str) -> dict:
        """
        Decompose complex query into reasoning steps.
        
        Returns:
            {
                "needs_multi_hop": bool,
                "reasoning_steps": [
                    {"question": "...", "answer_placeholder": "X"},
                    {"question": "Use {X} to answer...", "answer_placeholder": "Y"}
                ],
                "analysis": "..."
            }
        """
        decomposition_prompt = f"""Analyze this question and determine if it requires multi-hop reasoning:

Question: "{query}"

Multi-hop reasoning is needed when:
- The question requires connecting multiple pieces of information
- You need to answer one question before you can answer another
- There are implicit steps or dependencies
- The question involves relationships between entities

Task:
1. Does this need multi-hop reasoning? (true/false)
2. If yes, break it into sequential sub-questions
3. Each step should have a placeholder for its answer (X, Y, Z, etc.)

Respond ONLY with valid JSON:
{{
    "needs_multi_hop": true or false,
    "reasoning_steps": [
        {{
            "step": 1,
            "question": "First question to answer",
            "answer_placeholder": "X",
            "reasoning": "Why this step is needed"
        }},
        {{
            "step": 2,
            "question": "Use {{X}} to find...",
            "answer_placeholder": "Y",
            "reasoning": "How this builds on previous step"
        }}
    ],
    "analysis": "Brief explanation of the reasoning approach"
}}

JSON Response:"""
        
        try:
            response = llm_service.generate(decomposition_prompt, max_tokens=500)
            
            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            decomposition = json.loads(response)
            logger.info(f"Query decomposition: {decomposition.get('analysis', 'N/A')}")
            
            return decomposition
            
        except Exception as e:
            logger.error(f"Failed to decompose query: {e}")
            logger.error(f"LLM Response: {response[:200] if 'response' in locals() else 'N/A'}")
            # Fallback to simple search
            return {"needs_multi_hop": False, "reasoning_steps": []}
    
    def _extract_answer_from_docs(self, question: str, documents: list[dict]) -> str:
        """
        Extract a concise answer to a specific question from documents.
        
        Args:
            question: The specific question to answer
            documents: Retrieved documents
            
        Returns:
            Concise answer string
        """
        if not documents:
            return "No relevant information found."
        
        # Combine document content
        context = "\n\n".join([
            f"[Source {i+1}]\n{doc['content']}"
            for i, doc in enumerate(documents[:3])  # Use top 3
        ])
        
        extraction_prompt = f"""Answer this specific question using ONLY the provided context.
Be concise and factual. If the context doesn't contain the answer, say "Information not found in documents."

Context:
{context}

Question: {question}

Concise Answer (1-2 sentences):"""
        
        try:
            answer = llm_service.generate(extraction_prompt, max_tokens=100)
            return answer.strip()
        except Exception as e:
            logger.error(f"Failed to extract answer: {e}")
            return "Error extracting answer."
    
    def _synthesize_final_answer(
        self,
        original_query: str,
        reasoning_steps: list[ReasoningStep],
        context: dict,
    ) -> str:
        """
        Synthesize final answer from all reasoning steps.
        
        Args:
            original_query: The original user question
            reasoning_steps: All reasoning steps executed
            context: Dictionary of intermediate answers
            
        Returns:
            Final comprehensive answer
        """
        # Build reasoning chain summary
        chain_summary = "\n".join([
            f"Step {step.step_number}: {step.question}\nAnswer: {step.answer}"
            for step in reasoning_steps
        ])
        
        synthesis_prompt = f"""Based on the following step-by-step reasoning, provide a comprehensive answer to the original question.

Original Question: {original_query}

Reasoning Chain:
{chain_summary}

Task: Synthesize a clear, comprehensive answer that:
1. Directly answers the original question
2. Incorporates insights from all reasoning steps
3. Is well-structured and easy to understand
4. Cites which steps support the conclusion

Final Answer:"""
        
        try:
            final_answer = llm_service.generate(synthesis_prompt, max_tokens=300)
            return final_answer.strip()
        except Exception as e:
            logger.error(f"Failed to synthesize final answer: {e}")
            # Fallback to combining individual answers
            return " ".join([step.answer for step in reasoning_steps])
    
    def _calculate_confidence(self, documents: list[dict]) -> float:
        """
        Calculate confidence score based on retrieval quality.
        
        Args:
            documents: Retrieved documents with distance scores
            
        Returns:
            Confidence score between 0 and 1
        """
        if not documents:
            return 0.0
        
        # Use distance scores (lower is better in cosine distance)
        distances = [doc.get('distance', 1.0) for doc in documents]
        
        if not distances:
            return 0.5
        
        # Convert distance to similarity (1 - distance for cosine)
        avg_similarity = 1.0 - sum(distances) / len(distances)
        
        # Normalize to 0-1 range
        confidence = max(0.0, min(1.0, avg_similarity))
        
        return round(confidence, 3)
    
    def _deduplicate_documents(self, documents: list[dict]) -> list[dict]:
        """
        Remove duplicate documents based on ID.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Deduplicated list
        """
        seen_ids = set()
        unique_docs = []
        
        for doc in documents:
            doc_id = doc.get('id')
            if doc_id and doc_id not in seen_ids:
                unique_docs.append(doc)
                seen_ids.add(doc_id)
            elif not doc_id:
                # Include documents without IDs
                unique_docs.append(doc)
        
        return unique_docs


# Global instance
reasoning_rag_service = ReasoningRAGService()
