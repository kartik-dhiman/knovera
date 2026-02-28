# Knovera

Turn any document into a conversational knowledge base.

## Features
- Upload one or many PDFs
- Convert PDF chunks into embeddings
- Store/search vectors in local ChromaDB
- Ask questions against indexed PDFs
- Toggle citations on/off per query
- Top menu UI with `Chats` and `Knowledge Bases`
- Create/update knowledge bases and bind new chats to a selected KB
- Small LLM via local Ollama, with extractive fallback when unavailable

## Quick Start
### One Command
```bash
cd knovera
bash ./bootstrap_knovera.sh
```

Optional (also bootstrap Ollama + pull model):
```bash
cd knovera
BOOTSTRAP_OLLAMA=1 bash ./bootstrap_knovera.sh
```

### Manual Steps
1. Create env and install deps
```bash
cd knovera
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. (Optional but recommended) run Ollama and pull model
```bash
ollama serve
ollama pull qwen2.5:3b-instruct
```

3. Start app
```bash
uvicorn app.main:app --reload
```

4. Open UI
- http://127.0.0.1:8000

## Configuration
Set env vars in `.env` (optional):

```env
APP_NAME="Knovera"
DATA_DIR=./data
UPLOAD_DIR=./data/uploads
CHROMA_DIR=./data/chroma
SQLITE_PATH=./data/app.db

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=900
CHUNK_OVERLAP=150

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b-instruct
RETRIEVAL_TOP_K=5
MAX_CONTEXT_CHARS=6000
```

## API Endpoints
- `POST /api/ingest` (multipart PDF files)
- `GET /api/documents`
- `DELETE /api/documents/{doc_id}`
- `GET /api/knowledge-bases`
- `POST /api/knowledge-bases`
- `GET /api/knowledge-bases/{kb_id}`
- `POST /api/knowledge-bases/{kb_id}/documents`
- `GET /api/chats`
- `POST /api/chats`
- `GET /api/chats/{chat_id}`
- `POST /api/chats/{chat_id}/ask`
- `DELETE /api/chats/{chat_id}`
- `POST /api/query`
- `GET /health`

Detailed API and architecture docs are in `docs/`.
