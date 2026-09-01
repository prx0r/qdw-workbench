"""Module Client — HTTP contract between Private Lab and modules.

Modules own their ecosystems. Private Lab should not crawl their filesystem
as the long-term interface.

HTTP contract:
    GET  /v1/module/status
    GET  /v1/programs/{id}
    POST /v1/tasks/materialize
    POST /v1/evaluate
    POST /v1/submit
    GET  /v1/submissions/{id}/outcome

For /bitt:
    Program: bittensor/sn60
    Module: bitt

The bitt_adapter.py reading /root/bitt/... is temporary compatibility.
Long-term: Private Lab → HTTP → /bitt API.

Do not couple the Lab to /root.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lab.contracts import TaskInstance, EvaluationResult, Split
from lab.modules import ModuleStatus, ModuleProgram


class ModuleClient:
    """HTTP client for module APIs."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, data: dict | None = None,
                 timeout: int = 30) -> dict | None:
        """Make HTTP request to module API."""
        if not self.base_url:
            return None

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
        except Exception:
            return None

    def get_status(self) -> ModuleStatus | None:
        """GET /v1/module/status"""
        data = self._request("GET", "/v1/module/status")
        if not data:
            return None
        return ModuleStatus(**data)

    def get_program(self, program_id: str) -> dict | None:
        """GET /v1/programs/{id}"""
        return self._request("GET", f"/v1/programs/{program_id}")

    def materialize_task(self, task_spec: dict) -> TaskInstance | None:
        """POST /v1/tasks/materialize"""
        data = self._request("POST", "/v1/tasks/materialize", task_spec)
        if not data:
            return None
        return TaskInstance(**data)

    def evaluate(self, run_id: str, artifacts: list[str]) -> EvaluationResult | None:
        """POST /v1/evaluate"""
        data = self._request("POST", "/v1/evaluate", {
            "run_id": run_id,
            "artifacts": artifacts,
        })
        if not data:
            return None
        return EvaluationResult(**data)

    def submit(self, run_id: str, artifacts: list[str]) -> dict | None:
        """POST /v1/submit"""
        return self._request("POST", "/v1/submit", {
            "run_id": run_id,
            "artifacts": artifacts,
        })

    def get_outcome(self, submission_id: str) -> dict | None:
        """GET /v1/submissions/{id}/outcome"""
        return self._request("GET", f"/v1/submissions/{submission_id}/outcome")


class BittModuleClient(ModuleClient):
    """Bittensor-specific module client."""

    def __init__(self, base_url: str = "http://localhost:8400"):
        super().__init__(base_url)

    def get_subnet_status(self, subnet_id: int) -> dict | None:
        """Get status for a specific subnet."""
        return self._request("GET", f"/v1/subnets/{subnet_id}/status")

    def get_emissions(self, subnet_id: int) -> dict | None:
        """Get emission data for a subnet."""
        return self._request("GET", f"/v1/subnets/{subnet_id}/emissions")

    def register_miner(self, subnet_id: int, hotkey: str) -> dict | None:
        """Register a miner on a subnet."""
        return self._request("POST", "/v1/miners/register", {
            "subnet_id": subnet_id,
            "hotkey": hotkey,
        })


# ─── Filesystem fallback (temporary compatibility) ────────────────────

class FilesystemModuleAdapter:
    """Read module status from filesystem. TEMPORARY — use HTTP client long-term."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def read_status(self) -> ModuleStatus | None:
        """Read status from filesystem."""
        raise NotImplementedError("Use ModuleClient.get_status() instead")
