from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from app.core.config import settings


class SQLiteStore:
    def __init__(self) -> None:
        Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(settings.sqlite_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0,
                    error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    knowledge_base_id TEXT,
                    user_name TEXT DEFAULT 'User',
                    assistant_name TEXT DEFAULT 'Assistant',
                    citation_mode INTEGER DEFAULT 1,
                    top_k INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_documents (
                    chat_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    PRIMARY KEY (chat_id, doc_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base_documents (
                    knowledge_base_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    PRIMARY KEY (knowledge_base_id, doc_id)
                )
                """
            )
            columns = [r["name"] for r in conn.execute("PRAGMA table_info(chats)").fetchall()]
            if "knowledge_base_id" not in columns:
                conn.execute("ALTER TABLE chats ADD COLUMN knowledge_base_id TEXT")
            if "user_name" not in columns:
                conn.execute("ALTER TABLE chats ADD COLUMN user_name TEXT DEFAULT 'User'")
            if "assistant_name" not in columns:
                conn.execute("ALTER TABLE chats ADD COLUMN assistant_name TEXT DEFAULT 'Assistant'")
            if "citation_mode" not in columns:
                conn.execute("ALTER TABLE chats ADD COLUMN citation_mode INTEGER DEFAULT 1")
            if "top_k" not in columns:
                conn.execute("ALTER TABLE chats ADD COLUMN top_k INTEGER DEFAULT 5")
            if "status" not in columns:
                conn.execute("ALTER TABLE chats ADD COLUMN status TEXT DEFAULT 'active'")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def create_document(self, doc_id: str, name: str, path: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO documents(id, name, path, status, created_at, updated_at)
                VALUES (?, ?, ?, 'queued', ?, ?)
                """,
                (doc_id, name, path, now, now),
            )

    def update_document_status(
        self, doc_id: str, status: str, chunk_count: Optional[int] = None, error: Optional[str] = None
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            if chunk_count is None:
                conn.execute(
                    """
                    UPDATE documents
                    SET status = ?, error = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, error, now, doc_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE documents
                    SET status = ?, chunk_count = ?, error = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, chunk_count, error, now, doc_id),
                )

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, path, status, created_at, updated_at, chunk_count, error FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, path, status, created_at, updated_at, chunk_count, error FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()
        return dict(row) if row else None

    def delete_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = self.get_document(doc_id)
        if not doc:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.execute("DELETE FROM chat_documents WHERE doc_id = ?", (doc_id,))
            conn.execute("DELETE FROM knowledge_base_documents WHERE doc_id = ?", (doc_id,))
        return doc

    def filter_existing_ready_document_ids(self, doc_ids: List[str]) -> List[str]:
        if not doc_ids:
            return []
        placeholders = ",".join("?" for _ in doc_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT id FROM documents WHERE status = 'ready' AND id IN ({placeholders})",
                tuple(doc_ids),
            ).fetchall()
        return [r["id"] for r in rows]

    def create_chat(
        self,
        chat_id: str,
        title: str,
        document_ids: List[str],
        knowledge_base_id: Optional[str] = None,
        user_name: str = "User",
        assistant_name: str = "Assistant",
        citation_mode: bool = True,
        top_k: int = 5,
    ) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chats(id, title, knowledge_base_id, user_name, assistant_name, citation_mode, top_k, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (chat_id, title, knowledge_base_id, user_name, assistant_name, 1 if citation_mode else 0, top_k, now, now),
            )
            for doc_id in document_ids:
                conn.execute(
                    "INSERT INTO chat_documents(chat_id, doc_id) VALUES (?, ?)",
                    (chat_id, doc_id),
                )

    def _build_chat_summary(self, conn: sqlite3.Connection, chat_row: sqlite3.Row) -> Dict[str, Any]:
        kb_id = chat_row["knowledge_base_id"]
        kb_name = None
        if kb_id:
            kb = conn.execute("SELECT id, name FROM knowledge_bases WHERE id = ?", (kb_id,)).fetchone()
            if kb:
                kb_name = kb["name"]
                docs = conn.execute(
                    """
                    SELECT d.id, d.name
                    FROM knowledge_base_documents kbd
                    JOIN documents d ON d.id = kbd.doc_id
                    WHERE kbd.knowledge_base_id = ?
                    ORDER BY d.name ASC
                    """,
                    (kb_id,),
                ).fetchall()
            else:
                docs = []
        else:
            docs = conn.execute(
                """
                SELECT d.id, d.name
                FROM chat_documents cd
                JOIN documents d ON d.id = cd.doc_id
                WHERE cd.chat_id = ?
                ORDER BY d.name ASC
                """,
                (chat_row["id"],),
            ).fetchall()
        return {
            "id": chat_row["id"],
            "title": chat_row["title"],
            "created_at": chat_row["created_at"],
            "updated_at": chat_row["updated_at"],
            "document_ids": [d["id"] for d in docs],
            "document_names": [d["name"] for d in docs],
            "knowledge_base_id": kb_id,
            "knowledge_base_name": kb_name,
            "user_name": chat_row["user_name"] or "User",
            "assistant_name": chat_row["assistant_name"] or "Assistant",
            "citation_mode": bool(chat_row["citation_mode"]) if chat_row["citation_mode"] is not None else True,
            "top_k": int(chat_row["top_k"] or 5),
            "status": chat_row["status"] or "active",
        }

    def list_chats(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if include_inactive:
                rows = conn.execute(
                    "SELECT id, title, knowledge_base_id, user_name, assistant_name, citation_mode, top_k, status, created_at, updated_at FROM chats ORDER BY updated_at DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, title, knowledge_base_id, user_name, assistant_name, citation_mode, top_k, status, created_at, updated_at FROM chats WHERE status = 'active' ORDER BY updated_at DESC"
                ).fetchall()
            return [self._build_chat_summary(conn, row) for row in rows]

    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, title, knowledge_base_id, user_name, assistant_name, citation_mode, top_k, status, created_at, updated_at FROM chats WHERE id = ?",
                (chat_id,),
            ).fetchone()
            if not row:
                return None
            return self._build_chat_summary(conn, row)

    def update_chat_status(self, chat_id: str, status: str) -> bool:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone()
            if not exists:
                return False
            conn.execute(
                "UPDATE chats SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, chat_id),
            )
        return True

    def update_chat_identities(self, chat_id: str, user_name: str, assistant_name: str) -> bool:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone()
            if not exists:
                return False
            conn.execute(
                "UPDATE chats SET user_name = ?, assistant_name = ?, updated_at = ? WHERE id = ?",
                (user_name, assistant_name, now, chat_id),
            )
        return True

    def update_chat_settings(
        self,
        chat_id: str,
        title: Optional[str] = None,
        user_name: Optional[str] = None,
        assistant_name: Optional[str] = None,
        citation_mode: Optional[bool] = None,
        top_k: Optional[int] = None,
    ) -> bool:
        fields: List[str] = []
        values: List[Any] = []

        if title is not None:
            title_clean = title.strip()
            if title_clean:
                fields.append("title = ?")
                values.append(title_clean)
        if user_name is not None:
            user_name_clean = user_name.strip() or "User"
            fields.append("user_name = ?")
            values.append(user_name_clean)
        if assistant_name is not None:
            assistant_name_clean = assistant_name.strip() or "Assistant"
            fields.append("assistant_name = ?")
            values.append(assistant_name_clean)
        if citation_mode is not None:
            fields.append("citation_mode = ?")
            values.append(1 if citation_mode else 0)
        if top_k is not None:
            fields.append("top_k = ?")
            values.append(int(top_k))

        if not fields:
            return False

        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone()
            if not exists:
                return False
            query = f"UPDATE chats SET {', '.join(fields)}, updated_at = ? WHERE id = ?"
            values.extend([now, chat_id])
            conn.execute(query, tuple(values))
        return True

    def touch_chat(self, chat_id: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (now, chat_id))

    def update_chat_title(self, chat_id: str, title: str) -> bool:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone()
            if not exists:
                return False
            conn.execute(
                "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, chat_id),
            )
        return True

    def add_chat_message(self, chat_id: str, role: str, content: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chat_messages(chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, now),
            )
            conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (now, chat_id))

    def list_chat_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, created_at
                FROM chat_messages
                WHERE chat_id = ?
                ORDER BY id ASC
                """,
                (chat_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_chat(self, chat_id: str) -> bool:
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone()
            if not exists:
                return False
            conn.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
            conn.execute("DELETE FROM chat_documents WHERE chat_id = ?", (chat_id,))
            conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        return True

    def create_knowledge_base(self, kb_id: str, name: str, document_ids: List[str]) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO knowledge_bases(id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (kb_id, name, now, now),
            )
            for doc_id in document_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO knowledge_base_documents(knowledge_base_id, doc_id) VALUES (?, ?)",
                    (kb_id, doc_id),
                )

    def add_documents_to_knowledge_base(self, kb_id: str, document_ids: List[str]) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            for doc_id in document_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO knowledge_base_documents(knowledge_base_id, doc_id) VALUES (?, ?)",
                    (kb_id, doc_id),
                )
            conn.execute("UPDATE knowledge_bases SET updated_at = ? WHERE id = ?", (now, kb_id))

    def update_knowledge_base(self, kb_id: str, name: Optional[str], document_ids: List[str]) -> bool:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            exists = conn.execute("SELECT 1 FROM knowledge_bases WHERE id = ?", (kb_id,)).fetchone()
            if not exists:
                return False
            if name is not None and name.strip():
                conn.execute(
                    "UPDATE knowledge_bases SET name = ?, updated_at = ? WHERE id = ?",
                    (name.strip(), now, kb_id),
                )
            for doc_id in document_ids:
                conn.execute(
                    "INSERT OR IGNORE INTO knowledge_base_documents(knowledge_base_id, doc_id) VALUES (?, ?)",
                    (kb_id, doc_id),
                )
            conn.execute("UPDATE knowledge_bases SET updated_at = ? WHERE id = ?", (now, kb_id))
        return True

    def _build_kb_summary(self, conn: sqlite3.Connection, kb_row: sqlite3.Row) -> Dict[str, Any]:
        docs = conn.execute(
            """
            SELECT d.id, d.name, d.status
            FROM knowledge_base_documents kbd
            JOIN documents d ON d.id = kbd.doc_id
            WHERE kbd.knowledge_base_id = ?
            ORDER BY d.name ASC
            """,
            (kb_row["id"],),
        ).fetchall()
        return {
            "id": kb_row["id"],
            "name": kb_row["name"],
            "created_at": kb_row["created_at"],
            "updated_at": kb_row["updated_at"],
            "document_ids": [d["id"] for d in docs],
            "document_names": [d["name"] for d in docs],
            "document_count": len(docs),
        }

    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at, updated_at FROM knowledge_bases ORDER BY updated_at DESC"
            ).fetchall()
            return [self._build_kb_summary(conn, row) for row in rows]

    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, created_at, updated_at FROM knowledge_bases WHERE id = ?",
                (kb_id,),
            ).fetchone()
            if not row:
                return None
            return self._build_kb_summary(conn, row)

    def get_knowledge_base_document_ids(self, kb_id: str) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT doc_id FROM knowledge_base_documents WHERE knowledge_base_id = ?",
                (kb_id,),
            ).fetchall()
        return [r["doc_id"] for r in rows]
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """Delete a knowledge base and all its document associations.
        
        Returns True if deleted, False if not found.
        """
        with self._connect() as conn:
            # Check if KB exists
            kb = conn.execute(
                "SELECT id FROM knowledge_bases WHERE id = ?",
                (kb_id,),
            ).fetchone()
            if not kb:
                return False
            
            # Delete knowledge base document associations
            conn.execute(
                "DELETE FROM knowledge_base_documents WHERE knowledge_base_id = ?",
                (kb_id,),
            )
            
            # Delete knowledge base itself
            conn.execute(
                "DELETE FROM knowledge_bases WHERE id = ?",
                (kb_id,),
            )
            conn.commit()
            return True