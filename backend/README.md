# AI Chat Backend

FastAPI backend with llama.cpp, LangGraph, LangChain, and ChromaDB.

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
   ```
      # Option 1: Fix venv (if possible)
      python3 -m venv venv --clear
      # Option 2: Create new venv
      rm -rf venv
      python3 -m venv venv
      # Install all dependencies
      source venv/bin/activate
      pip install -r requirements.txt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download a GGUF model:**
   Place your model file in `models/model.gguf`. Recommended models:
   - [TinyLlama-1.1B](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) - For testing
   - [Llama-3.2-3B](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) - Lightweight
   - [Mistral-7B](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) - Better quality

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/chat` - Non-streaming chat
- `POST /api/chat/stream` - Streaming chat (SSE)
- `POST /api/documents` - Add document for RAG
- `GET /api/documents/count` - Get document count

## Configuration

Set environment variables or create a `.env` file:

```env
MODEL_PATH=./models/model.gguf
N_CTX=4096
N_GPU_LAYERS=0
TEMPERATURE=0.7
```
