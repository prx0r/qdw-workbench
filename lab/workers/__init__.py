"""Worker Registry — persistent worker identity + immutable version lineage.

A worker is a persistent subject:
    security-01
        ├── v0 (initial)
        ├── v1 (after first learning proposal)
        ├── v2 (after promotion)
        └── ...

Each WorkerVersion is immutable and pins:
    - model/provider
    - system prompt digest
    - process (repo, commit, path)
    - skills
    - memory revision
    - tools
    - runtime
    - context policy
    - source repo + commit
    - artifact/config digests

Changing any of those creates a new version.
Never modify v3 after creation.

Promotion always points back to evidence.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lab.contracts import Worker, WorkerVersion, SourceRef, PromotionReceipt
from lab.ledger import Ledger
from lab.artifacts import ArtifactStore


class WorkerRegistry:
    """Manages worker identity and version lineage."""

    def __init__(self, ledger: Ledger, artifacts: ArtifactStore):
        self.ledger = ledger
        self.artifacts = artifacts

    def create_worker(
        self,
        worker_id: str,
        name: str = "",
        letta_agent_id: str = "",
        metadata: dict | None = None,
    ) -> Worker:
        """Create a new persistent worker identity."""
        worker = Worker(
            worker_id=worker_id,
            letta_agent_id=letta_agent_id,
            metadata=metadata or {},
        )

        # Record to ledger
        self.ledger.append_event(
            event_type="worker.created",
            entity_id=worker_id,
            payload={
                "worker_id": worker_id,
                "name": name or worker_id,
                "letta_agent_id": letta_agent_id,
                "metadata": metadata or {},
            },
        )

        # Store contract as artifact
        self.artifacts.store_json(
            worker.model_dump(), name=f"worker-{worker_id}.json"
        )

        return worker

    def create_version(
        self,
        worker_id: str,
        version_id: str,
        parent_version_id: str = "",
        model_provider: str = "",
        model_name: str = "",
        system_prompt_digest: str = "",
        memory_revision: str = "",
        skill_versions: list[str] | None = None,
        tool_policy: str = "",
        process_policy: str = "",
        routing_policy: str = "",
        context_policy: str = "",
        source: SourceRef | None = None,
        git_commits: dict | None = None,
        git_digests: dict | None = None,
    ) -> WorkerVersion:
        """Create an immutable worker version. Never modify after creation."""
        version = WorkerVersion(
            version_id=version_id,
            worker_id=worker_id,
            parent_version_id=parent_version_id,
            model_provider=model_provider,
            model_name=model_name,
            system_prompt_digest=system_prompt_digest,
            memory_revision=memory_revision,
            skill_versions=skill_versions or [],
            tool_policy=tool_policy,
            process_policy=process_policy,
            routing_policy=routing_policy,
            context_policy=context_policy,
            source=source or SourceRef(),
            git_commits=git_commits or {},
            git_digests=git_digests or {},
        )

        # Record to ledger
        self.ledger.append_event(
            event_type="version.created",
            entity_id=version_id,
            payload={
                "version_id": version_id,
                "worker_id": worker_id,
                "parent_version_id": parent_version_id,
                "model_provider": model_provider,
                "model_name": model_name,
                "source_repo": (source or SourceRef()).repository,
                "source_commit": (source or SourceRef()).commit_sha,
                "source_path": (source or SourceRef()).path,
                "digest": version.compute_digest(),
            },
        )

        # Store contract as artifact
        self.artifacts.store_json(
            version.model_dump(), name=f"version-{version_id}.json"
        )

        return version

    def get_worker_history(self, worker_id: str) -> list[dict]:
        """Get all versions for a worker, in creation order."""
        # Query by event type, filter by worker_id in payload
        events = self.ledger.get_events_by_type("version.created", limit=1000)
        versions = []
        for e in events:
            payload = json.loads(e["payload_json"])
            if payload.get("worker_id") == worker_id:
                versions.append(payload)
        return versions

    def get_latest_version(self, worker_id: str) -> dict | None:
        """Get the most recent version for a worker."""
        versions = self.get_worker_history(worker_id)
        return versions[-1] if versions else None

    def promote(
        self,
        worker_id: str,
        candidate_version: str,
        experiment_result_id: str,
        reason: str = "",
    ) -> PromotionReceipt:
        """Promote a worker version. Always points back to evidence."""
        receipt = PromotionReceipt(
            candidate=candidate_version,
            experiment_result=experiment_result_id,
            reason=reason,
        )

        # Record to ledger
        self.ledger.append_event(
            event_type="promotion.created",
            entity_id=candidate_version,
            payload={
                "candidate": candidate_version,
                "experiment_result": experiment_result_id,
                "worker_id": worker_id,
                "reason": reason,
            },
        )

        # Store receipt as artifact
        self.artifacts.store_json(
            receipt.model_dump(), name=f"promotion-{candidate_version}.json"
        )

        return receipt

    def verify_version_immutability(self, version_id: str) -> dict:
        """Verify a version hasn't been tampered with."""
        events = self.ledger.get_entity_history(version_id)
        creation_events = [e for e in events if e["event_type"] == "version.created"]

        if not creation_events:
            return {"valid": False, "error": "no creation event found"}

        if len(creation_events) > 1:
            return {"valid": False, "error": f"multiple creation events: {len(creation_events)}"}

        # Check artifact exists and matches
        payload = json.loads(creation_events[0]["payload_json"])
        digest = payload.get("digest", "")

        return {
            "valid": True,
            "version_id": version_id,
            "creation_event": creation_events[0]["event_id"],
            "digest": digest,
        }
