"""Thin HTTP projection over canonical QDW state.

The bridge owns no authoritative database and performs no independent verification.
"""
from __future__ import annotations
import json, os
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_system=None

def system():
    global _system
    if _system is None:
        from qdw.system import QDWSystem
        _system=QDWSystem(os.environ.get("QDW_DB","data/qdw.db"))
    return _system

@asynccontextmanager
async def lifespan(_:FastAPI):
    system(); yield

app=FastAPI(title="QDW Workbench Bridge",version="0.1.0",lifespan=lifespan)

@app.get("/health")
def health():
    d=system().doctor(); return {"status":"ok" if d.get("ok") else "degraded","doctor":d}

@app.get("/v1/factories")
def factories(): return system().factories.list()

@app.get("/v1/products")
def products():
    s=system()
    with s.db.connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM products ORDER BY updated_at DESC, created_at DESC").fetchall()]

@app.get("/v1/products/{product_id}")
def product(product_id:str):
    try:return system().products.passport(product_id)
    except KeyError:raise HTTPException(404,"product not found")

@app.get("/v1/human/pending")
def pending(): return system().human.pending()

class Decision(BaseModel):
    actor_id:str
    decision:dict[str,Any]|None=None

@app.post("/v1/human/{action_id}/approve")
def approve(action_id:str,b:Decision):
    try: system().human.approve(action_id,b.actor_id,b.decision or {})
    except (KeyError,ValueError) as e: raise HTTPException(409,str(e))
    return {"action_id":action_id,"status":"APPROVED"}

@app.post("/v1/human/{action_id}/decline")
def decline(action_id:str,b:Decision):
    try: system().human.decline(action_id,b.actor_id,b.decision or {})
    except (KeyError,ValueError) as e: raise HTTPException(409,str(e))
    return {"action_id":action_id,"status":"DECLINED"}

@app.get("/v1/federation/health")
def federation_health():
    return system().federation.health()

@app.get("/v1/workgraphs")
def workgraphs(limit:int=100):
    s=system(); limit=max(1,min(500,limit))
    with s.db.connect() as con:
        rows=con.execute("SELECT * FROM work_graphs ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) for r in rows]

@app.get("/v1/workgraphs/{graph_id}")
def workgraph(graph_id:str):
    s=system()
    with s.db.connect() as con:
        g=con.execute("SELECT * FROM work_graphs WHERE graph_id=?",(graph_id,)).fetchone()
        if not g: raise HTTPException(404,"graph not found")
        ns=con.execute("SELECT * FROM work_nodes WHERE graph_id=? ORDER BY priority DESC",(graph_id,)).fetchall()
        return {"graph":dict(g),"nodes":[dict(n) for n in ns]}

@app.get("/v1/recent-ledger")
def recent_ledger(limit:int=100):
    s=system(); limit=max(1,min(500,limit))
    with s.db.connect() as con:
        # Table name may evolve; fail loudly rather than fabricate an empty history.
        try: rows=con.execute("SELECT * FROM ledger_events ORDER BY rowid DESC LIMIT ?",(limit,)).fetchall()
        except Exception as e: raise HTTPException(501,f"current QDW ledger projection unavailable: {e}")
        return [dict(r) for r in rows]

# --- Memory bridge endpoints ---

@app.get("/v1/memory/recent")
def memory_recent(kind:str|None=None, limit:int=20):
    from .memory_bridge import get_recent_memory
    return get_recent_memory(kind=kind, limit=limit)

@app.get("/v1/memory/search")
def memory_search(q:str, limit:int=10):
    from .memory_bridge import search_memory
    return search_memory(query=q, limit=limit)

@app.post("/v1/memory/store")
def memory_store(body:dict[str,Any]):
    from .memory_bridge import store_event
    entry_id = store_event(
        kind=body.get("kind","manual"),
        source=body.get("source","bridge"),
        content=body.get("content",""),
        metadata=body.get("metadata"),
    )
    return {"id":entry_id,"stored":True}

# --- LCM context provider endpoint ---

@app.post("/v1/context/lcm")
def lcm_context(body:dict[str,Any]):
    from .lcm_provider import compile_lcm_context
    return compile_lcm_context(
        assertions=body.get("assertions",[]),
        max_tokens=body.get("max_tokens",8000),
        reserve_tokens=body.get("reserve_tokens",2000),
    )
