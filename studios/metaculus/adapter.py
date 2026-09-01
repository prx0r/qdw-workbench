"""Metaculus Studio — domain adapter for forecasting.

From spec §19: Supplies historical questions, resolution criteria,
point-in-time evidence packets, known resolutions, proper scoring rule,
live question adapter.
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any

from lab.contracts import (
    TaskInstance, Split, RunSpec, RunReceipt, EvaluationResult,
    StudioManifest, ExternalSubmissionReceipt, ExternalOutcomeReceipt,
)


METACULUS_API = "https://www.metaculus.com/api2"


class MetaculusClient:
    """Thin client for Metaculus API."""

    def __init__(self, token: str = ""):
        self.token = token or os.environ.get("METACULUS_API_KEY", "")
        self._headers = {
            "Authorization": f"Token {self.token}",
            "Accept": "application/json",
            "User-Agent": "MoltworkPrivateLab/0.1",
        }

    def _get(self, path: str, params: dict = None) -> dict | None:
        url = f"{METACULUS_API}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v)
            if query:
                url += f"?{query}"
        try:
            req = urllib.request.Request(url, headers=self._headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, data: dict) -> dict | None:
        url = f"{METACULUS_API}{path}"
        body = json.dumps(data).encode()
        try:
            req = urllib.request.Request(url, data=body, headers={
                **self._headers, "Content-Type": "application/json"
            }, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception as e:
            return {"error": str(e)}

    def list_questions(self, status: str = "open", qtype: str = "binary",
                       limit: int = 50) -> list[dict]:
        data = self._get("/questions/", {"status": status, "type": qtype, "limit": limit})
        return data.get("results", []) if data else []

    def get_question(self, question_id: int) -> dict | None:
        return self._get(f"/questions/{question_id}/")

    def submit_forecast(self, question_id: int, probability: float) -> dict | None:
        return self._post(f"/questions/{question_id}/forecast/", {
            "probability": max(0.01, min(0.99, probability)),
        })


class MetaculusStudio:
    """Studio adapter for Metaculus forecasting."""

    def __init__(self):
        self.client = MetaculusClient()

    def manifest(self) -> StudioManifest:
        return StudioManifest(
            studio_id="metaculus",
            name="Metaculus Forecasting",
            task_families=["forecasting.binary", "forecasting.numeric"],
            evaluator_versions=["brier-v1", "log-score-v1"],
            modes=["REPLAY", "SECRET", "LIVE"],
        )

    def get_task(self, split: Split, seed: int | None = None) -> TaskInstance:
        """Get a historical question for the specified split."""
        # In production: fetch from local dataset of resolved questions
        # For now: fetch open questions from API
        questions = self.client.list_questions(status="open", limit=10)
        if not questions:
            return TaskInstance(
                task_id="empty", studio_id="metaculus",
                task_family="forecasting.binary", split=split,
            )
        q = questions[0]
        return TaskInstance(
            task_id=f"mc:{q['id']}",
            studio_id="metaculus",
            task_family="forecasting.binary",
            split=split,
            seed=seed,
            content={
                "question_id": q["id"],
                "title": q.get("title", ""),
                "description": q.get("description", "")[:1000],
                "close_time": q.get("scheduled_close_time"),
                "resolve_time": q.get("scheduled_resolve_time"),
            },
            evaluation_data={
                "resolution": q.get("question", {}).get("resolution"),
                "community_prediction": None,  # hidden from worker
            },
        )

    def evaluate(self, run: RunReceipt, task: TaskInstance) -> EvaluationResult:
        """Score forecast against resolution (Brier score)."""
        # For REPLAY: score against known resolution
        # For LIVE: score will come later when question resolves
        resolution = task.evaluation_data.get("resolution")
        if resolution is None:
            return EvaluationResult(
                result_id=f"eval:{run.run_id}",
                run_id=run.run_id,
                success=True,
                scores={"status": "pending_resolution"},
                overall_score=0.0,
            )

        # Get worker's forecast from trajectory
        # For now: placeholder
        forecast = 0.5
        resolution_value = 1.0 if resolution == "yes" else 0.0
        brier = (forecast - resolution_value) ** 2

        return EvaluationResult(
            result_id=f"eval:{run.run_id}",
            run_id=run.run_id,
            success=True,
            scores={
                "brier": brier,
                "log_score": -abs(forecast - resolution_value),
                "calibration_error": abs(forecast - resolution_value),
            },
            overall_score=1.0 - brier,  # higher is better
        )

    def observe_external_outcome(self, submission_id: str) -> ExternalOutcomeReceipt | None:
        """Check if a submitted forecast has been scored."""
        # In production: check Metaculus API for resolution
        return None

    def submit_forecast(self, question_id: int, probability: float) -> ExternalSubmissionReceipt:
        """Submit a forecast to Metaculus."""
        result = self.client.submit_forecast(question_id, probability)
        return ExternalSubmissionReceipt(
            submission_id=f"mc-sub:{question_id}",
            venue="metaculus",
            external_id=str(question_id),
        )

    def curriculum_features(self, run: RunReceipt) -> dict:
        """Extract features for CGE curriculum generation."""
        return {
            "studio": "metaculus",
            "task_family": "forecasting.binary",
            "brier_score": run.evaluation_result_id,  # placeholder
            "cost_usd": sum(
                e.get("amount", 0) for e in run.cost_events
                if e.get("dimension") == "actual_cash"
            ),
        }
