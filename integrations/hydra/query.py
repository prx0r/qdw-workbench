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


# ─── Pool-based queries ───────────────────────────────────────────────

def list_pools(client: HydraClient | None = None) -> list[dict]:
    """List all capability pools."""
    return _client(client).run("MATCH (pool:CapabilityPool) RETURN pool.name AS name")


def get_pool_venues(pool_name: str, client: HydraClient | None = None) -> list[dict]:
    """Get all venues for a pool."""
    return _client(client).run("""
        MATCH (pool:CapabilityPool {name: $pool})-[:HAS_VENUE]->(v:Venue)
        RETURN v.name AS venue, v.protocol AS protocol
    """, pool=pool_name)


def get_pool_workers(pool_name: str, client: HydraClient | None = None) -> list[dict]:
    """Get all workers in a pool."""
    return _client(client).run("""
        MATCH (w:Worker)-[:MEMBER_OF]->(pool:CapabilityPool {name: $pool})
        RETURN w.name AS worker
    """, pool=pool_name)


def get_pool_findings(pool_name: str, client: HydraClient | None = None) -> list[dict]:
    """Get all findings for a pool."""
    return _client(client).run("""
        MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool})
        RETURN f.claim AS claim, f.tier AS tier, f.confidence AS confidence
    """, pool=pool_name)


def get_pool_runs(pool_name: str, client: HydraClient | None = None) -> list[dict]:
    """Get all runs contributing to a pool."""
    return _client(client).run("""
        MATCH (r:Run)-[:CONTRIBUTES_TO]->(pool:CapabilityPool {name: $pool})
        RETURN r.outcome AS outcome, r.studio AS studio
    """, pool=pool_name)


def get_pool_findings_by_tier(pool_name: str, tier: str, client: HydraClient | None = None) -> list[dict]:
    """Get findings in a pool filtered by tier."""
    return _client(client).run("""
        MATCH (f:Finding {tier: $tier})-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool})
        RETURN f.claim AS claim, f.confidence AS confidence
    """, pool=pool_name, tier=tier)


def get_pool_stats(pool_name: str, client: HydraClient | None = None) -> dict:
    """Get stats for a pool: runs, findings, workers, venues."""
    c = _client(client)
    runs = c.run("""
        MATCH (r:Run)-[:CONTRIBUTES_TO]->(pool:CapabilityPool {name: $pool})
        RETURN count(*) AS count
    """, pool=pool_name)
    findings = c.run("""
        MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool})
        RETURN count(*) AS count
    """, pool=pool_name)
    workers = c.run("""
        MATCH (w:Worker)-[:MEMBER_OF]->(pool:CapabilityPool {name: $pool})
        RETURN count(*) AS count
    """, pool=pool_name)
    venues = c.run("""
        MATCH (pool:CapabilityPool {name: $pool})-[:HAS_VENUE]->(v:Venue)
        RETURN count(*) AS count
    """, pool=pool_name)
    return {
        "pool": pool_name,
        "runs": runs[0]["count"] if runs else 0,
        "findings": findings[0]["count"] if findings else 0,
        "workers": workers[0]["count"] if workers else 0,
        "venues": venues[0]["count"] if venues else 0,
    }


def get_transferred_findings(client: HydraClient | None = None) -> list[dict]:
    """Findings that have been transferred across venues."""
    return _client(client).run("""
        MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool)
        WHERE f.tier = 'TRANSFER_CLAIM' OR f.tier = 'DOCTRINE'
        RETURN f.claim AS claim, f.tier AS tier, pool.name AS pool,
               f.valid_in AS valid_in, f.transferred_to AS transferred_to
    """)


def get_pool_win_rate(pool_name: str, client: HydraClient | None = None) -> list[dict]:
    """Win rate per venue within a pool."""
    runs = _client(client).run("""
        MATCH (r:Run)-[:EXECUTED_AT]->(v:Venue)-[:HAS_VENUE]-(pool:CapabilityPool {name: $pool})
        RETURN v.name AS venue, r.outcome AS outcome
    """, pool=pool_name)
    stats: dict[str, dict] = {}
    for r in runs:
        venue = r["venue"]
        if venue not in stats:
            stats[venue] = {"total": 0, "won": 0}
        stats[venue]["total"] += 1
        if r["outcome"] == "won":
            stats[venue]["won"] += 1
    return [{"venue": k, **v} for k, v in stats.items()]


def pool_summary(client: HydraClient | None = None) -> list[dict]:
    """Summary of all pools."""
    pools = list_pools(client)
    return [get_pool_stats(p["name"], client) for p in pools]
