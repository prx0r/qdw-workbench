"""HydraDB integration — the shared lab graph database.

Any client (desktop or VPS) connects to the same HydraDB instance.
This is the canonical store for all lab entities and relationships.

Two orthogonal axes:
    CapabilityPool: what domain (security, forecasting, coding)
    Venue: where you compete (bittensor/sn60, immunefi, metaculus)

A run belongs to ONE venue and ONE or MORE capability pools.

Connection:
    bolt://localhost:7687 (local) or bolt://<host>:7687 (remote)
    Auth: neo4j / private-lab-hydradb-token-2026-secure
"""
from integrations.hydra.client import HydraClient, get_client, close_client, hash_id
from integrations.hydra.schema import (
    create_worker, create_run, create_experiment,
    create_finding, create_learning_proposal,
    create_pool, create_venue, create_pool_venue,
    create_worker_in_pool, create_run_at_venue, create_finding_in_pool,
)
from integrations.hydra.query import (
    lab_summary, list_workers, list_runs, list_experiments, list_findings,
    count_workers, count_runs, count_experiments, count_findings,
    finding_to_studio, studio_stats, learning_chain, win_rate_by_studio,
    list_pools, get_pool_venues, get_pool_workers, get_pool_findings,
    get_pool_runs, get_pool_stats, get_transferred_findings,
    get_pool_win_rate, pool_summary,
)

__all__ = [
    "HydraClient", "get_client", "close_client", "hash_id",
    "create_worker", "create_run", "create_experiment",
    "create_finding", "create_learning_proposal",
    "create_pool", "create_venue", "create_pool_venue",
    "create_worker_in_pool", "create_run_at_venue", "create_finding_in_pool",
    "lab_summary", "list_workers", "list_runs", "list_experiments", "list_findings",
    "count_workers", "count_runs", "count_experiments", "count_findings",
    "finding_to_studio", "studio_stats", "learning_chain", "win_rate_by_studio",
    "list_pools", "get_pool_venues", "get_pool_workers", "get_pool_findings",
    "get_pool_runs", "get_pool_stats", "get_transferred_findings",
    "get_pool_win_rate", "pool_summary",
]
