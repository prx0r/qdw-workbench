"""Context compiler — assemble context packs from pool evidence.

The compiler builds a bounded context pack from:
- Pool doctrine (always included)
- Pool findings (relevant to task)
- Pool skills (promoted, relevant to task)
- Worker memory (Letta)
- Venue intel (module-specific)
- Budget info
"""
from __future__ import annotations
import json
from typing import Any
from lab.modules import PoolMatch, CapabilityDemand
from integrations.hydra import get_client, hash_id


# Token budgets by priority
TOKEN_BUDGETS = {
    "doctrine": 0.20,
    "findings": 0.25,
    "skills": 0.15,
    "venue_intel": 0.10,
    "worker_memory": 0.10,
    "task": 0.15,
    "budget": 0.05,
}


def compile_context(
    pool_matches: list[PoolMatch],
    demand: CapabilityDemand,
    task_content: dict | None = None,
    worker_memory: list[dict] | None = None,
    venue_intel: dict | None = None,
    total_tokens: int = 8000,
) -> dict:
    """Compile a context pack from pool evidence.

    Returns a dict with fragments, each with source, type, trust_tier, content, tokens.
    """
    fragments = []
    token_budgets = {k: int(v * total_tokens) for k, v in TOKEN_BUDGETS.items()}

    # 1. Pool doctrine (always included, highest trust)
    for match in pool_matches:
        doctrine = _get_pool_doctrine(match.pool_id, token_budgets["doctrine"] // len(pool_matches))
        if doctrine:
            fragments.append({
                "source": f"pool/{match.pool_id}/doctrine",
                "type": "doctrine",
                "trust_tier": "canonical",
                "content": doctrine,
                "tokens": len(doctrine.split()) * 4,  # rough estimate
                "pool": match.pool_id,
                "relevance": match.relevance,
            })

    # 2. Pool findings (relevant to demand)
    for match in pool_matches:
        findings = _get_pool_findings(match.pool_id, demand, token_budgets["findings"] // len(pool_matches))
        for f in findings:
            fragments.append({
                "source": f"pool/{match.pool_id}/finding/{f.get('id', '')}",
                "type": "finding",
                "trust_tier": "verified" if f.get("tier") in ("STUDIO_FINDING", "TRANSFER_CLAIM") else "observed",
                "content": f.get("claim", ""),
                "tokens": len(f.get("claim", "").split()) * 4,
                "pool": match.pool_id,
                "tier": f.get("tier", ""),
                "confidence": f.get("confidence", 0),
            })

    # 3. Pool skills
    for match in pool_matches:
        skills = _get_pool_skills(match.pool_id, demand, token_budgets["skills"] // len(pool_matches))
        for s in skills:
            fragments.append({
                "source": f"pool/{match.pool_id}/skill/{s.get('name', '')}",
                "type": "skill",
                "trust_tier": "canonical",
                "content": s.get("content", ""),
                "tokens": len(s.get("content", "").split()) * 4,
                "pool": match.pool_id,
            })

    # 4. Task content
    if task_content:
        task_text = json.dumps(task_content, indent=2)
        fragments.append({
            "source": "task",
            "type": "task",
            "trust_tier": "ephemeral",
            "content": task_text[:token_budgets["task"]],
            "tokens": len(task_text[:token_budgets["task"]].split()) * 4,
        })

    # 5. Worker memory
    if worker_memory:
        for mem in worker_memory[:5]:  # limit to 5 fragments
            fragments.append({
                "source": "worker_memory",
                "type": "memory",
                "trust_tier": "memory",
                "content": mem.get("content", ""),
                "tokens": len(mem.get("content", "").split()) * 4,
            })

    # 6. Venue intel
    if venue_intel:
        intel_text = json.dumps(venue_intel, indent=2)
        fragments.append({
            "source": "venue_intel",
            "type": "venue_intel",
            "trust_tier": "observed",
            "content": intel_text[:token_budgets["venue_intel"]],
            "tokens": len(intel_text[:token_budgets["venue_intel"]].split()) * 4,
        })

    # Sort by priority: doctrine > findings > skills > task > venue > memory
    trust_order = {"canonical": 0, "verified": 1, "observed": 2, "memory": 3, "ephemeral": 4}
    fragments.sort(key=lambda f: trust_order.get(f["trust_tier"], 5))

    total_used = sum(f["tokens"] for f in fragments)
    dropped = []
    if total_used > total_tokens:
        # Drop lowest priority fragments until under budget
        while fragments and total_used > total_tokens:
            dropped.append(fragments.pop())
            total_used = sum(f["tokens"] for f in fragments)

    return {
        "fragments": fragments,
        "dropped": dropped,
        "total_tokens": total_used,
        "budget_tokens": total_tokens,
        "pool_matches": [m.model_dump() for m in pool_matches],
    }


def _get_pool_doctrine(pool_id: str, max_tokens: int) -> str:
    """Get doctrine text from pool files."""
    doctrine_path = Path(__file__).parent.parent.parent / "pools" / pool_id / "doctrine"
    if not doctrine_path.exists():
        return ""
    texts = []
    for f in sorted(doctrine_path.glob("*.md")):
        texts.append(f.read_text())
    combined = "\n\n".join(texts)
    return combined[:max_tokens // 4]  # rough char limit


def _get_pool_findings(pool_id: str, demand: CapabilityDemand, max_items: int) -> list[dict]:
    """Get relevant findings from HydraDB for a pool."""
    try:
        client = get_client()
        # Get findings with their properties
        results = client.run(
            "MATCH (f:Finding)-[:APPLIES_TO]->(pool:CapabilityPool {name: $pool}) "
            "RETURN f.claim AS claim, f.tier AS tier, f.confidence AS confidence "
            "LIMIT $limit",
            pool=pool_id, limit=max_items
        )
        return results
    except Exception:
        return []


def _get_pool_skills(pool_id: str, demand: CapabilityDemand, max_items: int) -> list[dict]:
    """Get promoted skills from pool."""
    skill_path = Path(__file__).parent.parent.parent / "pools" / pool_id / "skills"
    if not skill_path.exists():
        return []
    skills = []
    for skill_dir in sorted(skill_path.iterdir()):
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skills.append({
                    "name": skill_dir.name,
                    "content": skill_file.read_text()[:2000],  # cap per skill
                })
                if len(skills) >= max_items:
                    break
    return skills
