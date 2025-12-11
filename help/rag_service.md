Reviewing the config to understand the settings, then explaining `rag_service.py` in beginner-friendly terms.

[2 tools called]

## End-to-End Explanation of `rag_service.py` (Beginner-Friendly)

This file implements RAG (Retrieval-Augmented Generation): it stores documents and finds relevant ones to help the AI answer questions.

---

## What is RAG?

RAG lets the AI use your documents to answer questions. Instead of only using its training data, it:

1. Stores your documents
2. Finds relevant parts when you ask a question
3. Uses those parts to generate an answer

Analogy: like a librarian who finds relevant books and pages for your question.

---

## Key Concepts

### 1. Embeddings (Vector Representations)

Embeddings convert text into numbers (vectors) that capture meaning. Similar text has similar numbers.

Example:

- "The cat sat on the mat" → `[0.2, -0.1, 0.8, ...]`
- "A feline rested on a rug" → `[0.19, -0.12, 0.79, ...]` (similar numbers)

### 2. ChromaDB

A vector database that stores documents with their embeddings and finds similar ones quickly.

### 3. Sentence Transformers

A model that converts text to embeddings. This code uses `all-MiniLM-L6-v2`.

---

## File Structure Overview

The file has:

1. Imports and setup (lines 1-13)
2. RAGService class definition (lines 15-122)
3. Global instance (line 125)

---

## 1. Imports (Lines 1-12)

```python
import chromadb
from sentence_transformers import SentenceTransformer
```

- `chromadb`: vector database
- `SentenceTransformer`: creates embeddings
- `uuid`: generates unique IDs
- `Optional`: for values that might be None

---

## 2. RAGService Class (Lines 15-122)

### Class Variables - The Storage (Lines 18-21)

```python
_instance: Optional["RAGService"] = None
_client: Optional[chromadb.Client] = None
_collection: Optional[chromadb.Collection] = None
_embedder: Optional[SentenceTransformer] = None
```

These store:

- `_instance`: singleton instance
- `_client`: ChromaDB connection
- `_collection`: document collection
- `_embedder`: embedding model

The `_` prefix indicates private/internal use.

---

### Singleton Pattern (Lines 23-26)

```python
def __new__(cls) -> "RAGService":
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance
```

Ensures only one instance exists. `__new__` runs before `__init__`.

How it works:

```python
service1 = RAGService()  # Creates instance
service2 = RAGService()  # Returns same instance
# service1 and service2 are the same object!
```

---

### initialize() Method (Lines 28-54)

Sets up ChromaDB and the embedding model.

Step-by-step:

1. Get settings (Line 30)

   ```python
   settings = get_settings()
   ```

   Loads configuration (e.g., embedding model name, ChromaDB path).

2. Load embedding model (Lines 34-35)

   ```python
   logger.info(f"Loading embedding model: {settings.embedding_model}")
   self._embedder = SentenceTransformer(settings.embedding_model)
   ```

   Loads the model (default: `"all-MiniLM-L6-v2"`). This can take a moment.

3. Initialize ChromaDB client (Lines 38-42)

   ```python
   self._client = chromadb.PersistentClient(
       path=settings.chroma_persist_dir,
       settings=ChromaSettings(anonymized_telemetry=False),
   )
   ```

   Creates a persistent client that saves data to disk.

4. Get or create collection (Lines 45-48)

   ```python
   self._collection = self._client.get_or_create_collection(
       name=settings.collection_name,
       metadata={"hnsw:space": "cosine"}
   )
   ```

   - Collection: like a table/folder for documents
   - `"hnsw:space": "cosine"`: uses cosine similarity for search

5. Log success (Line 50)
   ```python
   logger.info(f"ChromaDB initialized. Collection '{settings.collection_name}' has {self._collection.count()} documents.")
   ```

Error handling (Lines 52-54): logs and re-raises errors.

---

### add_document() Method (Lines 56-75)

Adds a document to the collection.

Step-by-step:

1. Check initialization (Lines 58-59)

   ```python
   if not self._collection or not self._embedder:
       raise RuntimeError("RAG service not initialized. Call initialize() first.")
   ```

2. Generate unique ID (Line 61)

   ```python
   doc_id = str(uuid.uuid4())
   ```

   Creates a unique ID like `"a1b2c3d4-e5f6-7890-abcd-ef1234567890"`.

3. Create embedding (Line 64)

   ```python
   embedding = self._embedder.encode(content).tolist()
   ```

   - `encode()`: text → numbers
   - `.tolist()`: converts NumPy array to a Python list

   Example:

   ```python
   text = "Python is a programming language"
   embedding = [0.23, -0.45, 0.67, 0.12, ...]  # 384 numbers for MiniLM
   ```

4. Add to collection (Lines 67-72)

   ```python
   self._collection.add(
       ids=[doc_id],
       documents=[content],
       embeddings=[embedding],
       metadatas=[metadata or {}],
   )
   ```

   Stores:

   - `ids`: unique identifier
   - `documents`: original text
   - `embeddings`: vector representation
   - `metadatas`: optional info (e.g., filename, source)

5. Return document ID (Line 75)
   ```python
   return doc_id
   ```

---

### search() Method (Lines 77-102)

Finds documents similar to a query.

Step-by-step:

1. Check initialization (Lines 79-80)
   Same as `add_document()`.

2. Create query embedding (Lines 82-83)

   ```python
   query_embedding = self._embedder.encode(query).tolist()
   ```

   Converts the query to an embedding.

3. Search collection (Lines 86-89)

   ```python
   results = self._collection.query(
       query_embeddings=[query_embedding],
       n_results=n_results,
   )
   ```

   - Finds the most similar documents
   - Returns top `n_results` (default: 3)

4. Format results (Lines 92-100)

   ```python
   documents = []
   if results["documents"] and results["documents"][0]:
       for i, doc in enumerate(results["documents"][0]):
           documents.append({
               "id": results["ids"][0][i] if results["ids"] else None,
               "content": doc,
               "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
               "distance": results["distances"][0][i] if results["distances"] else None,
           })
   ```

   Formats into a list of dictionaries with:

   - `id`: document ID
   - `content`: text
   - `metadata`: extra info
   - `distance`: similarity score (lower = more similar)

   Why `results["documents"][0]`? ChromaDB returns:

   ```python
   {
       "documents": [[doc1, doc2, doc3]],  # List of lists
       "ids": [[id1, id2, id3]],
       ...
   }
   ```

   So we use `[0]` to get the inner list.

5. Return formatted documents (Line 102)
   ```python
   return documents
   ```

---

### get_context() Method (Lines 104-115)

Formats search results into a context string for the LLM prompt.

Step-by-step:

1. Search for documents (Line 106)

   ```python
   documents = self.search(query, n_results)
   ```

2. Handle empty results (Lines 108-109)

   ```python
   if not documents:
       return ""
   ```

3. Format context (Lines 111-113)

   ```python
   context_parts = []
   for i, doc in enumerate(documents, 1):
       context_parts.append(f"[Document {i}]\n{doc['content']}")
   ```

   Creates strings like:

   ```
   [Document 1]
   Python is a high-level programming language...

   [Document 2]
   Python supports multiple programming paradigms...
   ```

4. Join and return (Line 115)
   ```python
   return "\n\n".join(context_parts)
   ```
   Combines with double newlines.

---

### get_document_count() Method (Lines 117-121)

Returns the number of documents in the collection.

```python
def get_document_count(self) -> int:
    if not self._collection:
        return 0
    return self._collection.count()
```

Simple: returns 0 if not initialized, otherwise the count.

---

## 3. Global Instance (Line 125)

```python
rag_service = RAGService()
```

Creates a single instance used throughout the app.

---

## How It All Works Together

### Example: Adding a Document

```python
# 1. Initialize (happens once at startup)
rag_service.initialize()

# 2. Add a document
doc_id = rag_service.add_document(
    content="Python is a programming language created by Guido van Rossum.",
    metadata={"source": "wikipedia", "year": 1991}
)

# What happens internally:
# - Text → Embedding: [0.23, -0.45, 0.67, ...]
# - Stored in ChromaDB with ID, text, embedding, metadata
```

### Example: Searching for Documents

```python
# User asks: "What is Python?"

# 1. Convert query to embedding
query_embedding = [0.24, -0.44, 0.68, ...]  # Similar to document embedding!

# 2. ChromaDB finds similar documents
results = rag_service.search("What is Python?", n_results=3)

# Returns:
# [
#     {
#         "id": "doc-123",
#         "content": "Python is a programming language...",
#         "distance": 0.15  # Very similar!
#     },
#     ...
# ]
```

### Example: Getting Context for LLM

```python
context = rag_service.get_context("What is Python?", n_results=2)

# Returns formatted string:
# """
# [Document 1]
# Python is a programming language created by Guido van Rossum.
#
# [Document 2]
# Python supports multiple programming paradigms including OOP.
# """
```

---

## Visual Flow Diagram

### Adding a Document:

```
Text: "Python is a language..."
    ↓
Create embedding: [0.23, -0.45, ...]
    ↓
Store in ChromaDB:
  - ID: "abc-123"
  - Text: "Python is a language..."
  - Embedding: [0.23, -0.45, ...]
  - Metadata: {"source": "wikipedia"}
```

### Searching:

```
Query: "What is Python?"
    ↓
Create query embedding: [0.24, -0.44, ...]
    ↓
ChromaDB compares with all document embeddings
    ↓
Finds 3 most similar documents
    ↓
Returns documents with similarity scores
```

---

## Key Python Concepts Explained

### Optional Type Hints

```python
_instance: Optional["RAGService"] = None
```

Means the variable can be `RAGService` or `None`.

### Dictionary Access

```python
doc['content']  # Get value by key
results["documents"][0][i]  # Nested access
```

### List Comprehensions (Alternative)

The code uses a loop, but could also use:

```python
documents = [
    {
        "id": results["ids"][0][i],
        "content": doc,
        ...
    }
    for i, doc in enumerate(results["documents"][0])
]
```

### String Formatting

```python
f"[Document {i}]\n{doc['content']}"
```

F-strings insert variables into strings.

### Method Chaining

```python
self._embedder.encode(content).tolist()
```

Calls `encode()` then `tolist()` on the result.

---

## Why This Design?

1. Singleton: one instance, shared state
2. Persistence: ChromaDB saves to disk
3. Fast search: vector similarity is efficient
4. Flexible metadata: store extra info per document
5. Separation of concerns: RAG logic isolated from other services

---

## Real-World Analogy

Think of it like a library:

- `initialize()`: opens the library and sets up the catalog
- `add_document()`: adds a book with a catalog entry
- `search()`: finds books by topic
- `get_context()`: pulls relevant pages for the librarian
- `get_document_count()`: counts books in the library

The embedding model is like the catalog system that groups similar books together.

---

This service enables RAG: it stores documents, finds relevant ones, and provides context so the AI can answer questions using your documents.
