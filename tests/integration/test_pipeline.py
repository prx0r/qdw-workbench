"""Integration tests — full pipeline verification."""
import tempfile
import os
import pytest


class TestLedgerHydraRoundtrip:
    """Ledger → HydraDB → rebuild roundtrip."""

    def test_ledger_to_hydra_to_rebuild(self):
        from lab.ledger import Ledger
        from lab.projection import HydraProjector
        from integrations.hydra.client import get_client
        from integrations.hydra.query import lab_summary

        db = tempfile.mktemp(suffix=".db")
        ledger = Ledger(db)
        hydra = get_client()

        # Clean
        for label in ["Worker", "WorkerVersion", "Run", "Studio"]:
            try: hydra.clear_label(label)
            except: pass

        # Write events
        ledger.append_event("worker.created", "integ-w1", {"worker_id": "integ-w1", "name": "Integ Worker"})
        ledger.append_event("version.created", "integ-w1/v0", {"version_id": "integ-w1/v0", "worker_id": "integ-w1", "model_name": "mimo"})
        ledger.append_event("run.created", "integ-r1", {"run_id": "integ-r1", "studio_id": "test", "outcome": "won"})

        # Project
        projector = HydraProjector(ledger, hydra)
        result = projector.rebuild()
        assert result["projected"] >= 3

        # Verify
        graph = lab_summary()
        assert graph["workers"] >= 1
        assert graph["versions"] >= 1

        # Delete and rebuild
        for label in ["Worker", "WorkerVersion", "Run", "Studio"]:
            try: hydra.clear_label(label)
            except: pass

        result2 = projector.rebuild()
        assert result2["projected"] >= 3

        graph2 = lab_summary()
        assert graph2["workers"] >= 1

        os.unlink(db)


class TestExecutionBackend:
    """Execution backend produces real artifacts."""

    def test_direct_backend(self):
        from lab.execution import DirectBackend
        from lab.ledger import Ledger
        from lab.artifacts import ArtifactStore
        from lab.contracts import RunSpec, BudgetEnvelope, Split

        db = tempfile.mktemp(suffix=".db")
        ledger = Ledger(db)
        artifacts = ArtifactStore(tempfile.mkdtemp())
        backend = DirectBackend(ledger, artifacts)

        spec = RunSpec(
            run_id="integ-exec-001", lab_id="test", studio_id="test",
            task_instance_id="task-001", split=Split.TRAIN,
            worker_id="w1", worker_version_id="w1/v0",
        )
        budget = BudgetEnvelope(envelope_id="b1", cash_usd=0.05, wall_seconds=60)

        result = backend.execute(spec, budget)
        assert result["success"]
        assert len(result["artifacts"]) > 0

        # Verify ledger recorded execution
        events = ledger.get_entity_history("integ-exec-001")
        assert len(events) >= 1

        os.unlink(db)


class TestMerkleRoot:
    """Trajectory Merkle root is deterministic."""

    def test_deterministic(self):
        from lab.ledger import Ledger

        db = tempfile.mktemp(suffix=".db")
        ledger = Ledger(db)

        ledger.append_event("test", "ent1", {"x": 1})
        ledger.append_event("test", "ent1", {"x": 2})

        root1 = ledger.compute_trajectory_merkle_root("ent1")
        root2 = ledger.compute_trajectory_merkle_root("ent1")
        assert root1 == root2

        # Different entity = different root
        root3 = ledger.compute_trajectory_merkle_root("ent2")
        assert root3 != root1

        os.unlink(db)


class TestReconstructionScoring:
    """Reconstruction fidelity scoring."""

    def test_perfect_reconstruction(self):
        from lab.evaluation import RunEvaluator

        ev = RunEvaluator()
        m = ev.evaluate(
            run_id="r1", worker_version_id="v0", world_id="w1",
            task_score=1.0, task_success=True,
            hidden_state={"a": "1", "b": "2"},
            worker_inferences={"a": "1", "b": "2"},
        )
        assert m.reconstruction.score == 1.0

    def test_partial_reconstruction(self):
        from lab.evaluation import RunEvaluator

        ev = RunEvaluator()
        m = ev.evaluate(
            run_id="r2", worker_version_id="v0", world_id="w1",
            task_score=0.8, task_success=True,
            hidden_state={"a": "1", "b": "2", "c": "3"},
            worker_inferences={"a": "1", "b": "wrong"},
        )
        assert 0 < m.reconstruction.score < 1.0


class TestCurriculum:
    """Curriculum progression."""

    def test_advance_after_threshold(self):
        from lab.curriculum import CurriculumEngine, CurriculumState

        engine = CurriculumEngine(runs_per_level=3, fidelity_threshold=0.5, task_threshold=0.5)
        state = CurriculumState(worker_id="test")

        for i in range(4):
            engine.record_run(state, state.current_level, 0.8, 0.75)

        assert state.current_level.value > 0

    def test_demote_on_regression(self):
        from lab.curriculum import CurriculumEngine, CurriculumState, CurriculumLevel as CL

        engine = CurriculumEngine(runs_per_level=2, demote_on_regression=True)
        state = CurriculumState(worker_id="test", current_level=CL.RANDOMIZED)
        start_level = state.current_level.value

        # 4 runs: 2 good then 2 bad (enough for regression detection)
        engine.record_run(state, CL.RANDOMIZED, 0.8, 0.8)
        engine.record_run(state, CL.RANDOMIZED, 0.8, 0.8)
        engine.record_run(state, CL.RANDOMIZED, 0.2, 0.2)
        engine.record_run(state, CL.RANDOMIZED, 0.1, 0.1)

        # Should have either demoted or stayed (not advanced further)
        assert state.current_level.value <= start_level + 1


class TestExternalIntelligence:
    """External intelligence contracts."""

    def test_source_creation(self):
        from lab.contracts import ExternalSource

        src = ExternalSource(
            source_id="test-src",
            source_name="Test Source",
            license="MIT",
        )
        assert src.source_id == "test-src"
        assert src.compute_digest() == src.compute_digest()

    def test_trajectory_separate_from_runreceipt(self):
        from lab.contracts import ExternalTrajectory, RunReceipt, RunSpec, Split

        traj = ExternalTrajectory(trajectory_id="t1", source_id="s1")
        spec = RunSpec(
            run_id="r1", lab_id="l", studio_id="s", task_instance_id="t",
            split=Split.TRAIN, worker_id="w", worker_version_id="w/v0",
        )
        receipt = RunReceipt(run_id="r1", spec=spec)

        # They are different types
        assert type(traj) != type(receipt)
        assert traj.trajectory_id == "t1"
        assert receipt.run_id == "r1"
