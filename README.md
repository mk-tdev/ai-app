# AI Chat Application

A full-stack AI chat application with streaming support, powered by local LLMs.

## Architecture

```
┌─────────────────┐     SSE      ┌─────────────────┐
│   Next.js 15    │◄────────────►│    FastAPI      │
│   Frontend      │              │    Backend      │
└─────────────────┘              └────────┬────────┘
                                          │
                       ┌──────────────────┼──────────────────┐
                       │                  │                  │
                       ▼                  ▼                  ▼
                ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
                │ llama.cpp   │   │  LangGraph  │   │  ChromaDB   │
                │   (LLM)     │   │ (Workflow)  │   │   (RAG)     │
                └─────────────┘   └─────────────┘   └─────────────┘
```

## Tech Stack

- **Backend**: FastAPI, llama-cpp-python, LangGraph, LangChain, ChromaDB
- **Frontend**: Next.js 15, React 19, TypeScript
- **Streaming**: Server-Sent Events (SSE)

## Quick Start

### 1. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download a Model

Download a GGUF model and place it in `backend/models/model.gguf`.

Recommended models:
- [TinyLlama-1.1B](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) - For testing
- [Llama-3.2-3B](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) - Lightweight
- [Mistral-7B](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) - Higher quality

### 3. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the App

Navigate to http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/chat` | POST | Non-streaming chat |
| `/api/chat/stream` | POST | Streaming chat (SSE) |
| `/api/documents` | POST | Add document for RAG |
| `/api/documents/count` | GET | Get document count |

## License

MIT
