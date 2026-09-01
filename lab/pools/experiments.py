"""Experiment tracking — CGE experiments in HydraDB.

Experiments are controlled comparisons between WorkerVersions.
They require a predeclared hypothesis and comparison.
"""
from __future__ import annotations
import time
from typing import Any
from integrations.hydra import get_client, hash_id


def create_experiment(
    experiment_id: str,
    hypothesis: str,
    control_version: str,
    candidate_version: str,
    studio_id: str = "",
    task_family: str = "",
    n_tasks: int = 0,
) -> dict:
    """Create an experiment in HydraDB."""
    client = get_client()
    eid = hash_id(experiment_id)
    cv = hash_id(control_version)
    candv = hash_id(candidate_version)

    props = {
        "id": eid,
        "experiment_id": experiment_id,
        "hypothesis": hypothesis,
        "control_version": control_version,
        "candidate_version": candidate_version,
        "status": "DESIGNED",
        "studio_id": studio_id,
        "task_family": task_family,
        "n_tasks": n_tasks,
    }

    # Create Experiment node
    p_str = ", ".join(f"{k}: ${k}" for k in props)
    client.run_write(
        f"CREATE (e:Experiment {{{p_str}}})-[:_SELF]->(e2:Experiment {{id: $id}})",
        **props
    )
    client.run_write(
        "MATCH (e:Experiment {id: $id})-[r:_SELF]->() DELETE r", id=eid
    )

    # Create version nodes
    for vid, label in [(cv, control_version), (candv, candidate_version)]:
        client.run_write(
            f"CREATE (v:WorkerVersion {{id: $vid, version: $version}})-[:_SELF]->(v2:WorkerVersion {{id: $vid}})",
            vid=vid, version=label
        )
        client.run_write(
            "MATCH (v:WorkerVersion {id: $vid})-[r:_SELF]->() DELETE r", vid=vid
        )

    # Link experiment to versions
    client.run_write(
        "MATCH (e:Experiment {id: $eid}), (c:WorkerVersion {id: $cv}) "
        "CREATE (e)-[:CONTROLLED_BY]->(c)",
        eid=eid, cv=cv
    )
    client.run_write(
        "MATCH (e:Experiment {id: $eid}), (c:WorkerVersion {id: $cv}) "
        "CREATE (e)-[:CANDIDATE]->(c)",
        eid=eid, cv=candv
    )

    return {"experiment_id": experiment_id, "eid": eid}


def record_experiment_result(
    experiment_id: str,
    control_score: float,
    candidate_score: float,
    quality_delta: float,
    cost_delta: float = 0.0,
    promoted: bool = False,
    reason: str = "",
) -> dict:
    """Record experiment results in HydraDB."""
    client = get_client()
    eid = hash_id(experiment_id)

    # Update experiment status
    status = "SUPPORTED" if promoted else "REFUTED"
    client.run_write(
        "MATCH (e:Experiment {id: $id}) "
        "SET e.status = $status, e.control_score = $control_score, "
        "e.candidate_score = $candidate_score, e.quality_delta = $quality_delta, "
        "e.cost_delta = $cost_delta, e.promoted = $promoted, e.reason = $reason",
        id=eid, status=status,
        control_score=control_score, candidate_score=candidate_score,
        quality_delta=quality_delta, cost_delta=cost_delta,
        promoted=promoted, reason=reason
    )

    return {"experiment_id": experiment_id, "status": status, "promoted": promoted}


def list_experiments(status: str | None = None) -> list[dict]:
    """List experiments, optionally filtered by status."""
    client = get_client()
    if status:
        return client.run(
            "MATCH (e:Experiment {status: $status}) "
            "RETURN e.experiment_id AS id, e.hypothesis AS hypothesis, "
            "e.status AS status, e.quality_delta AS delta",
            status=status
        )
    else:
        return client.run(
            "MATCH (e:Experiment) "
            "RETURN e.experiment_id AS id, e.hypothesis AS hypothesis, "
            "e.status AS status, e.quality_delta AS delta"
        )


def get_experiment_stats() -> dict:
    """Get experiment statistics."""
    client = get_client()
    results = client.run(
        "MATCH (e:Experiment) RETURN e.status AS status, count(*) AS count"
    )
    stats = {r["status"]: r["count"] for r in results}

    total = sum(stats.values())
    supported = stats.get("SUPPORTED", 0)
    return {
        "total": total,
        "by_status": stats,
        "promotion_rate": supported / max(1, total),
    }
