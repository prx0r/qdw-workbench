"""Module contract — standardized interface between modules and Private Lab.

Modules own their ecosystems. Private Lab receives standardized status.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal


class ModuleAction(BaseModel):
    """An action a module can take."""
    action_id: str
    action_type: Literal["train", "submit", "hold", "explore_new_worker", "register", "exit"]
    program_id: str
    worker_version: str = ""
    estimated_cost_usd: float = 0.0
    estimated_reward: float = 0.0
    confidence: float = 0.0
    metadata: dict = Field(default_factory=dict)


class ModulePerformance(BaseModel):
    """Module's performance on a program."""
    score: float = 0.0
    rank: int = 0
    delta: float = 0.0
    runs: int = 0
    wins: int = 0
    cost_usd: float = 0.0
    revenue_usd: float = 0.0


class ModuleProgram(BaseModel):
    """A program within a module (e.g., Bitsec SN60)."""
    program_id: str
    name: str
    state: Literal["DISCOVERED", "REPRODUCING", "LOCAL_BASELINE", "TRAINING",
                     "SHADOW", "LIVE_COMPETE", "DEFENDING", "EXITING", "PAUSED"]
    capability_demand: dict[str, float] = Field(default_factory=dict)
    our_performance: ModulePerformance = Field(default_factory=ModulePerformance)
    possible_actions: list[str] = Field(default_factory=list)
    estimated_costs: dict[str, float] = Field(default_factory=dict)
    estimated_rewards: dict[str, float] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class ModuleStatus(BaseModel):
    """Standardized module status report to Private Lab."""
    module_id: str
    module_name: str
    programs: list[ModuleProgram] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_revenue_usd: float = 0.0
    worker_versions: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class CapabilityDemand(BaseModel):
    """What capabilities an opportunity or program requires."""
    demands: dict[str, float] = Field(default_factory=dict)


class PoolMatch(BaseModel):
    """Result of matching a demand to pools."""
    pool_id: str
    relevance: float
    evidence_strength: float
    transfer_prior: float
    reasons: list[str] = Field(default_factory=list)


class OpportunityMatch(BaseModel):
    """Result of matching an opportunity to pools and workers."""
    opportunity_id: str
    capability_demand: CapabilityDemand
    pool_matches: list[PoolMatch] = Field(default_factory=list)
    nearest_runs: list[str] = Field(default_factory=list)
    candidate_workers: list[str] = Field(default_factory=list)
    estimated_success: float = 0.0
    estimated_cost_usd: float = 0.0
    estimated_reward: float = 0.0
    learning_value: float = 0.0
    source: str = ""


class AllocationDecision(BaseModel):
    """Lab's decision on how to allocate resources."""
    decision_id: str
    opportunity_id: str
    module_id: str = ""
    worker_id: str = ""
    budget_envelope_id: str = ""
    selected_pools: list[PoolMatch] = Field(default_factory=list)
    action: str = ""
    reason: str = ""
    cost_usd: float = 0.0
    expected_reward: float = 0.0
    expected_learning: float = 0.0
