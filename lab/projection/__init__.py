"""Hydra Projector — reads ledger events, creates graph projections in HydraDB.

Hydra is NOT canonical truth. It's a derived projection.
If destroying Hydra loses knowledge, the architecture is wrong.

Canonical truth:
    - append-only event ledger
    - immutable artifacts
    - Git source/version lineage

Hydra is:
    - search/index layer
    - relationship graph
    - experience projection
    - transfer graph
    - dashboard query substrate

Critical test:
    1. Run experiment.
    2. Verify UI.
    3. Delete Hydra graph.
    4. Rebuild Hydra from ledger.
    5. Compare resulting graph.
    Counts and lineage must match.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lab.ledger import Ledger
from integrations.hydra.client import HydraClient, get_client, hash_id


class HydraProjector:
    """Projects ledger events into HydraDB graph nodes and edges."""

    def __init__(self, ledger: Ledger, hydra: HydraClient | None = None):
        self.ledger = ledger
        self.hydra = hydra or get_client()

    # ─── Core projection ──────────────────────────────────────────────

    def project_worker_created(self, event: dict):
        """Project worker.created event to Hydra graph."""
        payload = json.loads(event["payload_json"])
        worker_id = payload.get("worker_id", event["entity_id"])
        name = payload.get("name", worker_id)
        self.hydra.create_worker_with_version(
            worker_id=worker_id, worker_name=name,
            version_id=f"{worker_id}/init", model=""
        )

    def project_version_created(self, event: dict):
        """Project version.created event to Hydra graph."""
        payload = json.loads(event["payload_json"])
        vid = payload.get("version_id", event["entity_id"])
        wid = payload.get("worker_id", "")
        model = payload.get("model_name", payload.get("model", ""))
        self.hydra.create_worker_with_version(
            worker_id=wid, worker_name=wid,
            version_id=vid, model=model,
        )

    def project_run_created(self, event: dict):
        """Project run.created event to Hydra graph."""
        payload = json.loads(event["payload_json"])
        run_id = payload.get("run_id", event["entity_id"])
        studio_id = payload.get("studio_id", "unknown")
        version_id = payload.get("worker_version_id", payload.get("version_id", "unknown"))
        outcome = payload.get("outcome", "pending")
        self.hydra.create_run(
            run_id=run_id, version_id=version_id,
            studio_id=studio_id, outcome=outcome,
        )

    def project_experiment_created(self, event: dict):
        """Project experiment.created event to Hydra graph."""
        payload = json.loads(event["payload_json"])
        exp_id = payload.get("experiment_id", event["entity_id"])
        hypothesis = payload.get("hypothesis", "")
        self.hydra.create_experiment(
            experiment_id=exp_id, hypothesis=hypothesis,
        )

    def project_finding_created(self, event: dict):
        """Project finding.created event to Hydra graph."""
        payload = json.loads(event["payload_json"])
        fid = payload.get("finding_id", event["entity_id"])
        claim = payload.get("claim", "")
        tier = payload.get("tier", "OBSERVATION")
        exp_id = payload.get("experiment_id", "")
        self.hydra.create_finding(
            finding_id=fid, experiment_id=exp_id or "none",
            claim=claim, tier=tier,
        )

    def project_evaluation_completed(self, event: dict):
        """Project evaluation.completed — update run outcome."""
        payload = json.loads(event["payload_json"])
        run_id = payload.get("run_id", "")
        success = payload.get("success", False)
        outcome = "won" if success else "lost"
        # Update run outcome via new event (immutable ledger)
        self.ledger.append_event(
            event_type="run.outcome_recorded",
            entity_id=run_id,
            payload={"run_id": run_id, "outcome": outcome},
        )

    def project_promotion(self, event: dict):
        """Project promotion event to Hydra."""
        payload = json.loads(event["payload_json"])
        candidate = payload.get("candidate", "")
        self.hydra.create_learning_proposal(
            proposal_id=f"promo-{candidate}",
            version_id=candidate,
            hypothesis=payload.get("reason", "promoted"),
        )

    # ─── Dispatch table ───────────────────────────────────────────────

    EVENT_PROJECTORS = {
        "worker.created": "project_worker_created",
        "version.created": "project_version_created",
        "run.created": "project_run_created",
        "experiment.created": "project_experiment_created",
        "finding.created": "project_finding_created",
        "evaluation.completed": "project_evaluation_completed",
        "promotion.created": "project_promotion",
    }

    def project_event(self, event: dict) -> bool:
        """Project a single event. Returns True if handled."""
        event_type = event.get("event_type", "")
        method_name = self.EVENT_PROJECTORS.get(event_type)
        if method_name:
            method = getattr(self, method_name)
            method(event)
            return True
        return False

    # ─── Rebuild ──────────────────────────────────────────────────────

    def rebuild(self) -> dict:
        """Delete Hydra graph and rebuild from ledger.

        This is the critical correctness test:
        Hydra must be completely reconstructable from the ledger.
        """
        # Clear all graph data
        self.hydra.clear_all()

        # Get all events in order
        conn = self.ledger._conn()
        conn.row_factory = __import__("sqlite3").Row
        try:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY rowid"
            ).fetchall()
        finally:
            conn.close()

        projected = 0
        skipped = 0
        errors = []

        for row in rows:
            event = dict(row)
            try:
                if self.project_event(event):
                    projected += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append({
                    "event_id": event["event_id"],
                    "event_type": event["event_type"],
                    "error": str(e),
                })

        return {
            "total_events": len(rows),
            "projected": projected,
            "skipped": skipped,
            "errors": errors,
        }

    def verify(self) -> dict:
        """Verify Hydra graph matches ledger state."""
        from integrations.hydra.query import lab_summary

        graph = lab_summary(self.hydra)
        ledger_events = self.ledger.summary()

        return {
            "graph": graph,
            "ledger_events": ledger_events["total_events"],
            "ledger_types": ledger_events["by_type"],
        }
