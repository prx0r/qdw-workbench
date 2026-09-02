"""Letta Integration — wraps runtime-letta for private-lab.

Runtime-letta runs on localhost:3000.
This module provides the worker agent interface.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

RUNTIME_URL = "http://localhost:3000"


class LettaClient:
    """Client for the Letta runtime service."""

    def __init__(self, base_url: str = RUNTIME_URL):
        self.base_url = base_url

    def health(self) -> dict:
        """Check if Letta runtime is available."""
        try:
            req = urllib.request.Request(f"{self.base_url}/health")
            resp = urllib.request.urlopen(req, timeout=5)
            return {"status": "ok", "response": json.loads(resp.read())}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def create_worker(self, worker_id: str, model: str = "opencode-go/mimo-v2.5",
                      persona: str = "") -> dict:
        """Create or update a worker agent."""
        return self._request("POST", "/workers", {
            "worker_id": worker_id,
            "model": model,
            "persona": persona or "You are a Moltwork worker. Complete tasks precisely.",
        })

    def run_worker(self, worker_id: str, task: str, workspace: str = "",
                   timeout: int = 300, tools: list[str] | None = None) -> dict:
        """Execute a task via a worker agent."""
        return self._request("POST", f"/workers/{worker_id}/run", {
            "task": task,
            "workspace": workspace,
            "timeout": timeout,
            "genome": {"memory_mode": "letta", "max_steps": 4},
            "allowedTools": tools or ["Read", "Write", "Edit", "LS", "Glob", "Grep"],
        }, timeout=timeout + 60)

    def list_workers(self) -> dict:
        """List all worker agents."""
        return self._request("GET", "/workers")

    def _request(self, method: str, path: str, data: dict | None = None,
                 timeout: int = 30) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e), "ok": False}


# Singleton
_client: LettaClient | None = None


def get_letta_client() -> LettaClient:
    global _client
    if _client is None:
        _client = LettaClient()
    return _client


__all__ = ["LettaClient", "get_letta_client"]
