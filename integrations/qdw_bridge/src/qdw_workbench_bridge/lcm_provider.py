"""QDW Context Provider — bridges hermes-lcm assertions into ContextFragments.

When hermes-lcm has accumulated assertions from a conversation, this module
converts them into QDW ContextFragments that can be fed into compile_context().
"""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from typing import Any

try:
    from qdw_workbench_bridge.app import system
except ImportError:
    system = None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def lcm_assertions_to_fragments(
    assertions: list[dict[str, Any]],
    provider_id: str = "hermes-lcm",
) -> list[dict[str, Any]]:
    """Convert LCM assertion dicts into QDW ContextFragment dicts."""
    fragments = []
    for i, assertion in enumerate(assertions):
        content = assertion.get("content", assertion.get("text", ""))
        if not content:
            continue
        trust = assertion.get("trust", "observed")
        if trust not in ("canonical", "verified", "observed", "memory", "ephemeral"):
            trust = "observed"
        fragments.append({
            "provider_id": provider_id,
            "source_uri": assertion.get("source", f"lcm:assertion:{i}"),
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "sha256": _sha256(content),
            "token_estimate": len(content.split()) * 4 // 3,  # rough token estimate
            "priority": assertion.get("priority", 50),
            "trust": trust,
            "title": assertion.get("title", f"LCM assertion {i}"),
            "content": content,
        })
    return fragments


def compile_lcm_context(
    assertions: list[dict[str, Any]],
    max_tokens: int = 8000,
    reserve_tokens: int = 2000,
) -> dict[str, Any]:
    """Compile LCM assertions into a QDW context pack."""
    fragments = lcm_assertions_to_fragments(assertions)
    policy = {
        "version": "qdw-lcm-v1",
        "max_tokens": max_tokens,
        "reserve_tokens": reserve_tokens,
    }
    # Use the contracts crate's compile_context logic
    # For now, return the raw fragments + policy (the node will compile)
    return {
        "fragments": fragments,
        "policy": policy,
        "fragment_count": len(fragments),
        "total_tokens": sum(f.get("token_estimate", 0) for f in fragments),
    }
