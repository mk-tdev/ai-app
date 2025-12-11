# Multi-Hop Reasoning: Visual Flow Diagrams

## Flow 1: Simple Query (No Multi-Hop)

```
┌─────────────────────────────────────────────────────────────┐
│  User Query: "What is RAG?"                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Strategy Selection                                         │
│  → Query is simple (no indicators for multi-hop)            │
│  → Decision: USE SIMPLE SEARCH                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Single Vector Search                                       │
│  → Embed query                                              │
│  → Search ChromaDB                                          │
│  → Return top 3 documents                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Generate Response                                          │
│  → Use documents as context                                 │
│  → LLM generates answer                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Response: "RAG is Retrieval-Augmented Generation..."      │
│  Strategy: "simple"                                         │
│  Latency: ~500ms                                            │
└─────────────────────────────────────────────────────────────┘
```

## Flow 2: Multi-Hop Query

```
┌─────────────────────────────────────────────────────────────┐
│  User Query: "Compare Docker and Kubernetes deployment     │
│               and explain which is better for small teams" │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Strategy Selection                                         │
│  ✓ Contains "compare" keyword                               │
│  ✓ Long query (12 words)                                    │
│  ✓ Multiple concepts (Docker, Kubernetes, small teams)      │
│  → Decision: USE MULTI-HOP REASONING                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Query Decomposition (LLM)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Prompt: "Break this into sequential sub-questions"   │  │
│  │ Response:                                             │  │
│  │  {                                                    │  │
│  │    "needs_multi_hop": true,                          │  │
│  │    "reasoning_steps": [                              │  │
│  │      {"step": 1, "question": "What is Docker         │  │
│  │                   deployment?"},                     │  │
│  │      {"step": 2, "question": "What is Kubernetes     │  │
│  │                   deployment?"},                     │  │
│  │      {"step": 3, "question": "What factors matter    │  │
│  │                   for small teams?"}                 │  │
│  │    ]                                                  │  │
│  │  }                                                    │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Execute Hop 1                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Question: "What is Docker deployment?"                │  │
│  │                                                        │  │
│  │ 1. Vector Search → Find Docker docs                   │  │
│  │ 2. Extract Answer → "Docker deployment uses           │  │
│  │    containers to package applications..."             │  │
│  │ 3. Store as X                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│  Sources: [docker_guide.pdf, deployment.md]                 │
│  Confidence: 0.87                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Execute Hop 2                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Question: "What is Kubernetes deployment?"            │  │
│  │                                                        │  │
│  │ 1. Vector Search → Find Kubernetes docs               │  │
│  │ 2. Extract Answer → "Kubernetes orchestrates          │  │
│  │    containers across clusters..."                     │  │
│  │ 3. Store as Y                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│  Sources: [k8s_intro.md, orchestration.pdf]                 │
│  Confidence: 0.92                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Execute Hop 3                                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Question: "What factors matter for small teams?"      │  │
│  │                                                        │  │
│  │ 1. Vector Search → Find team-size docs                │  │
│  │ 2. Extract Answer → "Small teams need simplicity,     │  │
│  │    low overhead..."                                   │  │
│  │ 3. Store as Z                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│  Sources: [best_practices.md]                               │
│  Confidence: 0.78                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Synthesize Final Answer (LLM)                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Context: All hop answers (X, Y, Z)                    │  │
│  │                                                        │  │
│  │ Prompt: "Based on these findings, answer:            │  │
│  │          Compare Docker and K8s for small teams"      │  │
│  │                                                        │  │
│  │ Output: "Docker is better for small teams because:    │  │
│  │          - Simpler setup (from X)                     │  │
│  │          - Lower overhead (from Z)                    │  │
│  │          While Kubernetes offers orchestration (Y),   │  │
│  │          it's overkill for small teams (Z)..."        │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Response with Reasoning Chain                              │
│  {                                                           │
│    "message": "Docker is better for small teams...",        │
│    "strategy_used": "multi_hop",                            │
│    "reasoning_chain": [                                     │
│      {step: 1, question: "...", answer: "...", conf: 0.87}, │
│      {step: 2, question: "...", answer: "...", conf: 0.92}, │
│      {step: 3, question: "...", answer: "...", conf: 0.78}  │
│    ]                                                         │
│  }                                                           │
│  Latency: ~4000ms                                           │
└─────────────────────────────────────────────────────────────┘
```

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  /api/chat          - Standard chat (optional reasoning)    │
│  /api/chat/reasoning - Dedicated multi-hop endpoint         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Graph Service                            │
│  - LangGraph workflow orchestration                         │
│  - State management (ChatState)                             │
│  - Session history integration                              │
└────────────────────┬────────────────────────────────────────┘
                     │
           ┌─────────┴─────────┐
           │                   │
           ▼                   ▼
┌──────────────────┐  ┌──────────────────────────────┐
│   RAGService     │  │  ReasoningRAGService         │
│  (Simple)        │  │  (Multi-Hop)                 │
│                  │  │                              │
│  • Vector Search │  │  • Strategy Selection        │
│  • Top-K Results │  │  • Query Decomposition       │
│  • Fast          │  │  • Iterative Retrieval       │
│                  │  │  • Answer Extraction         │
│                  │  │  • Synthesis                 │
└──────────────────┘  └──────────────────────────────┘
           │                   │
           └─────────┬─────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    ChromaDB                                 │
│  Collection: "documents"                                    │
│  • Document embeddings (384-dim)                            │
│  • Cosine similarity search                                 │
│  • Metadata filtering                                       │
└─────────────────────────────────────────────────────────────┘
```

## Decision Tree: When Multi-Hop is Used

```
                    User Query
                        │
                        ▼
              ┌─────────────────┐
              │  use_reasoning  │
              │    enabled?     │
              └────────┬────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
          NO                      YES
           │                       │
           ▼                       ▼
    ┌───────────┐      ┌──────────────────────┐
    │  Simple   │      │  Analyze Query       │
    │  Search   │      │  Complexity          │
    └───────────┘      └──────────┬───────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌───────────────────────┐   ┌──────────────────┐
        │  Has Multi-Hop        │   │  Simple Query    │
        │  Indicators?          │   │                  │
        │  • "compare"          │   │  Examples:       │
        │  • "relationship"     │   │  • "What is X?"  │
        │  • Multiple entities  │   │  • "How to Y?"   │
        │  • Long/complex       │   │                  │
        └───────────┬───────────┘   └────────┬─────────┘
                    │                        │
                   YES                      NO
                    │                        │
                    ▼                        ▼
        ┌────────────────────┐   ┌──────────────────┐
        │   Multi-Hop        │   │   Simple Search  │
        │   Reasoning        │   │                  │
        │                    │   │   • 1 retrieval  │
        │   • Decompose      │   │   • 1 LLM call   │
        │   • N retrievals   │   │   • Fast         │
        │   • N+2 LLM calls  │   │                  │
        │   • Synthesize     │   │                  │
        └────────────────────┘   └──────────────────┘
```

## Performance Comparison

```
                    Simple RAG         Multi-Hop (3 steps)
                ┌─────────────┐       ┌─────────────────┐
Latency         │   500ms     │       │    4000ms       │
                └─────────────┘       └─────────────────┘

LLM Calls       │      1      │       │       5         │
                └─────────────┘       └─────────────────┘
                                      (decompose + 3 extracts
                                       + synthesize)

Vector          │      1      │       │       3         │
Searches        └─────────────┘       └─────────────────┘

Quality         ████░░░░░░            ██████████
(Complex Qs)    (Good)                (Excellent)

Best For        • Simple facts        • Comparisons
                • Direct lookup       • Relationships
                • Speed critical      • Multi-step logic
                                      • Analysis
```

## Example Reasoning Chain

```
Query: "What's the relationship between ChromaDB and embeddings in RAG?"

┌───────────────────────────────────────────────────────────┐
│ Decomposition                                             │
├───────────────────────────────────────────────────────────┤
│ Step 1: What are embeddings in RAG?                       │
│ Step 2: What is ChromaDB?                                 │
│ Step 3: How does ChromaDB use embeddings?                 │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ Hop 1: What are embeddings in RAG?                        │
├─────────────────┬─────────────────────────────────────────┤
│ Retrieve        │ → embeddings.md, rag_overview.pdf       │
│ Extract         │ → "Embeddings are vector                │
│                 │    representations of text..."           │
│ Confidence      │ → 0.89                                  │
└─────────────────┴─────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ Hop 2: What is ChromaDB?                                  │
├─────────────────┬─────────────────────────────────────────┤
│ Retrieve        │ → chromadb_intro.md                     │
│ Extract         │ → "ChromaDB is a vector database for    │
│                 │    storing embeddings..."                │
│ Confidence      │ → 0.94                                  │
└─────────────────┴─────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ Hop 3: How does ChromaDB use embeddings?                  │
├─────────────────┬─────────────────────────────────────────┤
│ Retrieve        │ → vector_search.md, similarity.pdf      │
│ Extract         │ → "ChromaDB stores embeddings and uses  │
│                 │    cosine similarity for search..."      │
│ Confidence      │ → 0.91                                  │
└─────────────────┴─────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ Synthesis                                                  │
├───────────────────────────────────────────────────────────┤
│ Combining all hops:                                        │
│                                                            │
│ "The relationship between ChromaDB and embeddings in RAG:  │
│  1. Embeddings convert text to vectors (Hop 1)            │
│  2. ChromaDB stores these vectors (Hop 2)                 │
│  3. ChromaDB enables semantic search by comparing          │
│     query embeddings with stored embeddings using          │
│     cosine similarity (Hop 3)"                             │
└───────────────────────────────────────────────────────────┘
```

## Integration with Existing System

```
┌─────────────────────────────────────────────────────────────┐
│  Existing Components (Already Working)                      │
├─────────────────────────────────────────────────────────────┤
│  ✓ LangGraph workflow                                       │
│  ✓ RAG with ChromaDB                                        │
│  ✓ Session management                                       │
│  ✓ LLM providers (LlamaCPP, Ollama, HF)                     │
│  ✓ Document loading                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Now Enhanced With
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  NEW: Multi-Hop Reasoning Layer                             │
├─────────────────────────────────────────────────────────────┤
│  + ReasoningRAGService                                      │
│  + Automatic strategy selection                             │
│  + Query decomposition                                      │
│  + Iterative retrieval                                      │
│  + Answer synthesis                                         │
│  + Reasoning chain transparency                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Exposed Via
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  API Endpoints                                              │
├─────────────────────────────────────────────────────────────┤
│  POST /api/chat                 (with use_reasoning param)  │
│  POST /api/chat/reasoning       (dedicated endpoint)        │
└─────────────────────────────────────────────────────────────┘
```

---

These diagrams illustrate the complete multi-hop reasoning flow from 
user query to final answer, showing how the system intelligently decides 
when to use multi-hop reasoning and how it executes the process.
