"""Canonical Append-Only Event Ledger.

The single source of truth for what happened. Not Hydra, not SQLite projections.
This ledger is append-only: UPDATE and DELETE are rejected by triggers.

Canonical truth = this ledger + immutable artifacts + Git lineage.
Hydra is a derived projection rebuildable from this ledger.

Event structure:
    event_id       UUIDv7 (time-ordered, unique)
    event_type     e.g. "run.created", "evaluation.completed"
    entity_id      the entity this event concerns
    schema_version contract version
    occurred_at    UTC timestamp
    payload_json   serialized contract
    payload_sha256 digest of payload
    previous_event_hash  chain link (hash of previous event)
    event_hash     hash of this event's fields
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = str(Path(__file__).parent.parent.parent / "data" / "lab-ledger.db")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_event(fields: dict) -> str:
    """SHA-256 of event fields (excluding event_hash itself)."""
    raw = json.dumps(fields, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


class Ledger:
    """Append-only event store. SQLite WAL mode for concurrency."""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or DEFAULT_DB
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                schema_version TEXT NOT NULL DEFAULT '1.0.0',
                occurred_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                previous_event_hash TEXT NOT NULL DEFAULT '',
                event_hash TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_id);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_time ON events(occurred_at);

            -- Triggers: reject UPDATE and DELETE
            CREATE TRIGGER IF NOT EXISTS reject_update
            BEFORE UPDATE ON events
            BEGIN
                SELECT RAISE(ABORT, 'ledger is append-only: UPDATE rejected');
            END;

            CREATE TRIGGER IF NOT EXISTS reject_delete
            BEFORE DELETE ON events
            BEGIN
                SELECT RAISE(ABORT, 'ledger is append-only: DELETE rejected');
            END;
        """)
        conn.commit()
        conn.close()

    # ─── Write ─────────────────────────────────────────────────────────

    def append_event(
        self,
        event_type: str,
        entity_id: str,
        payload: dict,
        schema_version: str = "1.0.0",
        event_id: str = "",
        occurred_at: str = "",
    ) -> dict:
        """Append an event to the ledger. Returns the event record."""
        if not event_id:
            # UUIDv7-like: time-ordered
            event_id = f"evt-{uuid.uuid4().hex[:12]}"
        if not occurred_at:
            occurred_at = _now_utc()

        payload_json = json.dumps(payload, sort_keys=True, default=str)
        payload_sha256 = hashlib.sha256(payload_json.encode()).hexdigest()

        # Get previous event hash for chain linking
        previous_event_hash = self._get_last_event_hash()

        fields = {
            "event_id": event_id,
            "event_type": event_type,
            "entity_id": entity_id,
            "schema_version": schema_version,
            "occurred_at": occurred_at,
            "payload_json": payload_json,
            "payload_sha256": payload_sha256,
            "previous_event_hash": previous_event_hash,
        }
        event_hash = _hash_event(fields)

        conn = self._conn()
        try:
            conn.execute("""
                INSERT INTO events
                (event_id, event_type, entity_id, schema_version, occurred_at,
                 payload_json, payload_sha256, previous_event_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, event_type, entity_id, schema_version, occurred_at,
                  payload_json, payload_sha256, previous_event_hash, event_hash))
            conn.commit()
        finally:
            conn.close()

        return {**fields, "event_hash": event_hash}

    def _get_last_event_hash(self) -> str:
        """Get the event_hash of the most recent event."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT event_hash FROM events ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            return row[0] if row else ""
        finally:
            conn.close()

    # ─── Read ──────────────────────────────────────────────────────────

    def get_event(self, event_id: str) -> dict | None:
        """Get a single event by ID."""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT * FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_entity_history(self, entity_id: str) -> list[dict]:
        """Get all events for an entity, in order."""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM events WHERE entity_id = ? ORDER BY rowid",
                (entity_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_events_by_type(self, event_type: str, limit: int = 100) -> list[dict]:
        """Get events filtered by type."""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM events WHERE event_type = ? ORDER BY rowid DESC LIMIT ?",
                (event_type, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def count_events(self) -> int:
        conn = self._conn()
        try:
            return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        finally:
            conn.close()

    # ─── Verification ──────────────────────────────────────────────────

    def verify_event(self, event_id: str) -> dict:
        """Verify a single event's hash integrity."""
        event = self.get_event(event_id)
        if not event:
            return {"valid": False, "error": "event not found"}

        stored_hash = event.pop("event_hash")
        computed = _hash_event(event)
        valid = stored_hash == computed

        return {
            "valid": valid,
            "event_id": event_id,
            "stored_hash": stored_hash[:16],
            "computed_hash": computed[:16],
        }

    def verify_chain(self) -> dict:
        """Verify the entire chain hash linkage."""
        conn = self._conn()
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT * FROM events ORDER BY rowid").fetchall()
        finally:
            conn.close()

        if not rows:
            return {"valid": True, "events": 0, "broken": []}

        broken = []
        prev_hash = ""
        for i, row in enumerate(rows):
            r = dict(row)
            event_hash = r.pop("event_hash")

            # Check chain link
            if r["previous_event_hash"] != prev_hash:
                broken.append({
                    "index": i,
                    "event_id": r["event_id"],
                    "issue": "chain_link_broken",
                    "expected_prev": prev_hash[:16],
                    "actual_prev": r["previous_event_hash"][:16],
                })

            # Check event hash
            computed = _hash_event(r)
            if event_hash != computed:
                broken.append({
                    "index": i,
                    "event_id": r["event_id"],
                    "issue": "hash_mismatch",
                })

            prev_hash = event_hash

        return {
            "valid": len(broken) == 0,
            "events": len(rows),
            "broken": broken,
        }

    # ─── Export / Import ───────────────────────────────────────────────

    def export_receipt(self, entity_id: str) -> list[dict]:
        """Export all events for an entity as a receipt (for cross-node transfer)."""
        return self.get_entity_history(entity_id)

    def import_receipt(self, events: list[dict]) -> dict:
        """Import events from a receipt. Idempotent.

        Same event_id + same payload → OK (already present).
        Same event_id + different payload → HARD FAILURE.
        """
        imported = 0
        skipped = 0
        errors = []

        for event in events:
            event_id = event.get("event_id", "")
            existing = self.get_event(event_id)

            if existing:
                # Idempotent: same event already present
                if existing.get("payload_sha256") == event.get("payload_sha256"):
                    skipped += 1
                    continue
                else:
                    errors.append({
                        "event_id": event_id,
                        "error": "conflict: same ID, different payload",
                    })
                    continue

            # Append new event
            self.append_event(
                event_type=event["event_type"],
                entity_id=event["entity_id"],
                payload=json.loads(event["payload_json"]),
                schema_version=event.get("schema_version", "1.0.0"),
                event_id=event_id,
                occurred_at=event.get("occurred_at", ""),
            )
            imported += 1

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }

    # ─── Stats ─────────────────────────────────────────────────────────

    def summary(self) -> dict:
        conn = self._conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            types = conn.execute(
                "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type"
            ).fetchall()
            return {
                "total_events": total,
                "by_type": {r[0]: r[1] for r in types},
            }
        finally:
            conn.close()
