## End-to-End Explanation of `graph_service.py` (Beginner-Friendly)

This file orchestrates the chat workflow using LangGraph. It defines steps and their order, like a recipe.

---

## **1. Imports and Setup** (Lines 1-13)

```python
from langgraph.graph import StateGraph, END
```

- `StateGraph`: builds a workflow graph
- `END`: marks the end of the workflow
- `TypedDict`: defines a dictionary with fixed keys and types
- `AsyncGenerator`: used for streaming (yields values one at a time)

---

## **2. ChatState - The Data Container** (Lines 16-24)

```python
class ChatState(TypedDict):
    conversation_id: str
    user_message: str
    context: str
    response: str
    use_rag: bool
    sources: list[str]
    conversation_history: list[dict]
```

`ChatState` is a dictionary that holds all data as it moves through the workflow:

- `conversation_id`: unique ID for the conversation
- `user_message`: the user's input
- `context`: relevant documents (if RAG is used)
- `response`: the AI's response
- `use_rag`: whether to use RAG
- `sources`: document IDs used
- `conversation_history`: previous messages

---

## **3. Creating the System Prompt** (Lines 27-60)

```python
def create_system_prompt(context: str = "", conversation_history: list[dict] = None) -> str:
```

Builds the prompt for the LLM.

- Base prompt: instructions for the assistant
- Conversation history: adds recent messages (last 6) if available
- RAG context: adds relevant documents if provided

Example:

```python
# If there's context:
"You are a helpful AI assistant...
Previous conversation:
User: Hello
Assistant: Hi there!

Use the following context:
[Document 1]
Some relevant text...
"
```

---

## **4. Retrieving Context (RAG)** (Lines 63-86)

```python
def retrieve_context(state: ChatState) -> ChatState:
```

If RAG is enabled, searches for relevant documents and adds them to the state.

- If `use_rag` is False: returns empty context
- If True: searches ChromaDB, formats results, and updates state with context and source IDs

Returns an updated state with `context` and `sources` populated.

---

## **5. Generating the Response** (Lines 89-106)

```python
def generate_response(state: ChatState) -> ChatState:
```

Generates the AI response using the LLM.

- Builds the prompt with system prompt, context, history, and user message
- Calls `llm_service.generate(prompt)`
- Updates state with the response

Returns an updated state with `response` filled.

---

## **6. Building the Graph** (Lines 109-122)

```python
def create_chat_graph() -> StateGraph:
```

Creates the workflow graph.

```python
workflow = StateGraph(ChatState)  # Create graph with our state type
workflow.add_node("retrieve", retrieve_context)  # Add step 1
workflow.add_node("generate", generate_response)  # Add step 2
workflow.set_entry_point("retrieve")  # Start here
workflow.add_edge("retrieve", "generate")  # Then go to generate
workflow.add_edge("generate", END)  # Then finish
```

Flow:

```
START → retrieve_context → generate_response → END
```

---

## **7. GraphService Class** (Lines 125-225)

Manages the graph and provides chat methods.

### **Class Variable** (Line 128)

```python
_graph = None
```

Stores the compiled graph (created once, reused).

### **get_graph() Method** (Lines 130-135)

```python
@classmethod
def get_graph(cls):
    if cls._graph is None:
        cls._graph = create_chat_graph()
    return cls._graph
```

Singleton pattern: creates the graph once and reuses it.

---

### **chat() Method - Non-Streaming** (Lines 137-171)

Handles non-streaming chat.

Step-by-step:

1. Get or create conversation ID (Line 144)

   ```python
   conv_id = conversation_id or str(uuid.uuid4())
   ```

   Uses provided ID or generates a new one.

2. Get conversation history (Lines 147-149)

   ```python
   if conversation_id:
       conversation_history = session_service.get_conversation_history(conversation_id, limit=6)
   ```

   Loads recent messages if a conversation ID exists.

3. Create initial state (Lines 151-159)

   ```python
   initial_state: ChatState = {
       "conversation_id": conv_id,
       "user_message": message,
       "context": "",  # Will be filled by retrieve_context
       "response": "",  # Will be filled by generate_response
       "use_rag": use_rag,
       "sources": [],
       "conversation_history": conversation_history,
   }
   ```

4. Run the graph (Line 161)

   ```python
   result = graph.invoke(initial_state)
   ```

   Executes the workflow and returns the final state.

5. Save messages (Lines 164-165)

   ```python
   session_service.add_message(conv_id, "user", message)
   session_service.add_message(conv_id, "assistant", result["response"])
   ```

6. Return result (Lines 167-171)
   Returns the response, conversation ID, and sources.

---

### **chat_stream() Method - Streaming** (Lines 173-221)

Handles streaming chat (tokens as they're generated).

Differences from `chat()`:

- Does not use the graph (streaming happens directly)
- Uses `async def` and `AsyncGenerator`
- Yields tokens one at a time

Step-by-step:

1. Get conversation ID and history (Lines 183-188)
   Same as `chat()`.

2. Get RAG context if enabled (Lines 191-196)

   ```python
   if use_rag:
       context = rag_service.get_context(message, n_results=3)
   ```

3. Create prompt (Lines 199-203)
   Builds the prompt with context and history.

4. Save user message (Line 206)

   ```python
   session_service.add_message(conv_id, "user", message)
   ```

5. Stream tokens (Lines 209-218)

   ```python
   full_response = ""
   async for token in llm_service.generate_stream(prompt):
       full_response += token  # Collect for saving later
       yield token  # Send to client immediately
   ```

   - `async for`: iterates over async values
   - `yield`: sends each token immediately
   - Accumulates the full response for saving

6. Save assistant response (Line 221)
   ```python
   session_service.add_message(conv_id, "assistant", full_response)
   ```

---

## **8. Global Instance** (Line 225)

```python
graph_service = GraphService()
```

Creates a single instance used throughout the app.

---

## **Key Python Concepts Explained**

### **TypedDict**

A dictionary with a fixed structure:

```python
state = {"conversation_id": "123", "user_message": "Hello"}
```

### **Dictionary Unpacking** (`**state`)

```python
return {**state, "context": "new context"}
```

Creates a new dict with all keys from `state` plus updates.

### **Class Methods** (`@classmethod`)

Methods that belong to the class, not an instance:

```python
GraphService.chat("Hello")  # Can call without creating instance
```

### **Async Generators** (`AsyncGenerator`)

Functions that yield values over time:

```python
async for token in chat_stream():
    print(token)  # Prints each token as it arrives
```

### **Singleton Pattern**

Ensures only one instance exists:

```python
if cls._graph is None:
    cls._graph = create_chat_graph()  # Create once
return cls._graph  # Reuse forever
```

---

## **Visual Flow Diagram**

### **Non-Streaming (`chat()` method):**

```
User sends message
    ↓
Create initial state
    ↓
Run graph: retrieve_context → generate_response
    ↓
Save messages to database
    ↓
Return complete response
```

### **Streaming (`chat_stream()` method):**

```
User sends message
    ↓
Get context & history
    ↓
Create prompt
    ↓
Save user message
    ↓
Stream tokens one by one → Client sees text appear in real-time
    ↓
Save complete response
```

---

## **Why This Design?**

1. Separation of concerns: each function has one job
2. Reusability: functions can be reused
3. Testability: easy to test each step
4. Extensibility: easy to add steps (e.g., fact-checking)
5. Flexibility: supports both streaming and non-streaming

This file is the orchestrator: it coordinates RAG retrieval, LLM generation, and session management to produce chat responses.
