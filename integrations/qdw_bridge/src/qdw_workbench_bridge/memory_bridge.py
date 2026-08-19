"""QDW Memory Bridge — feeds QDW events into memory-installer's storage layer.

Listens for QDW ledger events and stores them as memory entries
for cross-session recall.
"""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MEMORY_DB = Path.home() / ".local/share/qdw-workbench/memory.db"


def _ensure_db() -> sqlite3.Connection:
    MEMORY_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(MEMORY_DB))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            source TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT,
            created_at TEXT NOT NULL,
            embedding_text TEXT
        )
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory_entries(kind)
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at)
    """)
    return con


def store_event(kind: str, source: str, content: str, metadata: dict | None = None) -> int:
    """Store a QDW event as a memory entry."""
    con = _ensure_db()
    now = datetime.now(timezone.utc).isoformat()
    cur = con.execute(
        "INSERT INTO memory_entries (kind, source, content, metadata_json, created_at, embedding_text) VALUES (?, ?, ?, ?, ?, ?)",
        (kind, source, content, json.dumps(metadata) if metadata else None, now, content),
    )
    con.commit()
    entry_id = cur.lastrowid
    con.close()
    return entry_id


def store_handover(handover: dict[str, Any]) -> int:
    """Store a handover as a memory entry for cross-session recall."""
    body = handover.get("body", "")
    metadata = {
        "session_id": handover.get("source_session_id"),
        "runtime": handover.get("runtime_id"),
        "model": handover.get("model_id"),
        "git": handover.get("git"),
        "context_used": handover.get("context_used_tokens"),
        "context_max": handover.get("context_max_tokens"),
    }
    return store_event("handover", "qdw-node", body, metadata)


def store_product_event(product: dict[str, Any]) -> int:
    """Store a product update as a memory entry."""
    return store_event(
        "product",
        "qdw-bridge",
        f"Product {product.get('name', 'unknown')} status: {product.get('status', 'unknown')}",
        product,
    )


def store_approval(action_id: str, decision: str, comment: str) -> int:
    """Store a human approval as a memory entry."""
    return store_event(
        "approval",
        "qdw-bridge",
        f"Human {decision} action {action_id}: {comment}",
        {"action_id": action_id, "decision": decision, "comment": comment},
    )


def search_memory(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Simple text search over memory entries."""
    con = _ensure_db()
    rows = con.execute(
        "SELECT id, kind, source, content, metadata_json, created_at FROM memory_entries WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
        (f"%{query}%", limit),
    ).fetchall()
    con.close()
    return [
        {
            "id": r[0],
            "kind": r[1],
            "source": r[2],
            "content": r[3],
            "metadata": json.loads(r[4]) if r[4] else None,
            "created_at": r[5],
        }
        for r in rows
    ]


def get_recent_memory(kind: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Get recent memory entries, optionally filtered by kind."""
    con = _ensure_db()
    if kind:
        rows = con.execute(
            "SELECT id, kind, source, content, metadata_json, created_at FROM memory_entries WHERE kind = ? ORDER BY created_at DESC LIMIT ?",
            (kind, limit),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT id, kind, source, content, metadata_json, created_at FROM memory_entries ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    con.close()
    return [
        {
            "id": r[0],
            "kind": r[1],
            "source": r[2],
            "content": r[3],
            "metadata": json.loads(r[4]) if r[4] else None,
            "created_at": r[5],
        }
        for r in rows
    ]
