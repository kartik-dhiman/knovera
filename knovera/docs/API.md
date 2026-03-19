# API Contract

## `POST /api/ingest`
Upload one or more PDFs (any language).

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

---

## `GET /api/knowledge-bases`
List all knowledge bases.

### Response
```json
[
  {
    "id": "uuid",
    "name": "My KB",
    "document_ids": ["uuid1", "uuid2"],
    "document_names": ["book.pdf", "notes.pdf"],
    "document_count": 2
  }
]
```

## `POST /api/knowledge-bases`
Create a new knowledge base.

### Request
```json
{
  "name": "My KB",
  "document_ids": ["uuid1", "uuid2"]
}
```

## `DELETE /api/knowledge-bases/{kb_id}`
Delete a knowledge base (documents are not deleted, only the KB mapping).

---

## `GET /api/chats`
List chats. Query params: `include_inactive=true|false` (default: false).

## `POST /api/chats`
Create a new chat.

### Request
```json
{
  "title": "New chat",
  "knowledge_base_id": "uuid-or-null",
  "document_ids": [],
  "user_name": "User",
  "assistant_name": "Assistant"
}
```

## `GET /api/chats/{chat_id}`
Get chat detail including messages and settings.

## `POST /api/chats/{chat_id}/ask`
Ask a question via HTTP (non-streaming).

### Request
```json
{
  "question": "What is X?",
  "citation_mode": true,
  "top_k": 3
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
  "used_chunks": 3,
  "messages": [...]
}
```

## `WS /api/chats/ws/{chat_id}`
WebSocket endpoint for real-time streaming answers.

### Client sends
```json
{
  "question": "What is X?",
  "citation_mode": true,
  "top_k": 3
}
```

### Server sends (in order)
1. `{"type": "info", "message": "retrieving context"}`
2. `{"type": "info", "message": "generating answer"}`
3. `{"type": "token", "content": "The"}` (repeated per token)
4. `{"type": "complete", "answer": "...", "citations": [...], "chat_id": "...", "used_chunks": 3}`

## `PATCH /api/chats/{chat_id}/settings`
Update chat settings (title, names, citation mode, top_k).

## `PATCH /api/chats/{chat_id}/status`
Set chat status to `active` or `inactive`.

## `DELETE /api/chats/{chat_id}`
Delete a chat and its messages.

---

## `POST /api/query`
One-shot query against indexed chunks (no chat history).

### Request
```json
{
  "question": "What is X?",
  "citation_mode": true,
  "top_k": 3,
  "document_ids": null
}
```

### Response
```json
{
  "answer": "...",
  "citations": [...],
  "used_chunks": 3
}
```

## `GET /health`
```json
{ "status": "ok" }
```
