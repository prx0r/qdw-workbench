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
    CREATE (pool:CapabilityPool)-[:HAS_VENUE]->(v:Venue)
    CREATE (w:Worker)-[:MEMBER_OF]->(pool:CapabilityPool)
    CREATE (r:Run)-[:CONTRIBUTES_TO]->(pool:CapabilityPool)
    CREATE (r:Run)-[:EXECUTED_AT]->(v:Venue)
    CREATE (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool)
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


# ─── Pool & Venue subgraphs ───────────────────────────────────────────

def create_pool(client: HydraClient | None = None, pool_id: str = "",
                name: str = "", subdomains: list[str] | None = None,
                **pool_props) -> dict:
    """Create a CapabilityPool node (via self-referencing edge)."""
    c = _client(client)
    pid = hash_id(pool_id)
    props = {"id": pid, "name": name}
    if subdomains:
        props["subdomains"] = str(subdomains)
    props.update(pool_props)

    p_str = ", ".join(f"{k}: ${k}" for k in props)
    query = f"CREATE (pool:CapabilityPool {{{p_str}}})-[:_SELF]->(pool2:CapabilityPool {{id: $id}})"
    c.run_write(query, **props)
    # Remove self-edge
    c.run_write(f"MATCH (pool:CapabilityPool {{id: $id}})-[r:_SELF]->() DELETE r", id=pid)
    return {"pool_id": pid, "name": name}


def create_venue(client: HydraClient | None = None, venue_id: str = "",
                 name: str = "", protocol: str = "", **venue_props) -> dict:
    """Create a Venue node (via self-referencing edge)."""
    c = _client(client)
    vid = hash_id(venue_id)
    props = {"id": vid, "name": name, "protocol": protocol}
    props.update(venue_props)

    v_str = ", ".join(f"{k}: ${k}" for k in props)
    query = f"CREATE (v:Venue {{{v_str}}})-[:_SELF]->(v2:Venue {{id: $id}})"
    c.run_write(query, **props)
    c.run_write(f"MATCH (v:Venue {{id: $id}})-[r:_SELF]->() DELETE r", id=vid)
    return {"venue_id": vid, "name": name}


def create_pool_venue(client: HydraClient | None = None,
                      pool_id: str = "", venue_id: str = "",
                      pool_name: str = "", venue_name: str = "",
                      protocol: str = "", **props) -> dict:
    """Create CapabilityPool + Venue linked subgraph."""
    c = _client(client)
    pid = hash_id(pool_id)
    vid = hash_id(venue_id)
    pp = {"id": pid, "name": pool_name}
    vp = {"id": vid, "name": venue_name, "protocol": protocol}

    p_str = ", ".join(f"{k}: ${k}" for k in pp)
    v_str = ", ".join(f"{k}: $v_{k}" for k in vp)
    params = {k: v for k, v in pp.items()}
    params.update({f"v_{k}": v for k, v in vp.items()})

    query = f"CREATE (pool:CapabilityPool {{{p_str}}})-[:HAS_VENUE]->(v:Venue {{{v_str}}})"
    c.run_write(query, **params)
    return {"pool_id": pid, "venue_id": vid}


def create_worker_in_pool(client: HydraClient | None = None,
                          worker_id: str = "", worker_name: str = "",
                          version_id: str = "", model: str = "",
                          pool_id: str = "", pool_name: str = "") -> dict:
    """Create Worker + WorkerVersion linked, then separately link to pool."""
    c = _client(client)
    wid = hash_id(worker_id)
    vid = hash_id(version_id)
    pid = hash_id(pool_id)

    # Step 1: Worker + WorkerVersion
    wp = {"id": wid, "name": worker_name}
    vp = {"id": vid, "model": model}
    w_str = ", ".join(f"{k}: ${k}" for k in wp)
    v_str = ", ".join(f"{k}: $v_{k}" for k in vp)
    params = {k: v for k, v in wp.items()}
    params.update({f"v_{k}": v for k, v in vp.items()})
    c.run_write(f"CREATE (w:Worker {{{w_str}}})-[:HAS_VERSION]->(wv:WorkerVersion {{{v_str}}})", **params)

    # Step 2: Worker + CapabilityPool (separate edge)
    pp = {"id": pid, "name": pool_name}
    w_str2 = ", ".join(f"{k}: ${k}" for k in wp)
    p_str = ", ".join(f"{k}: $p_{k}" for k in pp)
    params2 = {k: v for k, v in wp.items()}
    params2.update({f"p_{k}": v for k, v in pp.items()})
    c.run_write(f"CREATE (w:Worker {{{w_str2}}})-[:MEMBER_OF]->(pool:CapabilityPool {{{p_str}}})", **params2)

    return {"worker_id": wid, "version_id": vid, "pool_id": pid}


def create_run_at_venue(client: HydraClient | None = None,
                        run_id: str = "", outcome: str = "pending",
                        venue_id: str = "", venue_name: str = "",
                        pool_id: str = "", pool_name: str = "",
                        **run_props) -> dict:
    """Create Run + Venue, then separately link Run to pool."""
    c = _client(client)
    rid = hash_id(run_id)
    vid = hash_id(venue_id)
    pid = hash_id(pool_id)

    # Step 1: Run + Venue
    rp = {"id": rid, "outcome": outcome}
    rp.update(run_props)
    vp = {"id": vid, "name": venue_name}
    r_str = ", ".join(f"{k}: ${k}" for k in rp)
    v_str = ", ".join(f"{k}: $v_{k}" for k in vp)
    params = {k: v for k, v in rp.items()}
    params.update({f"v_{k}": v for k, v in vp.items()})
    c.run_write(f"CREATE (r:Run {{{r_str}}})-[:EXECUTED_AT]->(v:Venue {{{v_str}}})", **params)

    # Step 2: Run + CapabilityPool
    pp = {"id": pid, "name": pool_name}
    r_str2 = ", ".join(f"{k}: ${k}" for k in rp)
    p_str = ", ".join(f"{k}: $p_{k}" for k in pp)
    params2 = {k: v for k, v in rp.items()}
    params2.update({f"p_{k}": v for k, v in pp.items()})
    c.run_write(f"CREATE (r:Run {{{r_str2}}})-[:CONTRIBUTES_TO]->(pool:CapabilityPool {{{p_str}}})", **params2)

    return {"run_id": rid, "venue_id": vid, "pool_id": pid}


def create_finding_in_pool(client: HydraClient | None = None,
                           finding_id: str = "", claim: str = "",
                           tier: str = "OBSERVATION",
                           pool_id: str = "", pool_name: str = "",
                           domains: list[str] | None = None,
                           subdomains: list[str] | None = None,
                           capabilities: list[str] | None = None,
                           **find_props) -> dict:
    """Create Finding + CapabilityPool linked subgraph."""
    c = _client(client)
    fid = hash_id(finding_id)
    pid = hash_id(pool_id)
    fp = {"id": fid, "claim": claim, "tier": tier}
    if domains:
        fp["domains"] = str(domains)
    if subdomains:
        fp["subdomains"] = str(subdomains)
    if capabilities:
        fp["capabilities"] = str(capabilities)
    fp.update(find_props)
    pp = {"id": pid, "name": pool_name}

    f_str = ", ".join(f"{k}: ${k}" for k in fp)
    p_str = ", ".join(f"{k}: $p_{k}" for k in pp)
    params = {k: v for k, v in fp.items()}
    params.update({f"p_{k}": v for k, v in pp.items()})

    query = f"CREATE (f:Finding {{{f_str}}})-[:APPLIES_TO]->(pool:CapabilityPool {{{p_str}}})"
    c.run_write(query, **params)
    return {"finding_id": fid, "pool_id": pid}


# ─── World Genome subgraphs ──────────────────────────────────────────

def create_world_genome(client: HydraClient | None = None,
                        genome_id: str = "", family_id: str = "",
                        difficulty: int = 1, seed: int = 0,
                        structure: str = "", information: str = "",
                        resources: str = "", **props) -> dict:
    """Create a WorldGenome node (via self-referencing edge)."""
    c = _client(client)
    gid = hash_id(genome_id)
    p = {"id": gid, "genome_id": genome_id, "family_id": family_id,
         "difficulty": difficulty, "seed": seed}
    if structure:
        p["structure"] = structure
    if information:
        p["information"] = information
    if resources:
        p["resources"] = resources
    p.update(props)

    g_str = ", ".join(f"{k}: ${k}" for k in p)
    query = f"CREATE (g:WorldGenome {{{g_str}}})-[:_SELF]->(g2:WorldGenome {{id: $id}})"
    c.run_write(query, **p)
    c.run_write("MATCH (g:WorldGenome {id: $id})-[r:_SELF]->() DELETE r", id=gid)
    return {"genome_id": gid}


def create_run_with_world(client: HydraClient | None = None,
                          run_id: str = "", genome_id: str = "",
                          outcome: str = "pending", **run_props) -> dict:
    """Create Run + WorldGenome linked subgraph."""
    c = _client(client)
    rid = hash_id(run_id)
    gid = hash_id(genome_id)

    rp = {"id": rid, "outcome": outcome}
    rp.update(run_props)
    gp = {"id": gid, "genome_id": genome_id}

    r_str = ", ".join(f"{k}: ${k}" for k in rp)
    g_str = ", ".join(f"{k}: $g_{k}" for k in gp)
    params = {k: v for k, v in rp.items()}
    params.update({f"g_{k}": v for k, v in gp.items()})

    query = f"CREATE (r:Run {{{r_str}}})-[:EXECUTED_IN]->(g:WorldGenome {{{g_str}}})"
    c.run_write(query, **params)
    return {"run_id": rid, "genome_id": gid}


# ─── Capability subgraphs ────────────────────────────────────────────

def create_capability(client: HydraClient | None = None,
                      capability_id: str = "", capability: str = "",
                      worker_id: str = "", family_id: str = "",
                      score: float = 0.0, n_samples: int = 1,
                      **props) -> dict:
    """Create a Capability node (via self-referencing edge)."""
    c = _client(client)
    cid = hash_id(capability_id)
    p = {"id": cid, "capability_id": capability_id, "capability": capability,
         "worker_id": worker_id, "family_id": family_id,
         "score": score, "n_samples": n_samples}
    p.update(props)

    cap_str = ", ".join(f"{k}: ${k}" for k in p)
    query = f"CREATE (cap:Capability {{{cap_str}}})-[:_SELF]->(cap2:Capability {{id: $id}})"
    c.run_write(query, **p)
    c.run_write("MATCH (cap:Capability {id: $id})-[r:_SELF]->() DELETE r", id=cid)
    return {"capability_id": cid}


# ─── FailureMode subgraphs ──────────────────────────────────────────

def create_failure_mode(client: HydraClient | None = None,
                        failure_id: str = "", family_id: str = "",
                        failure_mode: str = "", severity: float = 0.0,
                        worker_id: str = "", **props) -> dict:
    """Create a FailureMode node (via self-referencing edge)."""
    c = _client(client)
    fid = hash_id(failure_id)
    p = {"id": fid, "failure_id": failure_id, "family_id": family_id,
         "failure_mode": failure_mode, "severity": severity, "worker_id": worker_id}
    p.update(props)

    fm_str = ", ".join(f"{k}: ${k}" for k in p)
    query = f"CREATE (fm:FailureMode {{{fm_str}}})-[:_SELF]->(fm2:FailureMode {{id: $id}})"
    c.run_write(query, **p)
    c.run_write("MATCH (fm:FailureMode {id: $id})-[r:_SELF]->() DELETE r", id=fid)
    return {"failure_id": fid}


# ─── Insight subgraphs ──────────────────────────────────────────────

def create_insight(client: HydraClient | None = None,
                   insight_id: str = "", title: str = "",
                   body: str = "", kind: str = "",
                   experiment_id: str = "", evidence_runs: int = 0,
                   confidence: float = 0.0, **props) -> dict:
    """Create an Insight node (via self-referencing edge)."""
    c = _client(client)
    iid = hash_id(insight_id)
    p = {"id": iid, "insight_id": insight_id, "title": title, "body": body,
         "kind": kind, "evidence_runs": evidence_runs, "confidence": confidence}
    if experiment_id:
        p["experiment_id"] = experiment_id
    p.update(props)

    i_str = ", ".join(f"{k}: ${k}" for k in p)
    query = f"CREATE (i:Insight {{{i_str}}})-[:_SELF]->(i2:Insight {{id: $id}})"
    c.run_write(query, **p)
    c.run_write("MATCH (i:Insight {id: $id})-[r:_SELF]->() DELETE r", id=iid)
    return {"insight_id": iid}
