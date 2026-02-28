# Architecture

## Overview
This app implements a local-first RAG pipeline:
1. Parse digital-text PDFs
2. Chunk text with overlap
3. Embed chunks
4. Store embeddings in vector DB
5. Retrieve top-k chunks for a query
6. Build prompt context
7. Generate answer with small LLM

## Components
- `app/api`: REST endpoints for ingest/query/document management
- `app/ingestion`: parser, chunker, embedder, indexing service
- `app/retrieval`: retrieval and context assembly
- `app/generation`: prompt builder and LLM adapter
- `app/db`: SQLite metadata + Chroma vector store
- `app/web`: simple HTML/CSS/JS UI

## Storage
- SQLite (`documents` table): document status/metadata (`queued`, `processing`, `ready`, `failed`)
- Chroma collection: chunk vectors + per-chunk metadata (`doc_id`, `doc_name`, `page`, `chunk_index`)
- Filesystem: uploaded PDFs under `data/uploads`

## Ingestion Flow
1. User uploads PDF(s) to `/api/ingest`
2. File is saved to disk
3. Row inserted into SQLite with `queued`
4. Background ingestion task runs:
   - Extract text per page with PyMuPDF
   - Chunk with `chunk_size/chunk_overlap`
   - Embed chunks via sentence-transformers
   - Upsert vectors + metadata to Chroma
   - Mark document `ready` with `chunk_count`

## Query Flow
1. User sends question to `/api/query`
2. Query is embedded
3. Top-k chunks retrieved from Chroma
4. Context is assembled under character budget
5. Prompt is created with citation mode on/off
6. LLM generates answer via Ollama
7. If Ollama fails/unavailable, extractive fallback answer is returned

## Citation Mode
- Controlled by `citation_mode` in `/api/query`
- When enabled:
  - Prompt enforces citations
  - API response returns chunk-level citations
- When disabled:
  - Prompt requests plain answer
  - API returns empty citation list

## Performance Notes
- Fast path uses small embedding model and local vector DB
- `top_k` and `max_context_chars` limit prompt size and latency
- Large PDFs are handled asynchronously via background tasks

## v1 Limitations
- No OCR (digital-text PDFs only)
- No auth / multi-user namespaces
- No reranker/hybrid retrieval yet
