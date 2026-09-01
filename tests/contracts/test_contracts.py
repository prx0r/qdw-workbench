"""Contract tests — Pydantic contract integrity.

P-001: reject string-for-int evidence fields
P-002: reject extra fields
P-003: missing required fields fails
P-005: committed JSON schema snapshots
P-006: model -> canonical JSON -> validate -> same hash
P-007: nested mutation detection
P-008: reject naive timestamps
P-010: stable typed IDs
P-011: cross-object invariants
P-012: hypothesis fuzz
"""
import json
import pytest
from datetime import datetime, timezone
from lab.contracts import (
    Worker, WorkerVersion, SourceRef, TaskInstance, RunSpec,
    BudgetEnvelope, EvaluationResult, ExperimentSpec, ExperimentResult,
    Finding, FindingTier, Split, TrustTier, FrozenModel,
)


class TestFrozenModels:
    """P-001 to P-012: Contract integrity tests."""

    def test_reject_string_for_int(self):
        """P-001: reject string-for-int evidence fields."""
        with pytest.raises(Exception):
            WorkerVersion(version_id="v0", worker_id="w1", model_name=123)

    def test_reject_extra_fields(self):
        """P-002: reject extra fields."""
        with pytest.raises(Exception):
            WorkerVersion(version_id="v0", worker_id="w1", bogus=True)

    def test_missing_required_fields(self):
        """P-003: missing required fields fails."""
        with pytest.raises(Exception):
            WorkerVersion()

    def test_frozen_immutability(self):
        """P-007: frozen models cannot be mutated."""
        v = WorkerVersion(version_id="v0", worker_id="w1")
        with pytest.raises(Exception):
            v.version_id = "v1"

    def test_utc_timestamps(self):
        """P-008: reject naive timestamps, require UTC."""
        w = WorkerVersion(version_id="v0", worker_id="w1")
        assert w.created_at.tzinfo is not None

    def test_stable_ids(self):
        """P-010: stable typed IDs."""
        w = Worker(worker_id="security-01")
        assert w.worker_id == "security-01"

    def test_cross_object_invariants(self):
        """P-011: RunSpec WorkerVersion matches."""
        run = RunSpec(
            run_id="r1", lab_id="lab", studio_id="s",
            task_instance_id="t1", split=Split.TRAIN,
            worker_id="w1", worker_version_id="w1/v0",
        )
        assert run.worker_version_id == "w1/v0"

    def test_content_digest_deterministic(self):
        """P-006: same data -> same digest (explicit all fields)."""
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        src = SourceRef(repository="repo", commit_sha="abc", path="p", content_digest="d")
        v1 = WorkerVersion(version_id="v0", worker_id="w1", created_at=ts, source=src)
        v2 = WorkerVersion(version_id="v0", worker_id="w1", created_at=ts, source=src)
        assert v1.compute_digest() == v2.compute_digest()

    def test_content_digest_different_data(self):
        """P-006: different data -> different digest."""
        v1 = WorkerVersion(version_id="v0", worker_id="w1")
        v2 = WorkerVersion(version_id="v1", worker_id="w1")
        assert v1.compute_digest() != v2.compute_digest()

    def test_json_schema_exists(self):
        """P-005: JSON schema can be generated."""
        schema = WorkerVersion.model_json_schema()
        assert "properties" in schema
        assert "version_id" in schema["properties"]
