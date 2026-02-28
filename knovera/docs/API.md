# API Contract

## `POST /api/ingest`
Upload one or more PDFs.

### Request
- `multipart/form-data`
- field: `files` (repeatable)

### Response
```json
{
  "items": [
    {
      "document_id": "uuid",
      "name": "book.pdf",
      "status": "queued"
    }
  ]
}
```

## `GET /api/documents`
Returns documents with ingestion state.

### Response
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "book.pdf",
      "path": "./data/uploads/...",
      "status": "ready",
      "created_at": "...",
      "updated_at": "...",
      "chunk_count": 123,
      "error": null
    }
  ]
}
```

## `DELETE /api/documents/{doc_id}`
Deletes SQLite record, vector chunks, and uploaded file.

### Response
```json
{ "deleted": "uuid" }
```

## `POST /api/query`
Ask question against indexed chunks.

### Request
```json
{
  "question": "What is X?",
  "citation_mode": true,
  "top_k": 5,
  "document_ids": null
}
```

### Response
```json
{
  "answer": "...",
  "citations": [
    {
      "doc_id": "uuid",
      "doc_name": "book.pdf",
      "page": 12,
      "chunk_index": 0,
      "score": 0.83
    }
  ],
  "used_chunks": 5
}
```

## `GET /health`
```json
{ "status": "ok" }
```
