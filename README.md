# Knovera

Turn any document into a conversational knowledge base — with full multilingual support.

## Features

- **Upload one or many PDFs** — digital-text or mixed-language documents
- **Multilingual RAG pipeline** — supports 24+ scripts and languages out of the box
- Convert PDF chunks into embeddings using a multilingual model
- Store / search vectors in local ChromaDB
- Ask questions against indexed PDFs in any supported language
- **Real-time streaming answers** via WebSocket
- Toggle citations on/off per query (with verbatim source excerpts)
- **Smart Intent Understanding** — the engine knows when you want a specific fact vs. a broad summary
- **Dynamic Context** — asks for "summaries" automatically boost retrieval depth and context budget
- Top menu UI with `Chats` and `Knowledge Bases`
- Create / update knowledge bases and bind new chats to a selected KB
- Small LLM via local Ollama, with extractive fallback when unavailable
- **Strictly extractive** — the LLM never uses pre-trained knowledge; answers come only from your documents

## Supported Languages

Knovera automatically detects and preserves text in any of these scripts:

| Family | Scripts |
|---|---|
| **Indic** | Hindi, Marathi, Sanskrit, Nepali (Devanagari), Bengali, Punjabi (Gurmukhi), Gujarati, Tamil, Telugu, Kannada, Malayalam, Odia, Sinhala |
| **East Asian** | Chinese (Simplified & Traditional), Korean (Hangul), Japanese (Hiragana, Katakana) |
| **Middle Eastern** | Arabic, Urdu, Persian |
| **Southeast Asian** | Thai, Lao, Khmer (Cambodian), Myanmar (Burmese) |
| **Other** | Russian, Ukrainian, Bulgarian (Cyrillic), Georgian, Armenian, Amharic/Tigrinya (Ethiopic), Tibetan |

Sentence splitting, embedding, retrieval, and citation are all language-aware.

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
ollama pull qwen2.5:1.5b-instruct
```

3. Start app
```bash
uvicorn app.main:app --reload
```

4. Open UI
- http://127.0.0.1:8000

## Clearing the Database
If you need to completely reset the application state, clear the entire database by removing the following directories and files:

```bash
rm -rf ./data/chroma ./data/app.db ./data/uploads
```

## Configuration
Set env vars in `.env` (optional):

```env
APP_NAME="Knovera"
DATA_DIR=./data
UPLOAD_DIR=./data/uploads
CHROMA_DIR=./data/chroma
SQLITE_PATH=./data/app.db

EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CHUNK_SIZE=900
CHUNK_OVERLAP=150

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b-instruct
RETRIEVAL_TOP_K=3
MAX_CONTEXT_CHARS=3500
```

> **Note on models:**
> - The embedding model `paraphrase-multilingual-MiniLM-L12-v2` supports 50+ languages. If you only use English documents, you can switch to `all-MiniLM-L6-v2` for a smaller download.
> - The LLM `qwen2.5:1.5b-instruct` is optimised for speed on local hardware. For better answer quality (at the cost of ~2× slower generation), use `qwen2.5:3b-instruct`.
> - Changing the embedding model requires re-ingesting all documents.

## API Endpoints
- `POST /api/ingest` — upload PDFs (multipart)
- `GET /api/documents` — list documents with status
- `DELETE /api/documents/{doc_id}` — remove document + vectors
- `GET /api/knowledge-bases` — list KBs
- `POST /api/knowledge-bases` — create a KB
- `GET /api/knowledge-bases/{kb_id}` — KB detail
- `POST /api/knowledge-bases/{kb_id}/documents` — add docs to a KB
- `DELETE /api/knowledge-bases/{kb_id}` — delete a KB
- `GET /api/chats` — list chats
- `POST /api/chats` — create a new chat
- `GET /api/chats/{chat_id}` — chat detail + messages
- `POST /api/chats/{chat_id}/ask` — ask a question (HTTP, non-streaming)
- `WS /api/chats/ws/{chat_id}` — ask via WebSocket (streaming tokens)
- `PATCH /api/chats/{chat_id}/settings` — update chat settings
- `PATCH /api/chats/{chat_id}/status` — activate / deactivate
- `PATCH /api/chats/{chat_id}/identity` — update user/assistant names
- `DELETE /api/chats/{chat_id}` — delete chat
- `POST /api/query` — one-shot query against indexed docs
- `GET /health` — health check

Detailed API and architecture docs are in `docs/`.

## License

Open source. See repository for details.
