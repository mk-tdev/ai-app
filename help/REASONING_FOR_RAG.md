# Reasoning Techniques for RAG Systems

## Overview

Adding **reasoning** to your RAG pipeline can dramatically improve answer quality by:
1. Better understanding user intent
2. Decomposing complex queries
3. Improving retrieval relevance
4. Synthesizing better answers from multiple sources

## Key Reasoning Techniques for RAG

### 1. **Query Understanding & Decomposition** 🔥 High Impact

Break complex queries into sub-queries for better retrieval.

#### Example:
```
User Query: "Compare the deployment process for Docker vs Kubernetes and explain which is better for small teams"

Reasoning Step:
1. What is Docker deployment?
2. What is Kubernetes deployment?
3. What are the differences?
4. What factors matter for small teams?
```

#### Implementation:

```python
def reason_about_query(self, query: str) -> dict:
    """Use LLM to reason about the query and decompose it."""
    reasoning_prompt = f"""Analyze this user question and break it down:

Question: {query}

Tasks:
1. What is the user really asking? (intent)
2. What sub-questions need to be answered?
3. What information would be most helpful?
4. Are there any implicit assumptions?

Respond in JSON format:
{{
    "intent": "...",
    "sub_queries": ["...", "..."],
    "key_concepts": ["...", "..."],
    "context_needed": "..."
}}"""
    
    response = llm_service.generate(reasoning_prompt)
    return json.loads(response)
```

### 2. **HyDE (Hypothetical Document Embeddings)** 🔥 Very High Impact

Generate a hypothetical answer first, then search for documents similar to that answer.

#### Why it works:
- Queries and documents often have different linguistic patterns
- A hypothetical answer is more similar to actual documents
- Bridges the "semantic gap" between questions and answers

#### Implementation:

```python
class ReasoningRAGService(RAGService):
    """RAG service enhanced with reasoning capabilities."""
    
    def hyde_search(self, query: str, n_results: int = 3) -> list[dict]:
        """
        Use HyDE (Hypothetical Document Embeddings) for better retrieval.
        
        Steps:
        1. Generate a hypothetical answer to the query
        2. Embed the hypothetical answer
        3. Search for documents similar to the answer
        """
        # Generate hypothetical answer
        hyde_prompt = f"""Given this question: "{query}"

Write a detailed, factual answer as if you had access to the relevant documentation. 
Be specific and technical. Don't say "I don't know" - write what the answer WOULD look like.

Hypothetical Answer:"""
        
        hypothetical_answer = llm_service.generate(hyde_prompt, max_tokens=200)
        
        logger.info(f"HyDE hypothetical answer: {hypothetical_answer[:100]}...")
        
        # Search using the hypothetical answer instead of the query
        hypothetical_embedding = self._embedder.encode(hypothetical_answer).tolist()
        
        results = self._collection.query(
            query_embeddings=[hypothetical_embedding],
            n_results=n_results,
        )
        
        return self._format_results(results)
```

**Expected Improvement**: 20-50% better retrieval in many cases!

### 3. **Chain-of-Thought Retrieval** 🔥 High Impact

Use reasoning to iteratively refine searches.

```python
def chain_of_thought_retrieval(self, query: str, max_iterations: int = 3) -> list[dict]:
    """
    Iteratively reason about what to retrieve next.
    
    Flow:
    1. Initial retrieval
    2. Reason about what's missing
    3. Retrieve additional context
    4. Repeat until satisfied
    """
    all_documents = []
    current_query = query
    
    for iteration in range(max_iterations):
        # Retrieve documents
        docs = self.search(current_query, n_results=3)
        all_documents.extend(docs)
        
        # Reason about gaps
        reasoning_prompt = f"""Question: {query}

Retrieved so far:
{self._format_documents(all_documents)}

Analysis:
1. Is this enough to answer the question? (yes/no)
2. What information is still missing?
3. What should we search for next?

Respond in JSON:
{{
    "sufficient": true/false,
    "missing_info": "...",
    "next_query": "..."
}}"""
        
        reasoning = json.loads(llm_service.generate(reasoning_prompt))
        
        if reasoning.get("sufficient", False):
            break
            
        current_query = reasoning.get("next_query", query)
        logger.info(f"Iteration {iteration + 1}: Next query = {current_query}")
    
    # Deduplicate and return
    return self._deduplicate_documents(all_documents)[:5]
```

### 4. **Self-Reflection & Re-ranking** 🔥 Medium-High Impact

After retrieval, reason about which documents are actually relevant.

```python
def reason_and_rerank(self, query: str, documents: list[dict]) -> list[dict]:
    """Use LLM reasoning to re-rank retrieved documents."""
    docs_text = "\n\n".join([
        f"[Doc {i+1}] (similarity: {doc['distance']:.3f})\n{doc['content'][:200]}..."
        for i, doc in enumerate(documents)
    ])
    
    rerank_prompt = f"""Question: {query}

Retrieved Documents:
{docs_text}

For each document, reason about:
1. How relevant is it to the question?
2. What specific information does it provide?
3. Rate relevance: 0-10

Respond in JSON:
[
    {{"doc_id": 1, "relevance": 8, "reason": "..."}},
    {{"doc_id": 2, "relevance": 3, "reason": "..."}}
]"""
    
    rankings = json.loads(llm_service.generate(rerank_prompt))
    
    # Re-order documents by LLM relevance score
    doc_scores = {r['doc_id']-1: r['relevance'] for r in rankings}
    documents.sort(key=lambda doc: doc_scores.get(documents.index(doc), 0), reverse=True)
    
    return documents
```

### 5. **Query Expansion via Reasoning** 🔥 Medium Impact

Generate better query variations through reasoning.

```python
def reason_query_expansion(self, query: str) -> list[str]:
    """Generate query variations through reasoning."""
    expansion_prompt = f"""Original Query: "{query}"

Think step-by-step about this query:

1. What are different ways to phrase this question?
2. What related questions might find the same information?
3. What synonyms or alternative terms could be used?
4. What specific vs. general versions exist?

Generate 3-5 alternative queries that might retrieve the same information:
- Use different terminology
- Vary specificity
- Include related concepts

Return as JSON array:
["query1", "query2", "query3"]"""
    
    variations = json.loads(llm_service.generate(expansion_prompt))
    return [query] + variations  # Include original
```

### 6. **Step-Back Prompting** 🔥 High Impact

Ask a more general question first to get better context.

```python
def step_back_retrieval(self, query: str, n_results: int = 3) -> list[dict]:
    """
    Retrieve using both specific and general queries.
    
    Example:
    Specific: "What are the GPU requirements for running Llama-3-70B?"
    Step-back: "What are the hardware requirements for running large language models?"
    """
    # Generate step-back question
    step_back_prompt = f"""Given this specific question:
"{query}"

Generate a more general, higher-level question that would help answer this.
The general question should capture the broader concept.

General question:"""
    
    general_query = llm_service.generate(step_back_prompt, max_tokens=50).strip()
    logger.info(f"Step-back query: {general_query}")
    
    # Retrieve for both queries
    specific_docs = self.search(query, n_results=n_results)
    general_docs = self.search(general_query, n_results=n_results)
    
    # Combine and deduplicate
    all_docs = specific_docs + general_docs
    return self._deduplicate_documents(all_docs)[:n_results]
```

### 7. **Multi-Hop Reasoning** 🔥 Very High Impact

Follow chains of information across multiple documents.

```python
def multi_hop_reasoning(self, query: str) -> dict:
    """
    Answer questions that require connecting multiple pieces of info.
    
    Example: "Who is the CEO of the company that acquired Instagram?"
    - Hop 1: Which company acquired Instagram? → Facebook
    - Hop 2: Who is the CEO of Facebook? → Mark Zuckerberg
    """
    reasoning_prompt = f"""Question: {query}

Does this question require multiple steps to answer? 
Break it down into sequential sub-questions.

Respond in JSON:
{{
    "needs_multi_hop": true/false,
    "reasoning_steps": [
        {{"step": 1, "question": "...", "answer_placeholder": "X"}},
        {{"step": 2, "question": "...", "depends_on": "X"}}
    ]
}}"""
    
    plan = json.loads(llm_service.generate(reasoning_prompt))
    
    if not plan.get("needs_multi_hop", False):
        # Simple single retrieval
        return {"answer": self.search(query), "reasoning_chain": []}
    
    # Execute multi-hop retrieval
    reasoning_chain = []
    context = {}
    
    for step in plan["reasoning_steps"]:
        step_query = step["question"]
        
        # Search for this step
        docs = self.search(step_query, n_results=2)
        
        # Extract answer for this hop (simplified)
        answer = self._extract_answer(step_query, docs)
        context[step.get("answer_placeholder", f"step_{step['step']}")] = answer
        
        reasoning_chain.append({
            "step": step["step"],
            "query": step_query,
            "answer": answer,
            "sources": docs
        })
    
    return {
        "reasoning_chain": reasoning_chain,
        "final_context": context,
        "all_documents": [doc for step in reasoning_chain for doc in step["sources"]]
    }
```

### 8. **Metacognitive Reasoning** 🔥 Medium Impact

Let the system reason about its own retrieval strategy.

```python
def metacognitive_search(self, query: str) -> dict:
    """Reason about the best search strategy for this query."""
    strategy_prompt = f"""Question: "{query}"

Analyze this question and determine the best retrieval strategy:

1. Query Type:
   - Factual lookup (who/what/when/where)
   - Procedural (how-to)
   - Comparative (compare X and Y)
   - Exploratory (explain concept)
   - Troubleshooting (why is X not working)

2. Best Strategy:
   - Simple vector search
   - HyDE (hypothetical document)
   - Multi-query expansion
   - Step-back (general then specific)
   - Chain-of-thought retrieval

3. Recommended n_results: (1-10)

Respond in JSON:
{{
    "query_type": "...",
    "recommended_strategy": "...",
    "reasoning": "...",
    "n_results": 5
}}"""
    
    meta_reasoning = json.loads(llm_service.generate(strategy_prompt))
    
    # Route to appropriate strategy
    strategy = meta_reasoning.get("recommended_strategy", "simple")
    
    if "hyde" in strategy.lower():
        return self.hyde_search(query)
    elif "step-back" in strategy.lower():
        return self.step_back_retrieval(query)
    elif "chain" in strategy.lower():
        return self.chain_of_thought_retrieval(query)
    else:
        return self.search(query)
```

## Implementation Roadmap

### Phase 1: Foundation (2-4 hours)
1. ✅ Implement **HyDE** - Biggest single improvement
2. ✅ Add **Query Understanding** - Helps with complex queries
3. ✅ Simple **Re-ranking** - Better relevance

### Phase 2: Advanced (4-8 hours)
4. 🔄 **Chain-of-Thought Retrieval** - Iterative refinement
5. 🔄 **Step-Back Prompting** - Better context
6. 🔄 **Multi-Query Expansion** with reasoning

### Phase 3: Sophisticated (8-16 hours)
7. 🚀 **Multi-Hop Reasoning** - Complex questions
8. 🚀 **Metacognitive Search** - Adaptive strategies
9. 🚀 Full **Agentic RAG** - Autonomous decision-making

## Complete Example: Enhanced RAG Service

```python
"""Enhanced RAG Service with Reasoning Capabilities."""
import logging
import json
from typing import Optional, Literal

from app.services.rag_service import RAGService
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ReasoningRAGService(RAGService):
    """RAG service with reasoning-enhanced retrieval."""
    
    def intelligent_search(
        self,
        query: str,
        strategy: Literal["auto", "hyde", "step_back", "chain", "simple"] = "auto",
        n_results: int = 3,
    ) -> dict:
        """
        Intelligent search with automatic strategy selection.
        
        Returns:
            {
                "documents": [...],
                "strategy_used": "hyde",
                "reasoning": "...",
            }
        """
        # Auto-select strategy if needed
        if strategy == "auto":
            strategy = self._select_strategy(query)
        
        logger.info(f"Using strategy: {strategy} for query: {query[:50]}...")
        
        # Execute selected strategy
        if strategy == "hyde":
            documents = self.hyde_search(query, n_results)
        elif strategy == "step_back":
            documents = self.step_back_retrieval(query, n_results)
        elif strategy == "chain":
            documents = self.chain_of_thought_retrieval(query, max_iterations=2)
        else:
            documents = self.search(query, n_results)
        
        # Re-rank with reasoning
        documents = self.reason_and_rerank(query, documents)
        
        return {
            "documents": documents[:n_results],
            "strategy_used": strategy,
            "reasoning": f"Selected {strategy} based on query characteristics",
        }
    
    def _select_strategy(self, query: str) -> str:
        """Simple heuristic-based strategy selection."""
        query_lower = query.lower()
        
        # Heuristic rules
        if any(word in query_lower for word in ["compare", "difference", "vs", "versus"]):
            return "step_back"
        elif any(word in query_lower for word in ["how", "why", "explain"]):
            return "hyde"
        elif len(query.split()) > 15:  # Complex query
            return "chain"
        else:
            return "simple"
    
    def hyde_search(self, query: str, n_results: int = 3) -> list[dict]:
        """[Implementation from above]"""
        # ... (code from earlier)
        pass
    
    def reason_and_rerank(self, query: str, documents: list[dict]) -> list[dict]:
        """[Implementation from above]"""
        # ... (code from earlier)
        pass


# Global instance
reasoning_rag_service = ReasoningRAGService()
```

## Performance Expectations

| Technique | Implementation Effort | Expected Improvement | Best For |
|-----------|---------------------|---------------------|----------|
| HyDE | Low (2h) | +20-50% | General queries |
| Query Understanding | Low (2h) | +15-30% | Complex questions |
| Re-ranking | Low (1h) | +10-20% | Noisy retrievals |
| Step-Back | Medium (3h) | +15-35% | Specific questions |
| Chain-of-Thought | Medium (4h) | +20-40% | Iterative needs |
| Multi-Hop | High (8h) | +30-60% | Complex reasoning |
| Metacognitive | High (6h) | +25-45% | Diverse queries |

## Key Considerations

### Latency vs. Quality Trade-off
- Simple search: ~50-100ms
- HyDE: +500-1000ms (one LLM call)
- Chain-of-Thought: +1500-3000ms (multiple LLM calls)
- Multi-Hop: +2000-5000ms (multiple retrievals + LLM)

### Cost Implications
More reasoning = more LLM calls = higher costs (for API-based models)

### When to Use What

**Use HyDE when:**
- Users ask high-level questions
- Query-document linguistic gap is large
- Quality matters more than speed

**Use Chain-of-Thought when:**
- Initial retrieval is insufficient
- Questions are exploratory
- You need comprehensive coverage

**Use Multi-Hop when:**
- Questions require connecting facts
- Information spans multiple documents
- Relationships matter

**Use Simple Search when:**
- Speed is critical
- Queries are well-formed
- Documents are high quality

## Testing & Evaluation

```python
# Test different strategies
test_queries = [
    "What is RAG?",  # Simple factual
    "How do I deploy with Docker vs Kubernetes?",  # Comparative
    "Why is my model not loading?",  # Troubleshooting
    "Explain the architecture of this system",  # Explanatory
]

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    # Try each strategy
    for strategy in ["simple", "hyde", "step_back", "chain"]:
        result = reasoning_rag_service.intelligent_search(
            query, 
            strategy=strategy
        )
        print(f"\nStrategy: {strategy}")
        print(f"Top doc: {result['documents'][0]['content'][:100]}...")
```

## Conclusion

**Reasoning transforms RAG from retrieval to intelligent information seeking.**

The key insight: Don't just embed and search - **think about what you're looking for and why**.

**Recommended Starting Point:**
1. Implement HyDE (biggest single win)
2. Add simple re-ranking
3. Implement query understanding for complex queries
4. Measure impact before adding more complexity

Would you like me to implement any of these reasoning techniques in your codebase?
