# Runbook

## Local Development
```bash
cd knovera
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Optional: Ollama for LLM Answers
1. Start service:
```bash
ollama serve
```
2. Pull model:
```bash
ollama pull qwen2.5:1.5b-instruct
```
3. Ensure `.env` matches Ollama host/model.

> **Tip:** For better quality answers (slower), use `qwen2.5:3b-instruct` instead.

## Verify End-to-End
1. Open `http://127.0.0.1:8000`
2. Upload a digital-text PDF (any language)
3. Wait until document status becomes `ready`
4. Ask question in UI with citations ON and OFF
5. Try asking in different languages to test multilingual support

## CLI Smoke Test
```bash
# Health check
curl -s http://127.0.0.1:8000/health

# One-shot query
curl -s -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Summarize the key idea","citation_mode":true,"top_k":3}'
```

## Common Issues

### Empty chunks / failed ingestion
- PDF may be scanned image only (OCR not supported in v1)
- Check document status via `GET /api/documents`

### Slow first run
- Embedding model (`paraphrase-multilingual-MiniLM-L12-v2`, ~120 MB) downloads on first use
- LLM model downloads on first `ollama pull`

### Weak answers
- Try increasing `RETRIEVAL_TOP_K` (default: 3)
- Try increasing `MAX_CONTEXT_CHARS` (default: 3500)
- Use a stronger Ollama model: `qwen2.5:3b-instruct`

### No streaming / tokens not appearing
- Ensure the WebSocket connection is active (check browser console)
- The HTTP fallback (`POST /api/chats/{chat_id}/ask`) does not stream tokens

### Changing the embedding model
- If you switch `EMBEDDING_MODEL` in `.env`, you **must** re-ingest all documents:
```bash
rm -rf data/chroma data/app.db
# restart app and re-upload PDFs
```

### Multilingual documents
- All 24 supported scripts are detected automatically — no configuration needed
- Sentence splitting uses language-specific terminators
- The prompt instructs the LLM to preserve original scripts verbatim in citations

## Data Reset
To reset local state, stop app and remove `./data`:
```bash
rm -rf data
```
Then restart and re-ingest PDFs.
