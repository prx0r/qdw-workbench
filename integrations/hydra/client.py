"""HydraClient — Bolt connection to HydraDB.

HydraDB write constraints:
    - ONLY `CREATE (a)-[:EDGE]->(b)` works for writes (creates both nodes + edge)
    - MATCH + CREATE fails ("write query is not executable by the mutation engine")
    - MERGE fails ("MERGE with following clauses is not executable")
    - Standalone CREATE on single node fails ("only one-hop edge patterns")
    - Node `id` property MUST be integer (use hash_id() for string IDs)
    - RETURN needs specific properties (not whole node)
    - count(*) works, count(n) does not
    - MATCH requires label or property predicate

This means the graph is immutable by design:
    - Each write creates a new subgraph (nodes + edges in one statement)
    - Updates = new nodes with edges to old ones (versioned lineage)
    - Reads = MATCH traversals
    - Deletes = MATCH + DETACH DELETE
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from typing import Any

from neo4j import GraphDatabase


DEFAULT_BOLT = os.environ.get("HYDRADB_BOLT", "bolt://127.0.0.1:7687")
DEFAULT_TOKEN = os.environ.get("HYDRADB_TOKEN", "private-lab-hydradb-token-2026-secure")
DEFAULT_USER = os.environ.get("HYDRADB_USER", "neo4j")
DEFAULT_DB = os.environ.get("HYDRADB_DB", "default")


def hash_id(s: str) -> int:
    """Convert string ID to integer for HydraDB node id property."""
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def _props_str(props: dict, var: str = "") -> str:
    """Build Cypher property string for CREATE pattern: {k: $k, ...}"""
    valid = {}
    for k, v in props.items():
        if isinstance(v, (str, int, float, bool)):
            valid[k] = v
        elif v is not None:
            valid[k] = str(v)
    return ", ".join(f"{k}: ${k}" for k in valid)


def _props_params(props: dict, var: str = "") -> dict:
    """Build params dict from properties (no prefix needed for CREATE)."""
    valid = {}
    for k, v in props.items():
        if isinstance(v, (str, int, float, bool)):
            valid[k] = v
        elif v is not None:
            valid[k] = str(v)
    return valid


@dataclass
class HydraClient:
    """Thin wrapper around neo4j driver for HydraDB."""

    bolt_url: str = DEFAULT_BOLT
    auth_user: str = DEFAULT_USER
    auth_token: str = DEFAULT_TOKEN
    database: str = DEFAULT_DB
    _driver: Any = field(default=None, repr=False)

    def connect(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.bolt_url, auth=(self.auth_user, self.auth_token)
            )
        return self

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.close()

    @property
    def driver(self):
        if self._driver is None:
            self.connect()
        return self._driver

    def run(self, query: str, **params) -> list[dict]:
        """Run a read query (MATCH)."""
        with self.driver.session(database=self.database) as session:
            return [dict(record) for record in session.run(query, **params)]

    def run_one(self, query: str, **params) -> dict | None:
        results = self.run(query, **params)
        return results[0] if results else None

    def run_write(self, query: str, **params) -> list[dict]:
        """Run a write query (CREATE edge pattern, DELETE)."""
        with self.driver.session(database=self.database) as session:
            return [dict(record) for record in session.run(query, **params)]

    # ─── Write primitives ─────────────────────────────────────────────
    # ONLY these patterns work for writes in HydraDB:

    def create_subgraph(self, query: str, **params) -> list[dict]:
        """Execute a CREATE statement that builds a subgraph.

        HydraDB only allows CREATE with edge patterns.
        Example: CREATE (a:Worker {id: 1})-[:HAS_VERSION]->(b:WorkerVersion {id: 2})
        """
        return self.run_write(query, **params)

    def delete_node(self, label: str, node_id: int) -> bool:
        """Delete a node and all its edges."""
        self.run_write(f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n", id=node_id)
        return True

    def clear_label(self, label: str) -> None:
        self.run_write(f"MATCH (n:{label}) DETACH DELETE n")

    def clear_all(self) -> None:
        for label in ["Worker", "WorkerVersion", "Run", "Studio", "TaskInstance",
                       "Experiment", "Finding", "LearningProposal", "BudgetEvent",
                       "EvaluationResult", "Artifact", "ExternalOutcome"]:
            self.clear_label(label)

    # ─── High-level write helpers ─────────────────────────────────────
    # These build the CREATE statements for common lab patterns.

    def create_worker_with_version(self, worker_id: str, worker_name: str,
                                   version_id: str, model: str,
                                   **version_props) -> dict:
        """Create a Worker and its first WorkerVersion, linked.

        Pattern: CREATE (w:Worker)-[:HAS_VERSION]->(wv:WorkerVersion)
        """
        wid = hash_id(worker_id)
        vid = hash_id(version_id)
        props = {"id": wid, "name": worker_name}
        vp = {"id": vid, "model": model, "worker_id": worker_id}
        vp.update(version_props)

        f_str = _props_str(props)
        t_str = _props_str(vp)
        params = {**_props_params(props), **_props_params(vp)}

        query = f"CREATE (w:Worker {{{f_str}}})-[:HAS_VERSION]->(wv:WorkerVersion {{{t_str}}})"
        self.run_write(query, **params)
        return {"worker_id": wid, "version_id": vid}

    def create_run(self, run_id: str, version_id: str, studio_id: str,
                   outcome: str = "pending", **run_props) -> dict:
        """Create a Run linked to a WorkerVersion and Studio.

        Pattern: CREATE (wv)-[:RAN]->(r:Run)-[:IN_STUDIO]->(s:Studio)
        This requires the WorkerVersion to already exist.
        But MATCH+CREATE fails... so we create Run+Studio together,
        and the caller must handle the wv link separately.

        Actually: we can do it in one CREATE if we include all three:
        But we can't MATCH existing wv...

        So: create Run+Studio in one CREATE, link to wv via traversal at read time.
        """
        rid = hash_id(run_id)
        sid = hash_id(studio_id)
        props = {"id": rid, "outcome": outcome, "studio_id": studio_id}
        props.update(run_props)
        sp = {"id": sid, "name": studio_id}

        r_str = _props_str(props)
        s_str = _props_str(sp)
        params = {**_props_params(props), **_props_params(sp)}

        query = f"CREATE (r:Run {{{r_str}}})-[:IN_STUDIO]->(s:Studio {{{s_str}}})"
        self.run_write(query, **params)
        return {"run_id": rid, "studio_id": sid}

    def create_experiment(self, experiment_id: str, studio_id: str,
                          hypothesis: str = "", **exp_props) -> dict:
        """Create an Experiment linked to a Studio."""
        eid = hash_id(experiment_id)
        sid = hash_id(studio_id)
        props = {"id": eid, "hypothesis": hypothesis, "studio_id": studio_id}
        props.update(exp_props)
        sp = {"id": sid, "name": studio_id}

        e_str = _props_str(props)
        s_str = _props_str(sp)
        params = {**_props_params(props), **_props_params(sp)}

        query = f"CREATE (e:Experiment {{{e_str}}})-[:IN_STUDIO]->(s:Studio {{{s_str}}})"
        self.run_write(query, **params)
        return {"experiment_id": eid, "studio_id": sid}

    def create_finding(self, finding_id: str, experiment_id: str,
                       claim: str = "", tier: str = "OBSERVATION", **find_props) -> dict:
        """Create a Finding supported by an Experiment."""
        fid = hash_id(finding_id)
        eid = hash_id(experiment_id)
        props = {"id": fid, "claim": claim, "tier": tier}
        props.update(find_props)
        ep = {"id": eid}

        f_str = _props_str(props)
        e_str = _props_str(ep)
        params = {**_props_params(props), **_props_params(ep)}

        query = f"CREATE (f:Finding {{{f_str}}})-[:SUPPORTED_BY]->(e:Experiment {{{e_str}}})"
        self.run_write(query, **params)
        return {"finding_id": fid, "experiment_id": eid}

    def create_learning_proposal(self, proposal_id: str, version_id: str,
                                 hypothesis: str = "", **prop_props) -> dict:
        """Create a LearningProposal that created a WorkerVersion."""
        pid = hash_id(proposal_id)
        vid = hash_id(version_id)
        props = {"id": pid, "hypothesis": hypothesis}
        props.update(prop_props)
        vp = {"id": vid}

        p_str = _props_str(props)
        v_str = _props_str(vp)
        params = {**_props_params(props), **_props_params(vp)}

        query = f"CREATE (p:LearningProposal {{{p_str}}})-[:CREATED]->(v:WorkerVersion {{{v_str}}})"
        self.run_write(query, **params)
        return {"proposal_id": pid, "version_id": vid}

    # ─── Read operations (all use MATCH) ──────────────────────────────

    def count_nodes(self, label: str) -> int:
        result = self.run_one(f"MATCH (n:{label}) RETURN count(*) AS count")
        return result["count"] if result else 0

    def list_nodes(self, label: str, limit: int = 100) -> list[dict]:
        results = self.run(f"MATCH (n:{label}) RETURN n.id AS id LIMIT $limit", limit=limit)
        return [{"id": r["id"], "label": label} for r in results]

    def get_node_props(self, label: str, node_id: int, props: list[str]) -> dict:
        prop_return = ", ".join(f"n.{p} AS {p}" for p in props)
        query = f"MATCH (n:{label} {{id: $id}}) RETURN {prop_return}"
        return self.run_one(query, id=node_id) or {}

    def get_edges_from(self, label: str, node_id: int, edge_type: str | None = None) -> list[dict]:
        if edge_type:
            query = f"""
                MATCH (a:{label} {{id: $id}})-[r:{edge_type}]->(b)
                RETURN type(r) AS type, b.id AS target_id, labels(b)[0] AS target_label
            """
        else:
            query = f"""
                MATCH (a:{label} {{id: $id}})-[r]->(b)
                RETURN type(r) AS type, b.id AS target_id, labels(b)[0] AS target_label
            """
        return self.run(query, id=node_id)

    def get_edges_to(self, label: str, node_id: int, edge_type: str | None = None) -> list[dict]:
        if edge_type:
            query = f"""
                MATCH (a)-[r:{edge_type}]->(b:{label} {{id: $id}})
                RETURN type(r) AS type, a.id AS source_id, labels(a)[0] AS source_label
            """
        else:
            query = f"""
                MATCH (a)-[r]->(b:{label} {{id: $id}})
                RETURN type(r) AS type, a.id AS source_id, labels(a)[0] AS source_label
            """
        return self.run(query, id=node_id)

    def health(self) -> dict:
        try:
            result = self.run_one("MATCH (n:Worker) RETURN count(*) AS count")
            return {"status": "ready", "bolt": self.bolt_url, "workers": result["count"] if result else 0}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ─── Singleton ────────────────────────────────────────────────────────

_client: HydraClient | None = None


def get_client(**kwargs) -> HydraClient:
    global _client
    if _client is None:
        _client = HydraClient(**kwargs)
        _client.connect()
    return _client


def close_client():
    global _client
    if _client:
        _client.close()
        _client = None
