"""HydraDB queries — read operations over the lab graph.

All queries use MATCH (read-only). Writes go through schema.py CREATE statements.
"""
from __future__ import annotations

from integrations.hydra.client import HydraClient, get_client, hash_id


def _client(c: HydraClient | None = None) -> HydraClient:
    return c or get_client()


# ─── Node reads ───────────────────────────────────────────────────────

def count_workers(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("Worker")

def count_versions(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("WorkerVersion")

def count_runs(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("Run")

def count_studios(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("Studio")

def count_experiments(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("Experiment")

def count_findings(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("Finding")

def count_proposals(client: HydraClient | None = None) -> int:
    return _client(client).count_nodes("LearningProposal")


def lab_summary(client: HydraClient | None = None) -> dict:
    """Get a summary of the entire lab graph."""
    c = _client(client)
    return {
        "workers": c.count_nodes("Worker"),
        "versions": c.count_nodes("WorkerVersion"),
        "runs": c.count_nodes("Run"),
        "studios": c.count_nodes("Studio"),
        "experiments": c.count_nodes("Experiment"),
        "findings": c.count_nodes("Finding"),
        "proposals": c.count_nodes("LearningProposal"),
    }


# ─── Worker queries ───────────────────────────────────────────────────

def get_worker_versions(worker_name: str, client: HydraClient | None = None) -> list[dict]:
    """Get all versions for a worker by name."""
    query = """
        MATCH (w:Worker {name: $name})<-[:HAS_VERSION]-(wv:WorkerVersion)
        RETURN wv.model AS model
    """
    return _client(client).run(query, name=worker_name)


def list_workers(client: HydraClient | None = None) -> list[dict]:
    return _client(client).run("MATCH (w:Worker) RETURN w.name AS name")


# ─── Run queries ──────────────────────────────────────────────────────

def list_runs(client: HydraClient | None = None, limit: int = 100) -> list[dict]:
    return _client(client).run(
        "MATCH (r:Run) RETURN r.outcome AS outcome, r.task_family AS family LIMIT $limit",
        limit=limit
    )


def get_runs_by_studio(studio_name: str, client: HydraClient | None = None) -> list[dict]:
    query = """
        MATCH (r:Run)-[:IN_STUDIO]->(s:Studio {name: $studio})
        RETURN r.outcome AS outcome, r.task_family AS family
    """
    return _client(client).run(query, studio=studio_name)


def get_runs_by_outcome(outcome: str, client: HydraClient | None = None) -> list[dict]:
    query = "MATCH (r:Run {outcome: $outcome}) RETURN r.task_family AS family"
    return _client(client).run(query, outcome=outcome)


# ─── Experiment queries ───────────────────────────────────────────────

def list_experiments(client: HydraClient | None = None) -> list[dict]:
    return _client(client).run(
        "MATCH (e:Experiment) RETURN e.hypothesis AS hypothesis, e.status AS status"
    )


def get_experiment_findings(experiment_id: str, client: HydraClient | None = None) -> list[dict]:
    eid = hash_id(experiment_id)
    query = """
        MATCH (f:Finding)-[:SUPPORTED_BY]->(e:Experiment {id: $eid})
        RETURN f.claim AS claim, f.tier AS tier
    """
    return _client(client).run(query, eid=eid)


# ─── Finding queries ──────────────────────────────────────────────────

def list_findings(client: HydraClient | None = None) -> list[dict]:
    return _client(client).run(
        "MATCH (f:Finding) RETURN f.claim AS claim, f.tier AS tier"
    )


def get_findings_by_tier(tier: str, client: HydraClient | None = None) -> list[dict]:
    query = "MATCH (f:Finding {tier: $tier}) RETURN f.claim AS claim"
    return _client(client).run(query, tier=tier)


# ─── Cross-entity traversals ──────────────────────────────────────────

def finding_to_studio(client: HydraClient | None = None) -> list[dict]:
    """Finding -> Experiment -> Studio chain."""
    return _client(client).run("""
        MATCH (f:Finding)-[:SUPPORTED_BY]->(e:Experiment)-[:IN_STUDIO]->(s:Studio)
        RETURN f.claim AS claim, e.hypothesis AS hypothesis, s.name AS studio
    """)


def studio_stats(studio_name: str, client: HydraClient | None = None) -> dict:
    """Get stats for a studio."""
    c = _client(client)
    runs = c.run(
        "MATCH (r:Run)-[:IN_STUDIO]->(s:Studio {name: $name}) RETURN count(*) AS count",
        name=studio_name
    )
    exps = c.run(
        "MATCH (e:Experiment)-[:IN_STUDIO]->(s:Studio {name: $name}) RETURN count(*) AS count",
        name=studio_name
    )
    findings = c.run("""
        MATCH (f:Finding)-[:SUPPORTED_BY]->(e:Experiment)-[:IN_STUDIO]->(s:Studio {name: $name})
        RETURN count(*) AS count
    """, name=studio_name)
    return {
        "studio": studio_name,
        "runs": runs[0]["count"] if runs else 0,
        "experiments": exps[0]["count"] if exps else 0,
        "findings": findings[0]["count"] if findings else 0,
    }


def learning_chain(client: HydraClient | None = None) -> list[dict]:
    """Proposal -> Version -> Worker chain."""
    return _client(client).run("""
        MATCH (p:LearningProposal)-[:CREATED]->(wv:WorkerVersion)
        RETURN p.hypothesis AS hypothesis, wv.model AS model
    """)


def win_rate_by_studio(client: HydraClient | None = None) -> list[dict]:
    """Win rate per studio."""
    # First get all runs with studios
    runs = _client(client).run("""
        MATCH (r:Run)-[:IN_STUDIO]->(s:Studio)
        RETURN s.name AS studio, r.outcome AS outcome
    """)
    # Aggregate in Python (HydraDB doesn't support CASE WHEN)
    stats: dict[str, dict] = {}
    for r in runs:
        studio = r["studio"]
        if studio not in stats:
            stats[studio] = {"total": 0, "won": 0}
        stats[studio]["total"] += 1
        if r["outcome"] == "won":
            stats[studio]["won"] += 1
    return [{"studio": k, **v} for k, v in stats.items()]
