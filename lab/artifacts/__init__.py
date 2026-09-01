"""Immutable Content-Addressed Artifact Store.

Runs produce large things that should not live inside the event ledger:
    agent trajectories, stdout/stderr, code patches, findings.json,
    evaluation output, benchmark logs, prompt traces, screenshots, test reports.

Store them content-addressed:
    artifacts/
      sha256/
        ab/
          abcdef1234...

Receipt contains:
    {
      "digest": "sha256:...",
      "media_type": "application/json",
      "size_bytes": 18233
    }

Never reference /root/random-output/latest.json as canonical provenance.
Reference immutable digests.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_STORE = str(Path(__file__).parent.parent.parent / "data" / "artifacts")


class ArtifactStore:
    """Content-addressed immutable artifact storage."""

    def __init__(self, store_path: str = ""):
        self.store_path = Path(store_path or DEFAULT_STORE)
        self.store_path.mkdir(parents=True, exist_ok=True)

    def _digest_path(self, digest: str) -> Path:
        """Map sha256:abc123... to store/ab/abc123..."""
        # Remove "sha256:" prefix
        hex_hash = digest.replace("sha256:", "")
        if len(hex_hash) < 4:
            raise ValueError(f"Digest too short: {digest}")
        prefix = hex_hash[:2]
        rest = hex_hash[2:]
        return self.store_path / "sha256" / prefix / rest

    def store(
        self,
        content: bytes,
        media_type: str = "application/octet-stream",
        name: str = "",
    ) -> dict:
        """Store content and return receipt with immutable digest."""
        sha256_hex = hashlib.sha256(content).hexdigest()
        digest = f"sha256:{sha256_hex}"

        dest = self._digest_path(digest)
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

        # Store metadata sidecar
        meta = {
            "digest": digest,
            "media_type": media_type,
            "size_bytes": len(content),
            "name": name,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }
        meta_path = dest.with_suffix(dest.suffix + ".meta.json")
        if not meta_path.exists():
            meta_path.write_text(json.dumps(meta, indent=2))

        return {
            "digest": digest,
            "media_type": media_type,
            "size_bytes": len(content),
            "name": name,
        }

    def store_json(self, data: Any, name: str = "") -> dict:
        """Store JSON-serializable data."""
        content = json.dumps(data, sort_keys=True, indent=2, default=str).encode()
        return self.store(content, media_type="application/json", name=name)

    def store_text(self, text: str, name: str = "", media_type: str = "text/plain") -> dict:
        """Store text content."""
        return self.store(text.encode(), media_type=media_type, name=name)

    def retrieve(self, digest: str) -> bytes | None:
        """Retrieve content by digest. Returns None if not found."""
        path = self._digest_path(digest)
        if path.exists():
            return path.read_bytes()
        return None

    def retrieve_json(self, digest: str) -> Any | None:
        """Retrieve and deserialize JSON content."""
        content = self.retrieve(digest)
        if content is not None:
            return json.loads(content)
        return None

    def exists(self, digest: str) -> bool:
        """Check if artifact exists."""
        return self._digest_path(digest).exists()

    def verify(self, digest: str) -> dict:
        """Verify artifact integrity by recomputing hash."""
        content = self.retrieve(digest)
        if content is None:
            return {"valid": False, "error": "not found"}

        recomputed = "sha256:" + hashlib.sha256(content).hexdigest()
        valid = recomputed == digest
        return {
            "valid": valid,
            "digest": digest,
            "recomputed": recomputed,
            "size_bytes": len(content),
        }

    def list_artifacts(self, limit: int = 100) -> list[dict]:
        """List stored artifacts with metadata."""
        artifacts = []
        meta_files = sorted(
            self.store_path.rglob("*.meta.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for mf in meta_files[:limit]:
            try:
                meta = json.loads(mf.read_text())
                artifacts.append(meta)
            except (json.JSONDecodeError, OSError):
                continue
        return artifacts

    def count(self) -> int:
        """Count total stored artifacts."""
        return sum(1 for _ in self.store_path.rglob("*.meta.json"))

    def clear(self):
        """Remove all artifacts. USE WITH CAUTION."""
        if self.store_path.exists():
            shutil.rmtree(self.store_path)
            self.store_path.mkdir(parents=True, exist_ok=True)
