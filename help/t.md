[14 tools called]

Here’s an end-to-end, beginner-friendly walkthrough of the backend.

## What it is

- FastAPI app that serves chat endpoints plus document upload/RAG and embedding visualizations.
- Uses a local GGUF model via `llama-cpp-python`, ChromaDB for vector storage, and LangGraph to orchestrate a simple two-step workflow (retrieve → generate).

## How it starts up

- `app` is created in `create_app()`, adding CORS and routers. A lifespan hook runs on startup.

```24:52:backend/app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    ...
    rag_service.initialize()
    new_docs = document_loader.load_documents()
    ...
    llm_service.load_model()
```

- Settings (model path, GPU layers, CORS, Chroma paths, etc.) come from `.env`/env vars via Pydantic settings.

```7:42:backend/app/config.py
class Settings(BaseSettings):
    model_path: str = ...
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    ...
```

## Core services

- **LLM**: Loads the GGUF model with `llama_cpp.Llama`; also sets up a LangChain wrapper for streaming.

```45:115:backend/app/services/llm_service.py
self._llm = Llama(...); self._langchain_llm = LlamaCpp(..., streaming=True)
```

- **RAG**: Initializes a persistent Chroma collection and a SentenceTransformer embedder; adds/searches documents and builds context strings.

```28:125:backend/app/services/rag_service.py
self._client = chromadb.PersistentClient(...); self._collection = ...
```

- **LangGraph orchestration**: Two nodes—`retrieve` (optional RAG) then `generate` (LLM).

```86:134:backend/app/services/graph_service.py
workflow.add_node("retrieve", retrieve_context)
workflow.add_node("generate", generate_response)
...
return workflow.compile()
```

- **Document ingestion (uploads)**: Validates file type, dedups by MD5, saves to disk, extracts text (PDF/txt/md), chunks, and adds each chunk to Chroma with metadata.

```75:233:backend/app/services/document_service.py
content_hash = md5(...)
chunks = self._document_loader._chunk_text(text)
rag_service.add_document(...)
```

- **Auto-loader on startup**: Scans `backend/data`, extracts text, chunks, and indexes into Chroma unless already loaded.

```114:182:backend/app/services/document_loader.py
for file_path in files_found:
    ...
    chunks = self._chunk_text(text)
    rag_service.add_document(...)
```

- **Visualization**: Pulls all embeddings from Chroma and renders 2D/3D t-SNE Plotly HTML.

```47:187:backend/app/services/visualization_service.py
tsne = TSNE(...); fig = go.Figure(); return fig.to_html(...)
```

## API surface

- `GET /health` returns status and whether the model is loaded.
- `POST /api/chat` → runs LangGraph workflow (retrieve→generate) and returns full response.

```28:58:backend/app/routers/chat.py
result = graph_service.chat(message=..., use_rag=...)
```

- `POST /api/chat/stream` → SSE stream of tokens from `llm_service.generate_stream`.
- Document ops:
  - `POST /api/documents` (raw text)
  - `POST /api/documents/upload` (file upload with dedup/chunk/index)
  - `GET /api/documents` list uploads; `GET /api/documents/count`; `DELETE /api/documents/{content_hash}`

```127:209:backend/app/routers/chat.py
upload_document -> document_service.upload_document(file)
```

- Visualization: `GET /api/visualize/2d` and `/3d` return Plotly HTML (require enough docs).

```15:61:backend/app/routers/visualization.py
html = visualization_service.generate_2d_visualization(...)
```

## Request lifecycle (chat)

1. Client hits `/api/chat` with message (and optional `use_rag`).
2. Graph node `retrieve` may query Chroma for top docs and build a context string.
3. Graph node `generate` crafts a prompt with context + user message and calls the local LLM.
4. Response returns text plus conversation_id and sources (when `use_rag=True`).

Streaming path is the same prompt, but tokens are yielded over SSE.

## Data & storage

- Vector store: persistent Chroma at `backend/data/chroma`.
- Uploaded files stored under `backend/uploads`, with a registry `.document_hashes.json`.
- Auto-loaded seed docs come from `backend/data/*`.

## Configure & run locally

1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r backend/requirements.txt`
3. Download a GGUF model and set `MODEL_PATH` (or place at `backend/app/models/model.gguf`), plus optional `N_CTX`, `N_GPU_LAYERS`, `TEMPERATURE`, etc. (see `backend/README.md`).
4. `uvicorn app.main:app --reload --port 8000` from the `backend` folder.
5. Open `http://localhost:8000/docs` for interactive docs.

## Mental model (beginner cheat sheet)

- FastAPI = web server + routes.
- Pydantic models = request/response validation.
- Services = reusable singletons (LLM, RAG, document handling, graph, visualization).
- LangGraph = simple state machine for “retrieve → generate”.
- Chroma + SentenceTransformer = embed and store text chunks; search returns relevant snippets.
- Llama-cpp = runs the local GGUF LLM to generate answers (stream or batch).
- Startup loads embeddings/model so requests work immediately.
