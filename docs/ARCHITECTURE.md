# Architecture

## Overview
This app implements a local-first, multilingual RAG pipeline:
1. Parse digital-text PDFs (any language)
2. Chunk text with overlap, respecting language-specific sentence boundaries
3. Embed chunks using a multilingual embedding model
4. Store embeddings in a local vector DB
5. Retrieve top-k chunks for a query
6. Build prompt context with automatic script detection
7. Generate a strictly extractive answer with a small LLM
8. Stream tokens to the client via WebSocket

## Components
- `app/api`: REST + WebSocket endpoints for ingest / query / chat / KB management
- `app/ingestion`: PDF parser, multilingual chunker, embedder, indexing service
- `app/retrieval`: retriever and context assembly
- `app/generation`: prompt builder (with language detection) and LLM adapter
- `app/db`: SQLite metadata + Chroma vector store
- `app/core`: config, multilingual script detection utilities, text normalisation
- `app/web`: single-page HTML/CSS/JS UI with real-time streaming

## Storage
- **SQLite** (`documents`, `chats`, `knowledge_bases` tables): document status/metadata, chat history, KB mappings
- **Chroma collection**: chunk vectors + per-chunk metadata (`doc_id`, `doc_name`, `page`, `chunk_index`)
- **Filesystem**: uploaded PDFs under `data/uploads`

## Multilingual Pipeline

### Script Detection (`app/core/utils.py`)
- `detect_scripts(text)` — scans text against 24 Unicode block ranges and returns the set of detected scripts
- `script_preservation_note(text)` — generates a prompt-ready note listing which scripts must be cited verbatim

### Sentence Splitting (`app/ingestion/chunker.py`)
The chunker uses a universal regex that handles terminators for:
- **Latin**: `. ! ?`
- **Devanagari**: `।` (purna viram) `॥` (double danda)
- **CJK**: `。！？` (fullwidth punctuation)
- **Arabic / Urdu**: `۔`
- **Khmer**: `។`, **Myanmar**: `။`, **Tibetan**: `།` `༎`
- **Armenian**: `։` `՞`, **Ethiopic**: `።` `፧`
- Other scripts that use Latin punctuation (Cyrillic, Korean, etc.) are handled by the standard `.!?` rules

### Embedding (`app/ingestion/embedder.py`)
- Default model: `paraphrase-multilingual-MiniLM-L12-v2` (50+ languages)
- All text is NFKC-normalised before encoding
- Embeddings are L2-normalised for cosine similarity search

### Prompt Building (`app/generation/prompt_builder.py`)
- Strictly extractive: the LLM is forbidden from using pre-trained knowledge
- Auto-detects scripts in context/question and adds a targeted preservation note
- Citation format (`[[KB_EXACT]]...[[/KB_EXACT]]`) with matched-pair enforcement
- Falls back to "I could not find an answer" when context is insufficient

## Ingestion Flow
1. User uploads PDF(s) to `/api/ingest`
2. File is saved to disk
3. Row inserted into SQLite with status `queued`
4. Background ingestion task runs:
   - Extract text per page with PyMuPDF (any Unicode text)
   - NFKC-normalise text
   - Chunk with language-aware sentence splitting
   - Embed chunks via multilingual sentence-transformers
   - Upsert vectors + metadata to Chroma
   - Mark document `ready` with `chunk_count`

## Query Flow
1. User sends question via WebSocket (`/api/chats/ws/{chat_id}`)
2. **Intent Analysis**: Question is scanned (`is_broad_question`) to see if it requests a summary/overview
3. Query is embedded using the same multilingual model
4. **Dynamic Context Allocation**: 
   - Standard questions retrieve `top_k=3` chunks and budget 3500 chars (optimised for speed)
   - Broad "summary" questions automatically boost to `top_k=6` and budget 6000 chars (optimised for coverage)
   - The LLM's `num_predict` window is expanded to 1024 tokens for broad questions to prevent cut-offs
5. Top-k chunks retrieved from Chroma and context is assembled
6. Script detection runs on context → adds preservation notes if non-Latin found
7. Strictly extractive prompt built (instructs LLM to understand intent without hallucinating)
8. LLM generates answer via Ollama (streamed through a thread pool to avoid blocking the event loop)
9. Tokens sent to client as they arrive; on completion, formatted with markdown/citations
10. If Ollama fails/unavailable, extractive fallback answer is returned

## Citation Mode
- Controlled by `citation_mode` per chat or per query
- When enabled:
  - Prompt enforces `[[KB_EXACT]]` blocks with verbatim excerpts
  - Script characters are preserved exactly (Devanagari, Arabic, CJK, etc.)
  - API response returns chunk-level citations with scores
- When disabled:
  - Prompt requests plain answer
  - API returns empty citation list

## Streaming Architecture
- The LLM client uses synchronous `requests` with `iter_lines()`
- To avoid blocking the async event loop, the stream runs in a thread pool
- Tokens are pushed to an `asyncio.Queue` via `call_soon_threadsafe`
- The WebSocket handler awaits the queue, sending each token immediately

## Performance Notes
- Multilingual embedding model (~120 MB) — fast on CPU, supports 50+ languages
- `top_k=3` and `max_context_chars=3500` keep prompts compact for fast generation
- `qwen2.5:1.5b-instruct` balances speed and quality on local hardware
- Large PDFs are handled asynchronously via background tasks
- Per-token logging is set to DEBUG to avoid I/O overhead

## Current Limitations
- No OCR (digital-text PDFs only)
- No auth / multi-user namespaces
- No reranker / hybrid retrieval yet
- Token-level streaming on HTTP fallback is not supported (WebSocket only)
