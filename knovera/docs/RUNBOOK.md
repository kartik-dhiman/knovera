# Runbook

## Local Development
```bash
cd knovera
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Optional: Ollama for better answers
1. Start service:
```bash
ollama serve
```
2. Pull model:
```bash
ollama pull qwen2.5:3b-instruct
```
3. Ensure `.env` matches Ollama host/model.

## Verify End-to-End
1. Open `http://127.0.0.1:8000`
2. Upload a digital-text PDF
3. Wait until document status becomes `ready`
4. Ask question in UI with citations ON and OFF

## CLI Smoke Test
```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Summarize the key idea","citation_mode":true,"top_k":5}'
```

## Common Issues
- Empty chunks / failed ingestion:
  - PDF may be scanned image only (OCR not supported in v1)
- Slow first run:
  - embedding model download and warm-up
- Weak answers:
  - increase `top_k`
  - increase `MAX_CONTEXT_CHARS`
  - use stronger local Ollama model

## Data Reset
To reset local state, stop app and remove `./data`:
```bash
rm -rf data
```
Then restart and re-ingest PDFs.
