"""HydraDB integration — the shared lab graph database.

Any client (desktop or VPS) connects to the same HydraDB instance.
This is the canonical store for all lab entities and relationships.

Connection:
    bolt://localhost:7687 (local) or bolt://<host>:7687 (remote)
    Auth: neo4j / private-lab-hydradb-token-2026-secure

Write pattern (HydraDB only supports CREATE with edge patterns):
    from integrations.hydra import create_worker, create_run, create_experiment

    create_worker(worker_id="r1", name="Agent", version_id="v1", model="mimo")
    create_run(run_id="r1", studio_id="metaculus", outcome="won")

Read pattern (MATCH traversals):
    from integrations.hydra import lab_summary, finding_to_studio

    lab_summary()
    finding_to_studio()
"""
from integrations.hydra.client import HydraClient, get_client, close_client, hash_id
from integrations.hydra.schema import (
    create_worker, create_run, create_experiment,
    create_finding, create_learning_proposal,
)
from integrations.hydra.query import (
    lab_summary, list_workers, list_runs, list_experiments, list_findings,
    count_workers, count_runs, count_experiments, count_findings,
    finding_to_studio, studio_stats, learning_chain, win_rate_by_studio,
)

__all__ = [
    "HydraClient", "get_client", "close_client", "hash_id",
    "create_worker", "create_run", "create_experiment",
    "create_finding", "create_learning_proposal",
    "lab_summary", "list_workers", "list_runs", "list_experiments", "list_findings",
    "count_workers", "count_runs", "count_experiments", "count_findings",
    "finding_to_studio", "studio_stats", "learning_chain", "win_rate_by_studio",
]
