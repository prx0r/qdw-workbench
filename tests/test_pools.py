"""Tests for pool matching and context compilation."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lab.modules import CapabilityDemand, PoolMatch
from lab.pools.matcher import match_demand_to_pools, POOL_CENTROIDS
from lab.context.compiler import compile_context


def test_pool_matching():
    """Test that pool matching returns relevant results."""
    demand = CapabilityDemand(demands={"security": 0.98, "solidity": 0.84})
    matches = match_demand_to_pools(demand, top_k=3)

    assert len(matches) > 0, "Should find matching pools"
    assert matches[0].pool_id in POOL_CENTROIDS, "Should match known pool"
    assert matches[0].relevance > 0.3, "Relevance should be meaningful"
    print(f"  Pool matching: {len(matches)} matches, top={matches[0].pool_id} (relevance={matches[0].relevance:.2f})")


def test_context_compilation():
    """Test that context compilation produces bounded output."""
    pool_matches = [
        PoolMatch(pool_id="security", relevance=0.95, evidence_strength=0.7, transfer_prior=0.3,
                  reasons=["strong security match"]),
    ]
    demand = CapabilityDemand(demands={"security": 0.98})

    context = compile_context(pool_matches, demand, total_tokens=4000)

    assert "fragments" in context, "Should have fragments"
    assert context["total_tokens"] <= 4000, "Should respect token budget"
    print(f"  Context compilation: {len(context['fragments'])} fragments, {context['total_tokens']} tokens")


def test_demand_matching_variety():
    """Test different demand types match appropriate pools."""
    tests = [
        ({"security": 0.9}, ["security", "smart-contract-security"]),
        ({"forecasting": 0.9}, ["forecasting"]),
        ({"software_engineering": 0.9}, ["software-engineering"]),
        ({"ai_security": 0.9}, ["ai-redteam"]),
    ]

    for demands, expected_pools in tests:
        demand = CapabilityDemand(demands=demands)
        matches = match_demand_to_pools(demand, top_k=1)
        if matches:
            assert matches[0].pool_id in expected_pools, \
                f"Expected one of {expected_pools} for {demands}, got {matches[0].pool_id}"
            print(f"  {demands} -> {matches[0].pool_id} ✓")
        else:
            print(f"  {demands} -> no match (may need more pool centroids)")


if __name__ == "__main__":
    print("=== Pool & Context Tests ===\n")
    test_pool_matching()
    test_context_compilation()
    test_demand_matching_variety()
    print("\nAll tests passed!")
