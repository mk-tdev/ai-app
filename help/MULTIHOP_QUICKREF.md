# Multi-Hop Reasoning: Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload

# 2. Test multi-hop (in another terminal)
python3 examples_multihop.py
```

## 📡 API Calls

### Simple Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is RAG?", "use_rag": true}'
```

### Multi-Hop Reasoning
```bash
curl -X POST http://localhost:8000/api/chat/reasoning \
  -H "Content-Type: application/json" \
  -d '{"message": "Compare Docker and Kubernetes", "max_hops": 3}'
```

## 🎯 When to Use

| Query Type | Use Multi-Hop? | Example |
|------------|----------------|---------|
| Simple fact | ❌ No | "What is RAG?" |
| Comparison | ✅ Yes | "Compare X and Y" |
| Relationship | ✅ Yes | "How does X relate to Y?" |
| Multi-step | ✅ Yes | "Who created X and what is it for?" |

## 📊 Parameters

```python
{
  "message": str,           # Required
  "use_rag": bool,          # Default: false
  "use_reasoning": bool,    # Default: false (enables multi-hop)
  "max_hops": int,          # Default: 3, Range: 1-5
  "conversation_id": str    # Optional (for context)
}
```

## 📤 Response

```json
{
  "message": "Final answer",
  "conversation_id": "uuid",
  "sources": ["doc1", "doc2"],
  "reasoning_chain": [/* if multi-hop */],
  "strategy_used": "simple|multi_hop",
  "needs_multi_hop": true|false
}
```

## ⚡ Performance

- **Simple**: ~500ms, 1 LLM call
- **Multi-Hop (3)**: ~4000ms, 5 LLM calls

## 🔧 Files

| File | Purpose |
|------|---------|
| `reasoning_rag_service.py` | Core logic |
| `examples_multihop.py` | Examples |
| `test_multihop.py` | Tests |
| `MULTIHOP_GUIDE.md` | Full guide |

## 🧪 Test It

```python
import requests

r = requests.post(
    "http://localhost:8000/api/chat/reasoning",
    json={"message": "Compare Docker and K8s", "max_hops": 3}
)

# View reasoning steps
for step in r.json()['reasoning_chain']:
    print(f"{step['question']} → {step['answer']}")
```

## 🎨 Python Example

```python
import requests

def ask_with_reasoning(question, max_hops=3):
    response = requests.post(
        "http://localhost:8000/api/chat/reasoning",
        json={"message": question, "max_hops": max_hops}
    )
    result = response.json()
    
    # Show reasoning
    if result.get('reasoning_chain'):
        print("🧠 Reasoning:")
        for step in result['reasoning_chain']:
            print(f"  {step['step_number']}. {step['question']}")
            print(f"     → {step['answer'][:80]}...")
    
    print(f"\n💡 Answer:\n{result['message']}")
    
    return result

# Use it
ask_with_reasoning(
    "What's the relationship between embeddings and ChromaDB?"
)
```

## 🎓 Examples

```python
# Example 1: Comparison
"Compare Docker and Kubernetes deployment"
# → Multi-hop with 3 steps

# Example 2: Relationship
"How do embeddings relate to vector databases?"
# → Multi-hop with 2-3 steps

# Example 3: Multi-entity
"Compare LlamaCPP, Ollama, and HuggingFace"
# → Multi-hop with 4 steps

# Example 4: Simple (no multi-hop)
"What is RAG?"
# → Simple search (automatic)
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Not using multi-hop | Set `use_reasoning=true` |
| Poor quality | Increase `max_hops` to 4-5 |
| Too slow | Reduce `max_hops` to 2 |
| Server error | Check backend logs |

## 📚 Documentation

- **Quick Start**: This file
- **Complete Guide**: `MULTIHOP_GUIDE.md`
- **Visual Diagrams**: `MULTIHOP_DIAGRAMS.md`
- **Summary**: `MULTIHOP_SUMMARY.md`
- **All Techniques**: `REASONING_FOR_RAG.md`

## ✅ Checklist

Before using:
- [ ] Backend running (`uvicorn app.main:app`)
- [ ] RAG documents loaded (check `/api/documents/count`)
- [ ] LLM model loaded (check `/health`)

## 🎯 Best Practices

1. Use `max_hops=3` for most queries
2. Monitor reasoning chains for quality
3. Use `/api/chat/reasoning` for complex questions
4. Use `/api/chat` with `use_reasoning=false` for simple questions
5. Cache common query patterns

## 🔥 Power User Tips

```python
# Force multi-hop for any query
{"use_reasoning": True}

# Get full reasoning chain
POST /api/chat/reasoning

# Adjust hop count dynamically
{"max_hops": 2}  # faster
{"max_hops": 5}  # more thorough

# Combine with conversation history
{"conversation_id": "session-123", "use_reasoning": True}
```

## 📞 Quick Commands

```bash
# Start server
uvicorn app.main:app --reload

# Run examples
python3 examples_multihop.py

# Run tests
python3 test_multihop.py

# Check health
curl http://localhost:8000/health
```

---

**Got Questions?** Check `MULTIHOP_GUIDE.md` for the full documentation!

**Ready to test?** Run: `python3 examples_multihop.py` 🚀
