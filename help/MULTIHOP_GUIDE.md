# Multi-Hop Reasoning Implementation Guide

## Overview

Multi-hop reasoning has been successfully implemented in your AI application! This allows the system to answer complex questions that require connecting multiple pieces of information across different documents.

## What is Multi-Hop Reasoning?

Multi-hop reasoning is the ability to:
1. **Decompose** complex questions into sequential sub-questions
2. **Retrieve** relevant information for each sub-question
3. **Connect** the answers to form a coherent final response

### Example

**Question**: "Compare Docker and Kubernetes deployment and explain which is better for small teams"

**Multi-Hop Process**:
- **Hop 1**: What is Docker deployment? → [Retrieve docs, extract answer]
- **Hop 2**: What is Kubernetes deployment? → [Retrieve docs, extract answer]
- **Hop 3**: What factors matter for small teams? → [Retrieve docs, extract answer]
- **Synthesis**: Combine all answers → Final comprehensive response

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Chat Request                            │
│  {message, use_rag, use_reasoning, max_hops}               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Graph Service                             │
│  - Manages LangGraph workflow                               │
│  - Routes to appropriate retrieval strategy                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ReasoningRAGService                            │
│  ┌──────────────────────────────────────────────┐          │
│  │ 1. Query Analysis                             │          │
│  │    - Check if multi-hop needed                │          │
│  │    - Decompose into sub-questions             │          │
│  └──────────────────────────────────────────────┘          │
│  ┌──────────────────────────────────────────────┐          │
│  │ 2. Multi-Hop Execution                        │          │
│  │    For each hop:                              │          │
│  │      - Retrieve documents (RAG)               │          │
│  │      - Extract answer (LLM)                   │          │
│  │      - Store for next hop                     │          │
│  └──────────────────────────────────────────────┘          │
│  ┌──────────────────────────────────────────────┐          │
│  │ 3. Answer Synthesis                           │          │
│  │    - Combine all hop answers                  │          │
│  │    - Generate final response                  │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### 1. Regular Chat with Optional Reasoning

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Your question here",
  "use_rag": true,
  "use_reasoning": true,    // Enable multi-hop
  "max_hops": 3,             // Maximum reasoning steps
  "conversation_id": "optional-session-id"
}
```

**Response**:
```json
{
  "message": "The final answer",
  "conversation_id": "uuid",
  "sources": ["doc1", "doc2"]
}
```

### 2. Dedicated Reasoning Endpoint (Recommended for Complex Queries)

```http
POST /api/chat/reasoning
Content-Type: application/json

{
  "message": "Complex multi-step question",
  "max_hops": 3
}
```

**Response** (includes full reasoning chain):
```json
{
  "message": "Final synthesized answer",
  "conversation_id": "uuid",
  "sources": ["doc1", "doc2", "doc3"],
  "strategy_used": "multi_hop",
  "needs_multi_hop": true,
  "reasoning_chain": [
    {
      "step_number": 1,
      "question": "First sub-question?",
      "answer": "Answer to first question",
      "sources": [{...}],
      "confidence": 0.85
    },
    {
      "step_number": 2,
      "question": "Second sub-question using {answer from step 1}?",
      "answer": "Answer to second question",
      "sources": [{...}],
      "confidence": 0.92
    }
  ]
}
```

## Automatic Strategy Selection

The system automatically determines if a query needs multi-hop reasoning based on:

1. **Keywords**: "compare", "difference between", "relationship between", etc.
2. **Complexity**: Multiple question words or long queries
3. **Structure**: Questions requiring connecting information

### Queries That Trigger Multi-Hop

✅ "Compare X and Y and explain which is better"
✅ "What is the relationship between A and B?"
✅ "Who is the CEO of the company that acquired Instagram?"
✅ "How does X affect Y in the context of Z?"

### Simple Queries (No Multi-Hop)

❌ "What is RAG?"
❌ "How do I install Docker?"
❌ "List the features of ChromaDB"

## Configuration

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | string | required | The user's question |
| `use_rag` | boolean | false | Enable retrieval-augmented generation |
| `use_reasoning` | boolean | false | Enable multi-hop reasoning |
| `max_hops` | integer | 3 | Maximum reasoning steps (1-5) |
| `conversation_id` | string | null | Session ID for context |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Final answer |
| `conversation_id` | string | Session identifier |
| `sources` | array | Document IDs used |
| `reasoning_chain` | array | Step-by-step reasoning (if multi-hop) |
| `strategy_used` | string | "simple" or "multi_hop" |
| `needs_multi_hop` | boolean | Whether multi-hop was needed |

## Code Examples

### Python Client

```python
import requests

# Simple query with multi-hop
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "Compare Docker and Kubernetes deployment",
        "use_rag": True,
        "use_reasoning": True,
        "max_hops": 3,
    }
)

result = response.json()
print(f"Answer: {result['message']}")
```

### JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8000/api/chat/reasoning', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "What's the relationship between embeddings and vector DBs?",
    max_hops: 3,
  })
});

const result = await response.json();

// Show reasoning chain
if (result.reasoning_chain) {
  result.reasoning_chain.forEach(step => {
    console.log(`Step ${step.step_number}: ${step.question}`);
    console.log(`Answer: ${step.answer}`);
  });
}

console.log(`Final: ${result.message}`);
```

### cURL

```bash
curl -X POST http://localhost:8000/api/chat/reasoning \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Compare LlamaCPP and Ollama for local models",
    "max_hops": 3
  }'
```

## Testing

### Run the Test Suite

```bash
cd backend
python test_multihop.py
```

This will test:
1. Simple queries (should NOT use multi-hop)
2. Comparative queries (should use multi-hop)
3. Entity relationship queries
4. Complex multi-step questions
5. Troubleshooting queries

### Manual Testing

**Test 1: Simple Query**
```json
{
  "message": "What is RAG?",
  "use_rag": true,
  "use_reasoning": true
}
```
Expected: Strategy = "simple" (no multi-hop needed)

**Test 2: Multi-Hop Query**
```json
{
  "message": "Compare deployment with Docker vs Kubernetes and explain which is better for small teams",
  "use_rag": true,
  "use_reasoning": true,
  "max_hops": 4
}
```
Expected: Strategy = "multi_hop" with 3-4 reasoning steps

## Performance Considerations

### Latency

| Strategy | Typical Latency | LLM Calls |
|----------|----------------|-----------|
| Simple RAG | 500-1000ms | 1 |
| Multi-Hop (3 steps) | 3000-5000ms | 4-5 |

**Why slower?**
- Query decomposition: +500ms (1 LLM call)
- Each hop: +800ms (retrieval + extraction)
- Synthesis: +500ms (1 LLM call)

### Cost

For API-based LLMs (not local models):
- Simple query: ~500 tokens
- Multi-hop (3 steps): ~2000-3000 tokens

### Optimization Tips

1. **Limit max_hops**: Use 2-3 for most queries
2. **Cache results**: Implement caching for common queries
3. **Parallel retrieval**: Retrieve for independent hops in parallel (future enhancement)
4. **Smart strategy selection**: Only use multi-hop when necessary

## Implementation Details

### Key Files

```
backend/app/
├── services/
│   ├── reasoning_rag_service.py    # Multi-hop logic
│   ├── graph_service.py             # Integration
│   └── rag_service.py               # Base retrieval
├── models/
│   └── schemas.py                   # Request/response models
└── routers/
    └── chat.py                      # API endpoints
```

### Core Classes

**ReasoningRAGService**
- `intelligent_search()`: Main entry point
- `multi_hop_reasoning()`: Execute multi-hop process
- `_decompose_query()`: Break query into steps
- `_extract_answer_from_docs()`: Extract per-hop answer
- `_synthesize_final_answer()`: Combine all hops

**MultiHopResult (Model)**
```python
class MultiHopResult:
    query: str
    needs_multi_hop: bool
    reasoning_steps: list[ReasoningStep]
    final_answer: str
    all_sources: list[dict]
    strategy_used: str
```

## Advanced Usage

### Custom Strategy Selection

Override automatic selection:

```python
# Force multi-hop
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "Simple question",
        "use_rag": True,
        "use_reasoning": True,  # Force multi-hop even for simple queries
    }
)
```

### Accessing Reasoning Steps

```python
result = response.json()

if result.get('reasoning_chain'):
    for step in result['reasoning_chain']:
        print(f"Step {step['step_number']}:")
        print(f"  Q: {step['question']}")
        print(f"  A: {step['answer']}")
        print(f"  Confidence: {step['confidence']:.2%}")
        print(f"  Sources: {len(step['sources'])} docs")
```

### Integration with Frontend

```typescript
interface ReasoningStep {
  step_number: number;
  question: string;
  answer: string;
  sources: any[];
  confidence: number;
}

interface MultiHopResponse {
  message: string;
  conversation_id: string;
  sources?: string[];
  reasoning_chain?: ReasoningStep[];
  strategy_used?: string;
  needs_multi_hop?: boolean;
}

// Display reasoning chain in UI
function displayReasoningChain(chain: ReasoningStep[]) {
  return (
    <div className="reasoning-chain">
      <h3>How I arrived at this answer:</h3>
      {chain.map(step => (
        <div key={step.step_number} className="reasoning-step">
          <strong>Step {step.step_number}:</strong> {step.question}
          <p>{step.answer}</p>
          <span className="confidence">Confidence: {(step.confidence * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
}
```

## Future Enhancements

### Planned Features

1. **Parallel Hop Execution**: Execute independent hops simultaneously
2. **Better Confidence Scoring**: Use LLM to assess answer quality
3. **Query Caching**: Cache decompositions for similar queries
4. **Adaptive Max Hops**: Automatically determine optimal hop count
5. **Reasoning Visualization**: Graph-based reasoning chain display
6. **HyDE Integration**: Combine with hypothetical document embeddings
7. **Cross-Document References**: Track information flow between documents

### Contributing

To extend multi-hop reasoning:

1. **Add new strategy**: Extend `_select_strategy()` in `ReasoningRAGService`
2. **Improve decomposition**: Enhance prompt in `_decompose_query()`
3. **Custom synthesis**: Modify `_synthesize_final_answer()`

## Troubleshooting

### Common Issues

**1. Multi-hop not triggering**
- Check `use_reasoning=true` in request
- Verify query complexity (try more complex questions)
- Check logs for strategy selection

**2. Poor reasoning quality**
- Increase `max_hops` (try 4-5)
- Improve document quality in ChromaDB
- Adjust LLM temperature (lower for factual queries)

**3. Slow performance**
- Reduce `max_hops` to 2-3
- Use local LLM with GPU acceleration
- Implement caching

**4. JSON parsing errors**
- LLM not returning valid JSON in decomposition
- Check LLM temperature (lower is better)
- Add more examples in prompt

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.services.reasoning_rag_service').setLevel(logging.DEBUG)
```

### Monitoring

Check logs for:
- Strategy selection decisions
- Reasoning step questions/answers
- Retrieval quality per hop
- Synthesis process

## Conclusion

Multi-hop reasoning significantly enhances your RAG system's ability to:
- ✅ Answer complex, multi-step questions
- ✅ Connect information across multiple documents
- ✅ Provide transparent reasoning chains
- ✅ Handle comparative and analytical queries

**Next Steps**:
1. Test with your specific use case
2. Fine-tune `max_hops` for optimal performance
3. Build UI to visualize reasoning chains
4. Collect user feedback on answer quality

Enjoy your enhanced AI application! 🚀
