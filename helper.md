## Backend Helper (Beginner Friendly)

- **What this service is**: FastAPI backend that serves chat endpoints, supports RAG (retrieve relevant document chunks from ChromaDB), and can visualize embeddings. Runs a local GGUF LLM via `llama-cpp-python`.
- **Startup flow**: On app startup (see `backend/app/main.py`), settings load; RAG initializes Chroma + embedder; documents in `backend/data` are auto-loaded and chunked; the LLM model is loaded from `MODEL_PATH`.
- **Key settings**: Defined in `backend/app/config.py`, overridable via `.env`—`MODEL_PATH`, `N_CTX`, `N_GPU_LAYERS`, `TEMPERATURE`, `DATA_DIR`, `CHROMA_PERSIST_DIR`, CORS origins, etc.
- **Core services**:
  - `llm_service`: loads and runs the GGUF model (sync and streaming).
  - `rag_service`: manages ChromaDB, embeddings, search, and context assembly.
  - `graph_service`: LangGraph workflow with two steps—`retrieve` (optional RAG) then `generate` (LLM).
  - `document_service`: handles file uploads, dedup by content hash, extracts text (PDF/txt/md), chunks, and indexes chunks into Chroma with metadata.
  - `document_loader`: on startup, ingests seed docs from `backend/data` (if new/changed).
  - `visualization_service`: builds 2D/3D t-SNE Plotly HTML of embeddings.
- **Endpoints (all under `/api` unless noted)**:
  - `/health` (no prefix): status + whether the LLM is loaded.
  - `POST /api/chat`: full reply (optional `use_rag`).
  - `POST /api/chat/stream`: SSE token stream.
  - `POST /api/documents`: add raw text to Chroma.
  - `POST /api/documents/upload`: upload PDF/txt/md, dedup + chunk + index.
  - `GET /api/documents`: list uploaded docs; `GET /api/documents/count`; `DELETE /api/documents/{content_hash}`.
  - `GET /api/visualize/2d` and `/3d`: Plotly HTML (needs enough docs).
- **Run locally (from `backend/`)**:
  1) `python -m venv venv && source venv/bin/activate`
  2) `pip install -r requirements.txt`
  3) Place/download a GGUF model; set `MODEL_PATH` in `.env` (or use default `backend/app/models/model.gguf`).
  4) `uvicorn app.main:app --reload --port 8000`
  5) Open `http://localhost:8000/docs` to try endpoints.

