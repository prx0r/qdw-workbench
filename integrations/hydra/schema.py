"""HydraDB schema — maps Pydantic contracts to graph CREATE statements.

HydraDB write constraints:
    - Only CREATE with edge patterns works
    - Node id must be integer (use hash_id())
    - MATCH is read-only
    - Each write creates a subgraph (nodes + edges)

Graph structure (each CREATE is a subgraph):
    CREATE (w:Worker)-[:HAS_VERSION]->(wv:WorkerVersion)
    CREATE (r:Run)-[:IN_STUDIO]->(s:Studio)
    CREATE (e:Experiment)-[:IN_STUDIO]->(s:Studio)
    CREATE (f:Finding)-[:SUPPORTED_BY]->(e:Experiment)
    CREATE (p:LearningProposal)-[:CREATED]->(wv:WorkerVersion)
"""
from __future__ import annotations

from integrations.hydra.client import HydraClient, get_client, hash_id


def _client(c: HydraClient | None = None) -> HydraClient:
    return c or get_client()


# ─── Subgraph creators ────────────────────────────────────────────────
# Each creates a self-contained subgraph in one CREATE statement.

def create_worker(client: HydraClient | None = None, worker_id: str = "",
                  name: str = "", version_id: str = "", model: str = "",
                  **version_props) -> dict:
    """Create Worker + WorkerVersion linked subgraph."""
    c = _client(client)
    wid = hash_id(worker_id)
    vid = hash_id(version_id) if version_id else 0

    w_props = {"id": wid, "name": name or worker_id}
    v_props = {"id": vid, "model": model}
    v_props.update(version_props)

    w_str = ", ".join(f"{k}: ${k}" for k in w_props)
    v_str = ", ".join(f"{k}: $v_{k}" for k in v_props)
    params = {**{k: v for k, v in w_props.items()}}
    params.update({f"v_{k}": v for k, v in v_props.items() if k != "id"})
    params["v_id"] = vid

    query = f"CREATE (w:Worker {{{w_str}}})-[:HAS_VERSION]->(wv:WorkerVersion {{{v_str}}})"
    c.run_write(query, **params)
    return {"worker_id": wid, "version_id": vid}


def create_run(client: HydraClient | None = None, run_id: str = "",
               studio_id: str = "", outcome: str = "pending",
               task_family: str = "", **run_props) -> dict:
    """Create Run + Studio linked subgraph."""
    c = _client(client)
    rid = hash_id(run_id)
    sid = hash_id(studio_id)

    r_props = {"id": rid, "outcome": outcome, "task_family": task_family}
    r_props.update(run_props)
    s_props = {"id": sid, "name": studio_id}

    r_str = ", ".join(f"{k}: ${k}" for k in r_props)
    s_str = ", ".join(f"{k}: $s_{k}" for k in s_props if k != "id")
    params = {k: v for k, v in r_props.items()}
    params["s_id"] = sid
    params.update({f"s_{k}": v for k, v in s_props.items() if k != "id"})

    query = f"CREATE (r:Run {{{r_str}}})-[:IN_STUDIO]->(s:Studio {{{s_str.replace(', s_id: $s_id', '') if s_str else 'id: $s_id'}}})"
    # Simpler approach
    s_param_str = ", ".join(f"{k}: $s_{k}" for k in s_props)
    params = {k: v for k, v in r_props.items()}
    params.update({f"s_{k}": v for k, v in s_props.items()})

    query = f"CREATE (r:Run {{{r_str}}})-[:IN_STUDIO]->(s:Studio {{{s_param_str}}})"
    c.run_write(query, **params)
    return {"run_id": rid, "studio_id": sid}


def create_experiment(client: HydraClient | None = None, experiment_id: str = "",
                      studio_id: str = "", hypothesis: str = "",
                      status: str = "DESIGNED", **exp_props) -> dict:
    """Create Experiment + Studio linked subgraph."""
    c = _client(client)
    eid = hash_id(experiment_id)
    sid = hash_id(studio_id)

    e_props = {"id": eid, "hypothesis": hypothesis, "status": status}
    e_props.update(exp_props)
    s_props = {"id": sid, "name": studio_id}

    e_str = ", ".join(f"{k}: ${k}" for k in e_props)
    s_str = ", ".join(f"{k}: $s_{k}" for k in s_props)
    params = {k: v for k, v in e_props.items()}
    params.update({f"s_{k}": v for k, v in s_props.items()})

    query = f"CREATE (e:Experiment {{{e_str}}})-[:IN_STUDIO]->(s:Studio {{{s_str}}})"
    c.run_write(query, **params)
    return {"experiment_id": eid, "studio_id": sid}


def create_finding(client: HydraClient | None = None, finding_id: str = "",
                   experiment_id: str = "", claim: str = "",
                   tier: str = "OBSERVATION", **find_props) -> dict:
    """Create Finding + Experiment linked subgraph."""
    c = _client(client)
    fid = hash_id(finding_id)
    eid = hash_id(experiment_id)

    f_props = {"id": fid, "claim": claim, "tier": tier}
    f_props.update(find_props)
    e_props = {"id": eid}

    f_str = ", ".join(f"{k}: ${k}" for k in f_props)
    e_str = ", ".join(f"{k}: $e_{k}" for k in e_props)
    params = {k: v for k, v in f_props.items()}
    params.update({f"e_{k}": v for k, v in e_props.items()})

    query = f"CREATE (f:Finding {{{f_str}}})-[:SUPPORTED_BY]->(e:Experiment {{{e_str}}})"
    c.run_write(query, **params)
    return {"finding_id": fid, "experiment_id": eid}


def create_learning_proposal(client: HydraClient | None = None, proposal_id: str = "",
                             version_id: str = "", hypothesis: str = "",
                             **prop_props) -> dict:
    """Create LearningProposal + WorkerVersion linked subgraph."""
    c = _client(client)
    pid = hash_id(proposal_id)
    vid = hash_id(version_id)

    p_props = {"id": pid, "hypothesis": hypothesis}
    p_props.update(prop_props)
    v_props = {"id": vid}

    p_str = ", ".join(f"{k}: ${k}" for k in p_props)
    v_str = ", ".join(f"{k}: $v_{k}" for k in v_props)
    params = {k: v for k, v in p_props.items()}
    params.update({f"v_{k}": v for k, v in v_props.items()})

    query = f"CREATE (p:LearningProposal {{{p_str}}})-[:CREATED]->(v:WorkerVersion {{{v_str}}})"
    c.run_write(query, **params)
    return {"proposal_id": pid, "version_id": vid}
